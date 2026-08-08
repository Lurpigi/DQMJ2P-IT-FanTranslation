#!/usr/bin/env python3
"""Wrap DQMJ2P SAY strings to the game's two-line dialogue window.

The original Italian DQMJ2 scripts use a variable-width font.  This tool uses
the actual glyph advances from font_16x16.NFTR and a calibrated limit of 230
pixels per rendered line.  It leaves line wrapping to the game and uses two
lines per page, inserting WAIT+CLEAR only when a SAY would otherwise need a
third visible line.

Usage:
    python Pro_Tools/format_dialogues.py --check
    python Pro_Tools/format_dialogues.py --apply
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import re
from pathlib import Path


# The official-font measurements and the screenshot review establish a safe
# interval of 226..232 px: "...con il" fits, adding "nome" does not, while
# the quoted second line ends at "la".  230 px reproduces that wrapping.
DEFAULT_WIDTH = 230.0
DEFAULT_LINES = 2
PAGE_CLEAR = "{WAIT}{CLEAR}"

FONT_PATH = (
    Path(__file__).resolve().parents[1]
    / "game" / "romP" / "root" / "font_16x16.NFTR"
)


def _font_widths(path: Path) -> dict[int, int]:
    """Read Unicode-codepoint -> advance-width mappings from an NFTR font."""
    data = path.read_bytes()
    widths: dict[int, int] = {}

    # NFTR blocks are stored with their four-byte signatures byte-reversed in
    # this ROM (HDWC = CWDH, PAMC = CMAP).
    pos = data.index(b"HDWC")
    while pos:
        first = int.from_bytes(data[pos + 8:pos + 10], "little")
        last = int.from_bytes(data[pos + 10:pos + 12], "little")
        for glyph in range(first, last + 1):
            entry = pos + 16 + (glyph - first) * 3
            widths[glyph] = int.from_bytes(
                data[entry + 2:entry + 3], "little", signed=True
            )
        next_ptr = int.from_bytes(data[pos + 12:pos + 16], "little")
        pos = next_ptr - 8 if next_ptr else 0

    cmap: dict[int, int] = {}
    pos = data.index(b"PAMC")
    while pos:
        first = int.from_bytes(data[pos + 8:pos + 10], "little")
        last = int.from_bytes(data[pos + 10:pos + 12], "little")
        method = int.from_bytes(data[pos + 12:pos + 14], "little")
        next_ptr = int.from_bytes(data[pos + 16:pos + 20], "little")
        base = pos + 20
        if method == 0:
            start_glyph = int.from_bytes(data[base:base + 2], "little")
            for codepoint in range(first, last + 1):
                cmap[codepoint] = start_glyph + codepoint - first
        elif method == 1:
            for index, codepoint in enumerate(range(first, last + 1)):
                offset = base + index * 2
                cmap[codepoint] = int.from_bytes(data[offset:offset + 2], "little")
        elif method == 2:
            count = int.from_bytes(data[base:base + 2], "little")
            for index in range(count):
                offset = base + 2 + index * 4
                codepoint = int.from_bytes(data[offset:offset + 2], "little")
                glyph = int.from_bytes(data[offset + 2:offset + 4], "little")
                cmap[codepoint] = glyph
        pos = next_ptr - 8 if next_ptr else 0

    return {
        codepoint: widths[glyph]
        for codepoint, glyph in cmap.items()
        if glyph in widths
    }


try:
    FONT_WIDTHS = _font_widths(FONT_PATH)
except (OSError, ValueError):
    # Keep the checker usable when run without an extracted ROM.  A normal
    # project checkout has the font, so this is only a diagnostic fallback.
    FONT_WIDTHS = {}

def text_width(text: str) -> float:
    """Return the rendered width in NFTR advance pixels."""
    if FONT_WIDTHS:
        # Italian text should be fully covered by the game's font.  The
        # fallback keeps an unmapped character conservative rather than
        # silently treating it as zero-width.
        width = 0
        index = 0
        while index < len(text):
            char = text[index]
            if char == "\\" and index + 1 < len(text):
                # The disassembly writes literal quotation marks as \"; the
                # backslash is syntax and is not rendered by the game.
                index += 1
                char = text[index]
            width += FONT_WIDTHS.get(ord(char), 12)
            index += 1
        return width
    return sum(
        14 if char.isupper() else 10
        for index, char in enumerate(text)
        if not (char == "\\" and index + 1 < len(text))
    )


# 1Fxx entries are DTE digraphs.  Keep the rendered letters, rather than
# merely counting two codepoints, because uppercase letters are wider.
DTE_TEXT = {
    "1F0B": "S ", "1F0D": "SA", "1F0F": "SC", "1F11": "SE",
    "1F14": "SH", "1F15": "SI", "1F1B": "SO", "1F1D": "SQ",
    "1F1F": "SS", "1F20": "ST", "1F27": "Sa", "1F29": "Sc",
    "1F2B": "Se", "1F2E": "Sh", "1F2F": "Si", "1F32": "Sl",
    "1F33": "Sm", "1F35": "So", "1F36": "Sp", "1F37": "Sq",
    "1F3A": "St", "1F3B": "Su", "1F3D": "Sw", "1F3F": "Sy",
    "1FE1": "S",
}

CONTROL_RE = re.compile(r"\{(?:[0-9A-Fa-f]{2,4}|[A-Z]+(?:=\d+)?)\}")
DTE_TOKEN_RE = re.compile(r"\{(1F[0-9A-Fa-f]{2})\}")
BOUNDARY_RE = re.compile(r"(\{WAIT\}\{CLEAR\}|\{PAGE\})")
# Some extracted scripts contain literal quotation marks inside SAY text
# without escaping them.  The final quote is the line terminator, so a greedy
# body is the correct parser for this disassembly format.
SAY_RE = re.compile(r'^(SAY)\s+"(.*)"\s*$')


def control_width(token: str) -> float:
    """Return the approximate visible width of a script token."""
    inner = token[1:-1]
    upper = inner.upper()
    if upper == "NAME":
        # Player names are variable-width placeholders.  This is deliberately
        # conservative for the maximum name length accepted by the game.
        return 96.0
    if upper in {"BREAK", "PAGE", "WAIT", "CLEAR", "END"}:
        return 0.0
    if upper.startswith("VOICE=") or upper.startswith("COLOR="):
        return 0.0
    if upper in DTE_TEXT:
        return text_width(DTE_TEXT[upper])
    if re.fullmatch(r"[0-9A-Fa-f]{2,4}", inner):
        # Most opaque E3/1F pairs are formatting or runtime substitutions.
        # Do not count them as visible glyphs; NAME and DTE are handled above.
        return 0.0
    return 0.0


def _tokens(text: str):
    """Yield ('control', token) and ('text', chunk) pieces in source order."""
    pos = 0
    for match in CONTROL_RE.finditer(text):
        if match.start() > pos:
            yield "text", text[pos:match.start()]
        yield "control", match.group(0)
        pos = match.end()
    if pos < len(text):
        yield "text", text[pos:]


def _official_dte_rules() -> dict[tuple[str, str], bool]:
    """Read unambiguous DTE-after-space rules from official Italian text."""
    normal = Path(__file__).resolve().parents[1] / "game" / "tmp" / "normal_scripts"
    rules: defaultdict[tuple[str, str], Counter[bool]] = defaultdict(Counter)
    if not normal.is_dir():
        return {}

    for path in normal.glob("*__3.txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = SAY_RE.fullmatch(line)
            if not match:
                continue
            body = match.group(1)
            for token in DTE_TOKEN_RE.finditer(body):
                cursor = token.end()
                had_gap = False
                while True:
                    whitespace = re.match(r"[ \t]+", body[cursor:])
                    if whitespace:
                        cursor += whitespace.end()
                        had_gap = True
                    if body.startswith("{BREAK}", cursor):
                        cursor += len("{BREAK}")
                        had_gap = True
                        continue
                    break
                suffix = re.match(r"[^\W\d_]+", body[cursor:])
                if suffix:
                    key = (token.group(1).upper(), suffix.group(0).lower())
                    rules[key][had_gap] += 1

    return {
        key: counts.most_common(1)[0][0]
        for key, counts in rules.items()
        if len(counts) == 1
    }


OFFICIAL_DTE_AFTER_SPACE = _official_dte_rules()


def normalize_dte_spacing(body: str) -> str:
    """Apply only DTE spacing patterns confirmed by official Italian text."""
    pieces: list[str] = []
    position = 0
    for match in DTE_TOKEN_RE.finditer(body):
        cursor = match.end()
        had_gap = False
        while True:
            whitespace = re.match(r"[ \t]+", body[cursor:])
            if whitespace:
                cursor += whitespace.end()
                had_gap = True
            if body.startswith("{BREAK}", cursor):
                cursor += len("{BREAK}")
                had_gap = True
                continue
            break
        suffix = re.match(r"[^\W\d_]+", body[cursor:])
        rule = (
            OFFICIAL_DTE_AFTER_SPACE.get(
                (match.group(1).upper(), suffix.group(0).lower())
            )
            if suffix
            else None
        )

        before = body[position:match.start()]
        if rule is not None and before:
            previous = before[-1]
            if (
                not previous.isspace()
                and previous not in "({[\\\"'"
                and previous != "}"
            ):
                before += " "
        pieces.append(before)
        pieces.append(match.group(0))

        position = match.end()
        if rule is True:
            if had_gap:
                pieces.append(body[position:cursor])
                position = cursor
            else:
                pieces.append(" ")
        elif rule is False:
            # Remove a source gap only when official Italian confirms that
            # the token is a prefix of the following word.
            position = cursor
    pieces.append(body[position:])
    return "".join(pieces)


class PageBuilder:
    """Build one or more pages while leaving line wrapping to the game.

    DQMJ2 automatically wraps text at the edge of the dialogue window.  The
    script must therefore not contain a generated BREAK: if our estimate and
    the game choose different word boundaries, that BREAK creates a third
    visible line.  We only count automatic lines here and insert a page clear
    before the word that would start line three.
    """

    def __init__(self, width: float, max_lines: int):
        self.width_limit = width
        self.max_lines = max_lines
        self.parts: list[str] = []
        self.line_width = 0.0
        self.line_count = 1
        self.line_has_text = False
        self.pending_space = False

    def add_control(self, token: str) -> None:
        # BREAK is a source-side manual line break.  In DQMJ2 it is safer to
        # treat it as whitespace and let the renderer choose the line: the
        # official Italian scripts overwhelmingly use PAGE, not BREAK.
        if token == "{BREAK}":
            self.pending_space = True
            return

        visible_width = control_width(token)
        is_visible_token = token[1:-1].upper() == "NAME" or token[1:-1].upper() in DTE_TEXT
        separator = " " if is_visible_token and self.pending_space and self.line_has_text else ""
        if self.pending_space and self.line_has_text and not separator:
            # Preserve a source space before an opaque placeholder such as
            # {E328}; otherwise a later text token could move that space to
            # the other side of the placeholder on the next formatter pass.
            separator = " "
        self.parts.append(separator + token)
        self.line_width += text_width(separator) + visible_width
        if visible_width:
            self.line_has_text = True
        if separator or is_visible_token:
            self.pending_space = False

    def add_word(self, word: str) -> bool:
        """Add a word, returning False when it would require line three."""
        word_width = text_width(word)
        separator = " " if self.pending_space and self.line_has_text else ""
        separator_width = text_width(separator)
        if (
            self.line_has_text
            and self.line_width + separator_width + word_width > self.width_limit
        ):
            self.line_count += 1
            if self.line_count > self.max_lines:
                return False
            self.line_width = 0.0
            self.line_has_text = False
            # Keep the source space in the message.  The game needs to see
            # it in order to perform its own automatic wrap; it simply does
            # not consume that space as visible width at the start of a new
            # rendered line.
            separator_width = 0.0

        self.parts.append(separator + word)
        self.line_width += separator_width + word_width
        self.line_has_text = True
        self.pending_space = False
        return True

    def render(self) -> str:
        return "".join(self.parts).rstrip()


def wrap_segment(segment: str, width: float, max_lines: int) -> str:
    pages: list[str] = []
    pending: list[tuple[str, str]] = list(_tokens(segment))
    builder = PageBuilder(width, max_lines)

    while pending:
        kind, value = pending.pop(0)
        if kind == "control":
            builder.add_control(value)
            continue

        parts = re.findall(r"\s+|[^\s]+", value)
        for index, part in enumerate(parts):
            if part.isspace():
                builder.pending_space = True
                continue
            if builder.add_word(part):
                continue

            pages.append(builder.render())
            builder = PageBuilder(width, max_lines)
            builder.add_word(part)

            # The rest of this text chunk continues on the new page.  It is
            # reprocessed as tokens so controls in later chunks stay ordered.
            remainder = "".join(parts[index + 1:])
            if remainder:
                pending.insert(0, ("text", remainder))
            break

    final = builder.render()
    if final or not pages:
        pages.append(final)
    return PAGE_CLEAR.join(page for page in pages if page)


def format_body(body: str, width: float, max_lines: int) -> str:
    # A boundary already present in the Professional translation is not
    # necessarily a deliberate page: earlier passes inserted it merely to
    # compensate for English/Italian line lengths.  Flatten it to whitespace
    # and let the real two-line renderer decide whether a page is needed.
    body = normalize_dte_spacing(body)
    body = BOUNDARY_RE.sub(" ", body)
    body = body.replace("{BREAK}", " ")
    return wrap_segment(body, width, max_lines)


def _canonical_official_key(body: str) -> str:
    """Create a strict text/control key for matching normal and Pro SAYs.

    Layout controls are ignored because the Professional source may contain
    a hand-added WAIT/CLEAR at a different word boundary.  Voice, colour,
    placeholders and other semantic controls remain part of the key, which
    prevents an unrelated line with the same prose from being overwritten.
    DTE entries are expanded so ``{1F29}out`` matches ``Scout``.
    """
    body = body.split("{END}", 1)[0]
    body = body.replace(r'\"', '"')

    def expand_dte(match: re.Match[str]) -> str:
        return DTE_TEXT.get(match.group(1).upper(), match.group(0))

    body = DTE_TOKEN_RE.sub(expand_dte, body)

    def keep_control(match: re.Match[str]) -> str:
        inner = match.group(0)[1:-1]
        if inner.upper() in {"WAIT", "CLEAR", "PAGE", "BREAK"}:
            return " "
        return match.group(0).upper()

    body = CONTROL_RE.sub(keep_control, body)
    return re.sub(r"\s+", " ", body).strip().casefold()


def _official_body_for_pro(body: str) -> str:
    """Convert a normal-ROM official body to the Professional tag dialect."""
    body = body.split("{END}", 1)[0]
    # A normal script often writes PAGE followed by WAIT/CLEAR.  In the
    # Professional scripts that pair represents one transition, not two.
    body = body.replace("{PAGE}{WAIT}{CLEAR}", PAGE_CLEAR)
    body = body.replace("{PAGE}", PAGE_CLEAR)
    body = re.sub(r"(?:\{WAIT\}\{CLEAR\})+$", "", body).rstrip()
    return body


def _load_official_bodies() -> dict[str, dict[str, str]]:
    """Load unique official Italian SAY bodies by matching script file."""
    normal = Path(__file__).resolve().parents[1] / "game" / "tmp" / "normal_scripts"
    result: dict[str, dict[str, str]] = {}
    if not normal.is_dir():
        return result

    candidates: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for path in normal.glob("*__3.txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = SAY_RE.fullmatch(line)
            if not match:
                continue
            body = match.group(2)
            key = _canonical_official_key(body)
            candidates[path.name][key].append(body)

    for filename, by_key in candidates.items():
        unique: dict[str, str] = {}
        for key, bodies in by_key.items():
            cleaned = [_official_body_for_pro(body) for body in bodies]
            if len(set(cleaned)) == 1:
                unique[key] = cleaned[0]
        result[filename] = unique
    return result


OFFICIAL_BODIES = _load_official_bodies()
OFFICIAL_OVERRIDE_COUNT = 0


def official_override(path: Path, body: str) -> str | None:
    """Return the official body when this Pro line is an exact 1:1 match."""
    normal_name = path.name.replace("__0.txt", "__3.txt")
    return OFFICIAL_BODIES.get(normal_name, {}).get(_canonical_official_key(body))


def process_file(path: Path, width: float, max_lines: int, apply: bool) -> tuple[int, int]:
    changed = 0
    say_count = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()

    output = []
    for raw in lines:
        ending = "\r\n" if raw.endswith("\r\n") else "\n" if raw.endswith("\n") else ""
        content = raw[: -len(ending)] if ending else raw
        match = SAY_RE.fullmatch(content)
        if not match:
            output.append(raw)
            continue
        say_count += 1
        global OFFICIAL_OVERRIDE_COUNT
        official = official_override(path, match.group(2))
        if official is not None:
            new_body = official
            OFFICIAL_OVERRIDE_COUNT += 1
        else:
            new_body = format_body(match.group(2), width, max_lines)
        new_line = f'{match.group(1)} "{new_body}"{ending}'
        if new_line != raw:
            changed += 1
        output.append(new_line if apply else raw)

    if apply and changed:
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.writelines(output)
    return say_count, changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--width", type=float, default=DEFAULT_WIDTH)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_LINES)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report files that would change")
    mode.add_argument("--apply", action="store_true", help="rewrite SAY lines in place")
    args = parser.parse_args()

    scripts = args.root / "Translation" / "SCRIPTS"
    if not scripts.is_dir():
        parser.error(f"scripts directory not found: {scripts}")

    total_says = total_changed = 0
    for path in sorted(scripts.glob("*.txt")):
        says, changed = process_file(path, args.width, args.max_lines, args.apply)
        total_says += says
        total_changed += changed
        if changed:
            action = "formatted" if args.apply else "would format"
            print(f"{action}: {path.relative_to(args.root)} ({changed} SAY)")

    print(f"SAY_LINES={total_says}")
    print(f"FILES_OR_LINES_CHANGED={total_changed}")
    print(f"OFFICIAL_1TO1_OVERRIDES={OFFICIAL_OVERRIDE_COUNT}")
    print(f"WIDTH={args.width} MAX_LINES={args.max_lines}")


if __name__ == "__main__":
    main()
