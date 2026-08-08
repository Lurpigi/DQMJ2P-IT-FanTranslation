#!/usr/bin/env python3
"""Print English diff/current/official-Italian triples for edited story files."""

from __future__ import annotations

import argparse
import subprocess
import re
from pathlib import Path

from common import DTE_TABLE


SAY_RE = re.compile(r"^SAY (.*)$")
SETNAME_RE = re.compile(r"^SETNAME (.*)$")


def say_lines(lines: list[str]) -> list[str]:
    return [match.group(1) for line in lines if (match := SAY_RE.match(line))]


def setname_lines(lines: list[str]) -> list[str]:
    return [match.group(1) for line in lines if (match := SETNAME_RE.match(line))]


def clean_name(value: str) -> str:
    value = value.split("{END}", 1)[0]
    return re.sub(r"\{(1F[0-9A-Fa-f]{2})\}", lambda m: DTE_TABLE.get(m.group(1).upper(), m.group(0)), value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("normal_dir", type=Path)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--only", nargs="*", help="review only the listed script basenames")
    parser.add_argument("--min", type=int, help="lowest d-script number to review")
    parser.add_argument("--max", type=int, help="highest d-script number to review")
    parser.add_argument("--show-names", action="store_true", help="also compare SETNAME lines")
    parser.add_argument("--names-only", action="store_true", help="suppress SAY comparison")
    args = parser.parse_args()

    root = Path.cwd()
    for target in sorted(args.target_dir.glob("d*__0.txt")):
        if args.only and target.name not in args.only:
            continue
        number_match = re.match(r"d(\d+)__0\.txt$", target.name)
        if number_match and args.min is not None and int(number_match.group(1)) < args.min:
            continue
        if number_match and args.max is not None and int(number_match.group(1)) > args.max:
            continue
        relative = target.as_posix()
        old = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        official_path = args.normal_dir / target.name.replace("__0", "__3")
        if not official_path.exists():
            continue
        current = target.read_text(encoding="utf-8").splitlines()
        official = official_path.read_text(encoding="utf-8").splitlines()
        old_say, current_say, official_say = map(say_lines, (old, current, official))
        if args.show_names:
            old_names, current_names, official_names = map(setname_lines, (old, current, official))
            print(f"NAMES {target.name}: {len(old_names)} English / {len(current_names)} current / {len(official_names)} official")
            for index, (english, current_name, italian) in enumerate(
                zip(old_names, current_names, official_names), start=1
            ):
                print(f"  NAME[{index}] EN {english} | CUR {current_name} | IT {clean_name(italian)}")
        if args.names_only:
            continue
        if len(old_say) != len(current_say) or len(old_say) != len(official_say):
            print(f"COUNT MISMATCH {target.name}: English={len(old_say)} current={len(current_say)} official={len(official_say)}")
            continue
        print(f"=== {target.name} ===")
        for index, (english, current_text, italian) in enumerate(
            zip(old_say, current_say, official_say), start=1
        ):
            print(f"[{index}] EN  {english}")
            print(f"    CUR {current_text}")
            print(f"    IT  {italian}")


if __name__ == "__main__":
    main()
