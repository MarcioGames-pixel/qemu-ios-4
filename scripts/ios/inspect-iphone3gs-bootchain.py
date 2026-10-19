#!/usr/bin/env python3
"""Inventory the iPhone2,1 iOS 6 IPSW boot chain without claiming to boot it.

The IPSW contains firmware payloads, not the immutable silicon BootROM or a
ready-made NAND dump. IMG3 payloads may be encrypted; this tool only inventories
them and records hashes. It does not decrypt, patch, or execute firmware.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

EXPECTED_PRODUCT = "iPhone2,1"
EXPECTED_VERSION = "6.0"
EXPECTED_BUILD = "10A403"
STAGES = (
    ("LLB", re.compile(r"(^|/)LLB\.", re.I)),
    ("iBSS", re.compile(r"(^|/)iBSS\.", re.I)),
    ("iBEC", re.compile(r"(^|/)iBEC\.", re.I)),
    ("DeviceTree", re.compile(r"DeviceTree", re.I)),
    ("KernelCache", re.compile(r"kernelcache", re.I)),
    ("RestoreRamDisk", re.compile(r"RestoreRamDisk|018-.*\.dmg$", re.I)),
    ("RootFilesystem", re.compile(r"(^|/)018-.*\.dmg$", re.I)),
)

def sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    return digest.hexdigest()

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipsw", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path,
                        help="write the inventory as JSON")
    args = parser.parse_args(argv)

    if not args.ipsw.is_file():
        parser.error(f"IPSW not found: {args.ipsw}")

    try:
        with zipfile.ZipFile(args.ipsw) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            info_name = next((n for n in names if n.lower() == "buildmanifest.plist"), None)
            info_plist = next((n for n in names if n.lower() == "info.plist"), None)
            if not info_plist:
                print("ERROR: IPSW has no Info.plist", file=sys.stderr)
                return 2
            import plistlib
            with zf.open(info_plist) as f:
                info = plistlib.load(f)
            product = info.get("ProductType")
            version = info.get("ProductVersion")
            build = info.get("ProductBuildVersion")
            if (product, version, build) != (EXPECTED_PRODUCT, EXPECTED_VERSION, EXPECTED_BUILD):
                print(f"ERROR: expected {EXPECTED_PRODUCT} iOS {EXPECTED_VERSION} ({EXPECTED_BUILD}); "
                      f"found {product} {version} ({build})", file=sys.stderr)
                return 2

            entries = []
            for stage, pattern in STAGES:
                matches = [n for n in names if pattern.search(n)]
                for name in matches:
                    with zf.open(name) as f:
                        digest = sha256_stream(f)
                    entries.append({"stage": stage, "path": name,
                                    "size": zf.getinfo(name).file_size,
                                    "sha256": digest,
                                    "img3_magic": _has_img3_magic(zf, name)})
            # Restore manifests identify board-specific paths and keys/IV metadata.
            manifests = [n for n in names if "manifest" in n.lower() and n.lower().endswith(".plist")]
            result = {
                "product": product, "version": version, "build": build,
                "build_manifest_present": info_name is not None,
                "payloads": entries,
                "restore_manifests": manifests,
                "limitations": [
                    "Inventory only: no payload decryption or signature validation.",
                    "IPSW does not provide the immutable silicon BootROM.",
                    "A NAND image and an implemented S5L8920 NAND/IOP path are still required.",
                    "Finding a payload does not prove it is the correct boot-stage image."
                ]
            }
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        print(f"ERROR: cannot inspect IPSW: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0

def _has_img3_magic(zf: zipfile.ZipFile, name: str) -> bool:
    # IMG3's big-endian tag is 'Img3'; compressed/encrypted payloads are not decoded.
    with zf.open(name) as f:
        return f.read(4) == b"Img3"

if __name__ == "__main__":
    raise SystemExit(main())
