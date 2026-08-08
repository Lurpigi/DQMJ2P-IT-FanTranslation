#!/usr/bin/env python3
"""Inspect the language variants packed in a normal DQMJ2 FPK archive."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import msgtool


def read_variants(path: Path) -> dict[str, list[str]]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 4)[0]
    table = msgtool.load_table()
    decode = msgtool.build_decoder(table)
    variants: dict[str, list[str]] = {}
    for index in range(count):
        record = 0 if index == 0 else 0x30 + (index - 1) * 0x28
        name_start = record + 8 if index == 0 else record
        name = data[name_start : name_start + 24].split(b"\0", 1)[0].decode("ascii")
        field_offset = record + (0x28 if index == 0 else 0x20)
        offset, size = struct.unpack_from("<II", data, field_offset)
        payload = data[offset : offset + size]
        entries = msgtool.split_entries(payload)
        variants[name[-1]] = [decode(entry) for entry in entries]
    return variants


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    variants = read_variants(args.archive)
    languages = sorted(variants)
    print("languages:", ", ".join(languages))
    print("entry counts:", {key: len(variants[key]) for key in languages})
    for index in range(1, max(map(len, variants.values()))):
        values = [variants[key][index] for key in languages]
        if len(set(values)) > 1:
            print(index, " | ".join(values))


if __name__ == "__main__":
    main()
