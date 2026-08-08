#!/usr/bin/env python3
"""Import official Italian monster names from the normal DQMJ2 archive."""

from __future__ import annotations

import argparse
from pathlib import Path

from inspect_multilang import read_variants


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    variants = read_variants(args.archive)
    english = variants["E"]
    italian = variants["I"]
    mapping: dict[str, str] = {}
    conflicts: set[str] = set()
    for source, target in zip(english, italian):
        key = source.casefold()
        if not source or not target or source == target:
            continue
        previous = mapping.get(key)
        if previous is not None and previous != target:
            conflicts.add(key)
        else:
            mapping[key] = target
    for key in conflicts:
        mapping.pop(key, None)

    with args.target.open("r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()
    changed = 0
    updated: list[str] = []
    for line in lines:
        content = line.rstrip("\r\n")
        ending = line[len(content) :]
        replacement = mapping.get(content.casefold())
        if replacement is not None:
            updated.append(replacement + ending)
            changed += 1
        else:
            updated.append(line)
    if changed:
        with args.target.open("w", encoding="utf-8", newline="") as handle:
            handle.write("".join(updated))
    print(f"official Italian monster names imported: {changed}")
    if conflicts:
        print(f"skipped conflicting source names: {len(conflicts)}")


if __name__ == "__main__":
    main()
