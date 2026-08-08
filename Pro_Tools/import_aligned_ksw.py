#!/usr/bin/env python3
"""Safely transplant official Italian lines into Professional k/s/w scripts.

Professional files often contain extra or missing branches compared with the
normal game.  This tool uses the normal English variant as an anchor: a line
is imported only when its visible English text matches a normal-game line in
the same forward sequence.  Unmatched Professional-only lines are left for
manual translation.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path('Pro_Tools').resolve()))
from import_official_story import clean_name, transplant_say  # noqa: E402

ROOT = Path('Translation/SCRIPTS')
NORMAL = Path('game/tmp/normal_scripts')
TOKEN_RE = re.compile(r'\{[^}]+\}')
NAME_RE = re.compile(r'^(SETNAME\s+")(.+)("\s*)$')


def visible_key(line: str) -> str:
    value = line.split('"', 1)[1].rsplit('"', 1)[0]
    value = TOKEN_RE.sub('', value).lower()
    value = re.sub(r'[^a-z0-9]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def forward_matches(current: list[str], source: list[str]) -> dict[int, int]:
    positions: dict[str, deque[int]] = defaultdict(deque)
    for index, line in enumerate(source):
        positions[visible_key(line)].append(index)
    result: dict[int, int] = {}
    last = -1
    for index, line in enumerate(current):
        key = visible_key(line)
        candidates = positions[key]
        while candidates and candidates[0] <= last:
            candidates.popleft()
        if candidates:
            result[index] = candidates.popleft()
            last = result[index]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--redo', action='store_true', help='start every target from its HEAD skeleton')
    args = parser.parse_args()
    imported_say = 0
    imported_names = 0
    files_changed = 0
    for target in sorted(ROOT.glob('*__0.txt')):
        if not re.fullmatch(r'[ksw][A-Za-z0-9]+__0\.txt', target.name, re.I):
            continue
        english_path = NORMAL / target.name
        italian_path = NORMAL / target.name.replace('__0', '__3')
        if not english_path.exists() or not italian_path.exists():
            continue
        if args.redo:
            relative = target.as_posix()
            current_text = subprocess.run(
                ['git', '-c', 'core.autocrlf=true', 'show', f'HEAD:{relative}'],
                check=True, capture_output=True, text=True,
            ).stdout
            current_lines = current_text.splitlines()
        else:
            current_lines = target.read_text(encoding='utf-8').splitlines()
        english_lines = english_path.read_text(encoding='utf-8').splitlines()
        italian_lines = italian_path.read_text(encoding='utf-8').splitlines()
        current_say = [line for line in current_lines if line.startswith('SAY ')]
        english_say = [line for line in english_lines if line.startswith('SAY ')]
        italian_say = [line for line in italian_lines if line.startswith('SAY ')]
        say_map = forward_matches(current_say, english_say)
        current_names = [line for line in current_lines if line.startswith('SETNAME ')]
        english_names = [line for line in english_lines if line.startswith('SETNAME ')]
        italian_names = [line for line in italian_lines if line.startswith('SETNAME ')]
        name_map = forward_matches(current_names, english_names)
        if not say_map and not name_map:
            continue
        say_index = 0
        name_index = 0
        output: list[str] = []
        changed = False
        for line in current_lines:
            if line.startswith('SAY '):
                source_index = say_map.get(say_index)
                if source_index is not None:
                    line = transplant_say(line, italian_say[source_index])
                    imported_say += 1
                    changed = True
                say_index += 1
            elif line.startswith('SETNAME '):
                source_index = name_map.get(name_index)
                if source_index is not None and source_index < len(italian_names):
                    match = NAME_RE.match(italian_names[source_index])
                    if match:
                        line = f'SETNAME "{clean_name(match.group(2))}"'
                        imported_names += 1
                        changed = True
                name_index += 1
            output.append(line)
        if changed:
            files_changed += 1
            if args.apply:
                target.write_text('\n'.join(output) + '\n', encoding='utf-8')
        print(f'{target.name}: SAY_MATCH={len(say_map)}/{len(current_say)} NAME_MATCH={len(name_map)}/{len(current_names)}' + (' APPLIED' if args.apply else ''))
    print(f'FILES_CHANGED={files_changed} IMPORTED_SAY={imported_say} IMPORTED_NAMES={imported_names}')


if __name__ == '__main__':
    main()
