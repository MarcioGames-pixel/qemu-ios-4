#!/usr/bin/env python3
"""Create blank 1 MiB iPhone 3GS SPI-NOR images for emulator testing.

The files are erased-flash placeholders (all bytes 0xff), not firmware and
not a substitute for a legally obtained dump. The current board model uses a
read-only base image plus an optional separate writable overlay.
"""
from __future__ import annotations

import argparse
from pathlib import Path

NOR_SIZE = 1 << 20


def create(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists (pass --force to replace it)")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        chunk = b"\xff" * 65536
        remaining = NOR_SIZE
        while remaining:
            amount = min(remaining, len(chunk))
            stream.write(chunk[:amount])
            remaining -= amount


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="output directory for nor.bin and nor-rw.bin")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()
    try:
        create(args.directory / "nor.bin", args.force)
        create(args.directory / "nor-rw.bin", args.force)
    except OSError as exc:
        parser.error(str(exc))
    print(f"Created blank erased-flash images ({NOR_SIZE} bytes each) in {args.directory}")
    print("These images contain no iBoot, NVRAM, or restore firmware.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
