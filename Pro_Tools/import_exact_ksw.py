from __future__ import annotations

import argparse
import re
from collections import defaultdict, deque
from pathlib import Path

from import_official_story import clean_name, transplant_say


ROOT = Path("Translation/SCRIPTS")
NORMAL = Path("game/tmp/normal_scripts")
TOKEN_RE = re.compile(r"\{[^}]+\}")
NAME_RE = re.compile(r'^(SETNAME\s+")(.+)("\s*)$')


def visible_key(line: str) -> str:
    if '"' not in line:
        return ""
    value = line.split('"', 1)[1].rsplit('"', 1)[0]
    # Normal-ROM disassembly keeps compressed bytes after END inside the
    # quoted field; those bytes are not part of the dialogue text.
    value = value.split("{END}", 1)[0]
    value = TOKEN_RE.sub("", value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def queues(lines: list[str]) -> dict[str, deque[int]]:
    result: dict[str, deque[int]] = defaultdict(deque)
    for index, line in enumerate(lines):
        key = visible_key(line)
        if key:
            result[key].append(index)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    imported_say = 0
    imported_names = 0
    files_changed = 0
    for target in sorted(ROOT.glob("*__0.txt")):
        if not re.fullmatch(r"[ksw][A-Za-z0-9]+__0\.txt", target.name, re.I):
            continue
        english_path = NORMAL / target.name
        italian_path = NORMAL / target.name.replace("__0", "__3")
        if not english_path.exists() or not italian_path.exists():
            continue
        current = target.read_text(encoding="utf-8").splitlines()
        english = english_path.read_text(encoding="utf-8").splitlines()
        italian = italian_path.read_text(encoding="utf-8").splitlines()
        english_say = [line for line in english if line.startswith("SAY ")]
        italian_say = [line for line in italian if line.startswith("SAY ")]
        english_names = [line for line in english if line.startswith("SETNAME ")]
        italian_names = [line for line in italian if line.startswith("SETNAME ")]
        say_positions = queues(english_say)
        name_positions = queues(english_names)
        say_index = 0
        name_index = 0
        output: list[str] = []
        changed = False
        local_say = 0
        local_names = 0
        for line in current:
            if line.startswith("SAY "):
                key = visible_key(line)
                candidates = say_positions.get(key)
                if candidates:
                    source_index = candidates.popleft()
                    if source_index < len(italian_say):
                        line = transplant_say(line, italian_say[source_index])
                        imported_say += 1
                        local_say += 1
                        changed = True
                say_index += 1
            elif line.startswith("SETNAME "):
                key = visible_key(line)
                candidates = name_positions.get(key)
                if candidates:
                    source_index = candidates.popleft()
                    if source_index < len(italian_names):
                        match = NAME_RE.match(italian_names[source_index])
                        if match:
                            line = f'SETNAME "{clean_name(match.group(2))}"'
                            imported_names += 1
                            local_names += 1
                            changed = True
                name_index += 1
            output.append(line)
        if changed:
            files_changed += 1
            if args.apply:
                target.write_text("\n".join(output) + "\n", encoding="utf-8")
        print(f"{target.name}: SAY={local_say} NAME={local_names}" + (" APPLIED" if args.apply else ""))
    print(f"FILES_CHANGED={files_changed} IMPORTED_SAY={imported_say} IMPORTED_NAMES={imported_names}")


if __name__ == "__main__":
    main()
