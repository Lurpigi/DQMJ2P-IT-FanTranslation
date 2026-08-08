#!/usr/bin/env python3
"""Import official Italian text into untouched Professional scripts.

The normal game stores Italian as the ``__3`` script variant.  Professional
scripts can contain extra dialogue, so only files with matching SAY/SETNAME
counts are eligible.  Files already modified in the working tree are skipped
to preserve hand-reviewed translation work.
"""

from __future__ import annotations

import re
import subprocess
import argparse
from pathlib import Path

from common import DTE_TABLE


TOKEN_RE = re.compile(r"\{[^}]+\}")
STRUCT_RE = re.compile(r"\{(?:WAIT|CLEAR|BREAK)\}")
PREFIX_RE = re.compile(r"\{(?:VOICE=\d+|COLOR=\d+)\}")
SEMANTIC_RE = re.compile(r"\{(?:NAME|E[0-9A-Fa-f]{3})\}")
SAY_RE = re.compile(r'^(SAY\s+")(.+)("\s*)$')
SETNAME_RE = re.compile(r'^(SETNAME\s+")(.+)("\s*)$')


def body(line: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.match(line)
    return match.group(2) if match else None


def clean_name(value: str) -> str:
    value = value.split("{END}", 1)[0]
    return re.sub(
        r"\{(1F[0-9A-Fa-f]{2})\}",
        lambda match: DTE_TABLE.get(match.group(1).upper(), match.group(0)),
        value,
    )


def clean_official_say(value: str) -> str:
    """Keep visible official text and DTE glyphs, drop language controls."""
    value = value.split("{END}", 1)[0]
    value = value.replace("{PAGE}", " ")
    value = re.sub(r"\{(?:VOICE=\d+|COLOR=\d+|WAIT|CLEAR|BREAK|NAME|E[0-9A-Fa-f]{3})\}", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def map_semantic_tokens(text: str, target_body: str) -> str:
    """Use Professional placeholder codes while keeping official placement."""
    target_tokens = SEMANTIC_RE.findall(target_body)
    name_tokens = [token for token in target_tokens if token == "{NAME}"]
    # E321 is a formatting/name prefix in the normal localization, not the
    # object/number placeholder that follows NAME.  Do not let it consume a
    # Professional E-token such as E328.
    e321_tokens = [token for token in target_tokens if token == "{E321}"]
    e_tokens = [token for token in target_tokens if token not in ("{NAME}", "{E321}")]
    name_index = 0
    e321_index = 0
    e_index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal name_index, e321_index, e_index
        token = match.group(0)
        if token == "{E321}":
            if e321_index < len(e321_tokens):
                result = e321_tokens[e321_index]
                e321_index += 1
                return result
            return ""
        if token == "{NAME}":
            if name_index < len(name_tokens):
                result = name_tokens[name_index]
                name_index += 1
                return result
            return token
        if e_index < len(e_tokens):
            result = e_tokens[e_index]
            e_index += 1
            return result
        # Normal Italian sometimes adds {E321} before {NAME}; it is not
        # present in the Professional skeleton in those cases.
        return ""

    return SEMANTIC_RE.sub(replace, text)


def text_chunks(value: str) -> tuple[list[str], list[str]]:
    tokens = TOKEN_RE.findall(value)
    chunks = TOKEN_RE.split(value)
    return chunks, tokens


def boundary(text: str, desired: int) -> int:
    if desired <= 0 or desired >= len(text):
        return max(0, min(len(text), desired))
    candidates = [index + 1 for index, char in enumerate(text) if char.isspace()]
    if not candidates:
        return desired
    return min(candidates, key=lambda value: abs(value - desired))


def preserve_edge_spaces(new: str, target: str) -> str:
    if target[:1].isspace() and not new[:1].isspace():
        new = " " + new
    if target[-1:].isspace() and not new[-1:].isspace():
        new += " "
    return new


def distribute(official: str, target_chunks: list[str]) -> list[str]:
    """Distribute official prose over the target's existing tag skeleton."""
    if len(target_chunks) == 1:
        return [official]
    weights = [len(chunk) for chunk in target_chunks]
    total = sum(weights)
    if total == 0:
        result = [""] * len(target_chunks)
        result[0] = official
        return result
    result: list[str] = []
    start = 0
    cumulative = 0
    for index, weight in enumerate(weights[:-1]):
        cumulative += weight
        desired = round(len(official) * cumulative / total)
        cut = boundary(official, desired)
        result.append(preserve_edge_spaces(official[start:cut], target_chunks[len(result)]))
        start = cut
    result.append(preserve_edge_spaces(official[start:], target_chunks[-1]))
    return result


def transplant_say(target_line: str, official_line: str) -> str:
    target_body = body(target_line, SAY_RE)
    official_body = body(official_line, SAY_RE)
    if target_body is None or official_body is None:
        return target_line
    prefix: list[str] = []
    remainder = target_body
    while (match := PREFIX_RE.match(remainder)):
        prefix.append(match.group(0))
        remainder = remainder[match.end():]
    target_parts = STRUCT_RE.split(remainder)
    target_controls = STRUCT_RE.findall(remainder)
    target_weights = [len(SEMANTIC_RE.sub("", part)) for part in target_parts]

    official_body = official_body.split("{END}", 1)[0]
    official_body = official_body.replace("{PAGE}", " ")
    official_body = PREFIX_RE.sub("", official_body)
    official_parts = STRUCT_RE.split(official_body)
    official_controls = STRUCT_RE.findall(official_body)
    official_parts = [re.sub(r"\s+", " ", part).strip() for part in official_parts]
    official_parts = [map_semantic_tokens(part, target_body) for part in official_parts]

    if official_controls == target_controls and len(official_parts) == len(target_parts):
        new_parts = official_parts
    else:
        official_text = " ".join(part for part in official_parts if part).strip()
        weighted_targets = ["x" * weight for weight in target_weights]
        new_parts = distribute(official_text, weighted_targets)

    rebuilt = "".join(prefix) + new_parts[0]
    for token, part in zip(target_controls, new_parts[1:]):
        rebuilt += token + part
    return f'SAY "{rebuilt}"'


def modified_paths() -> set[str]:
    result = subprocess.run(
        ["git", "-c", "core.autocrlf=true", "diff", "--name-only", "--", "Translation/SCRIPTS/*.txt"],
        check=True,
        capture_output=True,
        text=True,
    )
    # Git's pathspec is intentionally broad; filter to supported script families below.
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--redo", nargs="*", default=[], help="redo these files from their HEAD skeleton")
    parser.add_argument("--force", nargs="*", default=[], help="allow rewriting these already modified files")
    parser.add_argument("--say-only", nargs="*", default=[], help="import SAY lines even when SETNAME counts differ")
    args = parser.parse_args()
    target_dir = Path("Translation/SCRIPTS")
    official_dir = Path("game/tmp/normal_scripts")
    changed = modified_paths()
    imported: list[str] = []
    skipped_changed: list[str] = []
    skipped_mismatch: list[str] = []
    skipped_missing: list[str] = []

    for target in sorted(target_dir.glob("*__0.txt")):
        match = re.fullmatch(r"([dksw])[A-Za-z0-9]+__0\.txt", target.name, re.IGNORECASE)
        if not match:
            continue
        official = official_dir / target.name.replace("__0", "__3")
        relative = target.as_posix()
        redo = target.name in args.redo
        force = target.name in args.force
        say_only = target.name in args.say_only
        if relative in changed and not redo and not force:
            skipped_changed.append(target.name)
            continue
        if not official.exists():
            skipped_missing.append(target.name)
            continue

        if redo:
            current_lines = subprocess.run(
                ["git", "-c", "core.autocrlf=true", "show", f"HEAD:{relative}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        else:
            current_lines = target.read_text(encoding="utf-8").splitlines()
        official_lines = official.read_text(encoding="utf-8").splitlines()
        current_say = [line for line in current_lines if line.startswith("SAY ")]
        official_say = [line for line in official_lines if line.startswith("SAY ")]
        current_names = [line for line in current_lines if line.startswith("SETNAME ")]
        official_names = [line for line in official_lines if line.startswith("SETNAME ")]
        if len(current_say) != len(official_say) or (not say_only and len(current_names) != len(official_names)):
            skipped_mismatch.append(target.name)
            continue

        say_index = 0
        name_index = 0
        output: list[str] = []
        for line in current_lines:
            if line.startswith("SAY "):
                output.append(transplant_say(line, official_say[say_index]))
                say_index += 1
            elif line.startswith("SETNAME "):
                if say_only:
                    output.append(line)
                else:
                    official_name = clean_name(body(official_names[name_index], SETNAME_RE) or "")
                    output.append(f'SETNAME "{official_name}"')
                name_index += 1
            else:
                output.append(line)
        target.write_text("\n".join(output) + "\n", encoding="utf-8")
        imported.append(target.name)

    print(f"IMPORTED={len(imported)}")
    print("FILES=" + " ".join(imported))
    print(f"SKIPPED_CHANGED={len(skipped_changed)}")
    print(f"SKIPPED_MISMATCH={len(skipped_mismatch)} " + " ".join(skipped_mismatch))
    print(f"SKIPPED_MISSING={len(skipped_missing)}")


if __name__ == "__main__":
    main()
