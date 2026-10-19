#!/usr/bin/env python3
"""Inspect and extract public firmware payloads from an iPhone2,1 iOS 6.0 IPSW.

This does not manufacture NAND contents or extract the immutable BootROM from
silicon. It only extracts files actually present in the user's IPSW.
"""
from __future__ import annotations

import argparse
import hashlib
import plistlib
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED = {
    "ProductType": "iPhone2,1",
    "ProductVersion": "6.0",
    "ProductBuildVersion": "10A403",
}
BOOT_RE = re.compile(
    r"(?:^|/)(?:iBSS|iBEC|iBoot|LLB|DeviceTree|applelogo|"
    r"recoverymode|batterylow[01]?|glyphcharging|glyphplugin|"
    r"batteryfull)[^/]*|(?:^|/)kernelcache[^/]*",
    re.IGNORECASE,
)
MANIFESTS = {"BuildManifest.plist", "Restore.plist", "Info.plist"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and all(part not in ("..", "") for part in p.parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipsw", type=Path, help="path to iPhone2,1_6.0_10A403_Restore.ipsw")
    parser.add_argument("--out", type=Path, default=Path(".artifacts/firmware/iphone3gs-6.0-10A403"))
    args = parser.parse_args()

    ipsw = args.ipsw
    if not ipsw.is_file():
        parser.error(f"IPSW not found: {ipsw}")

    try:
        with zipfile.ZipFile(ipsw) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"corrupt ZIP member: {bad}")
            names = archive.namelist()
            info_name = next((n for n in names if PurePosixPath(n).name == "Info.plist"), None)
            if info_name is None:
                raise ValueError("Info.plist is missing; this does not look like a restore IPSW")
            info = plistlib.loads(archive.read(info_name))
            for key, expected in EXPECTED.items():
                actual = info.get(key)
                if actual != expected:
                    raise ValueError(f"{key} mismatch: found {actual!r}, expected {expected!r}")

            selected = []
            for name in names:
                base = PurePosixPath(name).name
                lower = name.lower()
                if not safe_member(name) or name.endswith("/"):
                    continue
                if base in MANIFESTS or "all_flash/all_flash.n88ap" in lower or (
                    "n88ap" in lower and BOOT_RE.search(name)
                ) or re.search(r"(?:^|/)kernelcache[^/]*$", name, re.I):
                    selected.append(name)

            if not selected:
                raise ValueError("no N88AP boot/NOR payloads found in IPSW")

            args.out.mkdir(parents=True, exist_ok=True)
            report = []
            for name in sorted(set(selected)):
                dest = args.out.joinpath(*PurePosixPath(name).parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                data = archive.read(name)
                dest.write_bytes(data)
                report.append(f"{hashlib.sha256(data).hexdigest()}  {len(data):>12}  {name}")
            (args.out / "SHA256SUMS.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
            print(f"Verified IPSW: {ipsw}")
            print(f"Device/build: {info['ProductType']} / iOS {info['ProductVersion']} ({info['ProductBuildVersion']})")
            print(f"Extracted {len(set(selected))} manifest/boot/NOR files to: {args.out}")
            print("SHA-256 inventory:", args.out / "SHA256SUMS.txt")
            print("Note: NAND is virtual persistent storage and must be initialized by the emulator.")
            print("Note: BootROM is immutable silicon ROM and is not contained in the IPSW.")
    except (zipfile.BadZipFile, KeyError, plistlib.InvalidFileException, ValueError, OSError) as exc:
        print(f"firmware inspection failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
