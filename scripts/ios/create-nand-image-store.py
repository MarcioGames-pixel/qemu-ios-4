#!/usr/bin/env python3
"""Create an empty NANDImage store for QEMU's nand-image helper.

This creates erased-page storage only. It does NOT infer iPhone 3GS NAND
geometry or create bootable firmware. Pass geometry from a verified N88AP
device-tree / flash-chip source before using it with a board model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORMAT = "nand-xor-blank-v2"
BLANKS = {"ff", "n72-generated"}


def create_store(
    directory: Path,
    *,
    chips: int,
    page_bytes: int,
    spare_bytes: int,
    pages_per_block: int,
    blocks_per_chip: int,
    blank: str,
    force: bool = False,
) -> None:
    if chips < 1 or chips > 8:
        raise ValueError("chips must be in range 1..8")
    if min(page_bytes, spare_bytes, pages_per_block, blocks_per_chip) < 1:
        raise ValueError("all geometry values must be positive")
    if blank not in BLANKS:
        raise ValueError(f"blank must be one of: {', '.join(sorted(BLANKS))}")
    if blank == "n72-generated" and spare_bytes < 12:
        raise ValueError("n72-generated blank requires spare_bytes >= 12")

    directory.mkdir(parents=True, exist_ok=True)
    geometry_path = directory / "geometry.json"
    if geometry_path.exists() and not force:
        raise FileExistsError(f"{geometry_path} exists (use --force to replace)")
    geometry = {
        "storage_format": FORMAT,
        "blank": blank,
        "chip_selects": chips,
        "page_bytes": page_bytes,
        "spare_bytes": spare_bytes,
        "pages_per_block": pages_per_block,
        "blocks_per_ce": blocks_per_chip,
    }
    geometry_path.write_text(json.dumps(geometry, indent=2) + "\n", encoding="utf-8")

    # The store is XOR-encoded against its blank record, so an all-zero sparse
    # file represents erased pages without allocating the full flash capacity.
    file_size = page_bytes + spare_bytes
    file_size *= pages_per_block * blocks_per_chip
    for chip in range(chips):
        path = directory / f"cs{chip}.pages"
        if path.exists() and not force:
            raise FileExistsError(f"{path} exists (use --force to replace)")
        with path.open("wb") as stream:
            stream.truncate(file_size)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--chips", type=int, required=True)
    parser.add_argument("--page-bytes", type=int, required=True)
    parser.add_argument("--spare-bytes", type=int, required=True)
    parser.add_argument("--pages-per-block", type=int, required=True)
    parser.add_argument("--blocks-per-chip", type=int, required=True)
    parser.add_argument("--blank", choices=sorted(BLANKS), default="ff")
    parser.add_argument("--force", action="store_true", help="replace geometry and chip files")
    args = parser.parse_args()
    try:
        create_store(
            args.directory,
            chips=args.chips,
            page_bytes=args.page_bytes,
            spare_bytes=args.spare_bytes,
            pages_per_block=args.pages_per_block,
            blocks_per_chip=args.blocks_per_chip,
            blank=args.blank,
            force=args.force,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Created erased NAND store at {args.directory}")
    print("Not bootable; geometry is supplied by you and must match the modeled chip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
