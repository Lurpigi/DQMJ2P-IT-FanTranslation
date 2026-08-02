#!/usr/bin/env python3
"""
DQMJ2P StoreTbl CSV Converter
Converts StoreTbl_A/B/C.bin (per-shop item availability) between binary and CSV.

Binary format:
    header:  4 bytes magic "STRE" + u32 record count (LE)
    records: count x 4 bytes, one per item ID (ID = array index, not stored):
        u16 Rank    - bitmask of shop ranks that stock the item (bit N = rank N)
        u8  ForSale - 0/1, whether the item is ever sold at all
        u8  (pad, always 0)

CSV columns: ID, Name, Rank, ForSale
    - Rank may be given as plain decimal or 0x-prefixed hex.

Usage:
    python store_tbl_csv.py --in <input> --out <output>

    Export: python store_tbl_csv.py --in ./data/StoreTbl_A.bin --out ./StoreTbl_A.csv
    Import: python store_tbl_csv.py --in ./StoreTbl_A.csv --out ./data/StoreTbl_A.bin
"""

import argparse
import csv
import struct
import sys
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
NAMES_FILE = SCRIPT_DIR.parent / 'Translation' / 'STRINGS' / 'msg_itemname.txt'

MAGIC      = b'STRE'
RECORD_LEN = 4


# ── data loaders ──────────────────────────────────────────────────────────────

def load_names() -> list[str]:
    if NAMES_FILE.exists():
        return NAMES_FILE.read_text(encoding='utf-8').splitlines()
    print(f"Warning: Names file not found: {NAMES_FILE}", file=sys.stderr)
    return []


def name_for_id(names: list[str], item_id: int) -> str:
    return names[item_id] if 0 <= item_id < len(names) else ''


def parse_int(cell: str, context: str) -> int:
    cell = cell.strip()
    try:
        return int(cell, 0) if cell.lower().startswith('0x') else int(cell)
    except ValueError:
        raise ValueError(f"{context}: invalid integer '{cell}'")


# ── binary <-> records ────────────────────────────────────────────────────────

def read_binary_table(filepath: Path) -> list[tuple[int, int]]:
    """Return list of (rank, for_sale), one per item ID."""
    data = filepath.read_bytes()
    magic, count = struct.unpack_from('<4sI', data, 0)
    if magic != MAGIC:
        sys.exit(f"Error: {filepath} does not start with {MAGIC!r} magic (got {magic!r})")

    expected = 8 + count * RECORD_LEN
    if len(data) != expected:
        sys.exit(f"Error: {filepath} size {len(data)} != expected {expected} "
                  f"for {count} records")

    records = []
    for i in range(count):
        rank, flags = struct.unpack_from('<HH', data, 8 + i * RECORD_LEN)
        for_sale = flags & 0xFF
        pad = flags >> 8
        if pad != 0:
            print(f"Warning: record {i} has non-zero padding byte 0x{pad:02x}",
                  file=sys.stderr)
        records.append((rank, for_sale))
    return records


def save_binary_table(filepath: Path, records: list[tuple[int, int]]) -> None:
    data = bytearray()
    data.extend(struct.pack('<4sI', MAGIC, len(records)))
    for rank, for_sale in records:
        data.extend(struct.pack('<HH', rank, for_sale))
    filepath.write_bytes(data)


# ── CSV conversion ────────────────────────────────────────────────────────────

def export_to_csv(input_path: Path, output_path: Path, names: list[str]) -> None:
    records = read_binary_table(input_path)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Rank', 'ForSale'])
        for item_id, (rank, for_sale) in enumerate(records):
            writer.writerow([item_id, name_for_id(names, item_id), rank, for_sale])

    print(f"Exported {len(records)} records -> {output_path}")


def import_from_csv(input_path: Path, output_path: Path) -> None:
    rows: dict[int, tuple[int, int]] = {}
    errors = []

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            context = f"Row {row_num}"
            try:
                item_id = parse_int(row['ID'], context)
                rank    = parse_int(row['Rank'], context)
                for_sale = parse_int(row['ForSale'], context)
            except ValueError as e:
                errors.append(str(e))
                continue

            if item_id in rows:
                errors.append(f"{context}: duplicate ID {item_id}")
                continue
            rows[item_id] = (rank, for_sale)

    if errors:
        print("Import errors found:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)

    count = len(rows)
    missing = [i for i in range(count) if i not in rows]
    if missing:
        print(f"Error: CSV must have contiguous IDs 0..{count - 1}; "
              f"missing {missing[:10]}{'...' if len(missing) > 10 else ''}",
              file=sys.stderr)
        sys.exit(1)

    records = [rows[i] for i in range(count)]
    save_binary_table(output_path, records)
    print(f"Imported {len(records)} records -> {output_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description='DQMJ2P StoreTbl CSV Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('--in', dest='input', required=True, metavar='FILE',
                    help='Input file (binary .bin or CSV .csv)')
    ap.add_argument('--out', dest='output', required=True, metavar='FILE',
                    help='Output file (CSV .csv or binary .bin)')
    args = ap.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix == '.bin' and output_path.suffix == '.csv':
        names = load_names()
        print(f"Exporting: {input_path} -> {output_path}")
        export_to_csv(input_path, output_path, names)
    elif input_path.suffix == '.csv' and output_path.suffix == '.bin':
        print(f"Importing: {input_path} -> {output_path}")
        if output_path.exists():
            print(f"Warning: Output file will be overwritten: {output_path}", file=sys.stderr)
        import_from_csv(input_path, output_path)
    else:
        print(f"Error: Need .bin <-> .csv conversion. "
              f"Got: {input_path.suffix} -> {output_path.suffix}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
