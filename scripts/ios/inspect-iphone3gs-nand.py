#!/usr/bin/env python3
"""Validate a file-backed NAND page-store manifest without guessing chip geometry.

This is a diagnostic for candidate NAND stores, not an N88AP geometry database
or a NAND controller. It never creates or modifies flash files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FORMATS = {"legacy-zero-blank-v1", "nand-xor-ff-v2"}
POSITIVE = ("page_bytes", "pages_per_block", "blocks_per_ce", "ce_per_bus", "buses")
NONNEGATIVE = ("spare_bytes",)


def inspect_store(root: Path) -> tuple[dict, list[str]]:
    errors: list[str] = []
    manifest = root / "geometry.json"
    if not manifest.is_file():
        return {"directory": str(root), "valid": False, "errors": ["missing geometry.json"]}, errors

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"directory": str(root), "valid": False,
                "errors": [f"cannot parse geometry.json: {exc}"]}, errors
    if not isinstance(data, dict):
        return {"directory": str(root), "valid": False,
                "errors": ["geometry.json must contain a JSON object"]}, errors

    for key in POSITIVE:
        if type(data.get(key)) is not int or data[key] <= 0:
            errors.append(f"{key} must be a positive integer")
    for key in NONNEGATIVE:
        if type(data.get(key)) is not int or data[key] < 0:
            errors.append(f"{key} must be a non-negative integer")
    chip_id = data.get("chip_id")
    if not isinstance(chip_id, str) or not chip_id or any(c not in "0123456789abcdefABCDEF" for c in chip_id):
        errors.append("chip_id must be a non-empty hexadecimal string")
    storage_format = data.get("storage_format", "legacy-zero-blank-v1")
    if storage_format not in FORMATS:
        errors.append(f"unsupported storage_format: {storage_format!r}")

    required = [*POSITIVE, *NONNEGATIVE]
    if not any(err.startswith(tuple(f"{k} " for k in required)) for err in errors):
        page_bytes = data["page_bytes"]
        spare_bytes = data["spare_bytes"]
        ppb = data["pages_per_block"]
        blocks = data["blocks_per_ce"]
        buses = data["buses"]
        ce_per_bus = data["ce_per_bus"]
        if page_bytes + spare_bytes <= 0:
            errors.append("page_bytes + spare_bytes must be positive")
        else:
            expected_size = page_bytes * 0 + (page_bytes + spare_bytes) * ppb * blocks
            for bus in range(buses):
                for ce in range(ce_per_bus):
                    page_file = root / f"bus{bus}-ce{ce}.pages"
                    if not page_file.is_file():
                        errors.append(f"missing {page_file.name}")
                    elif page_file.stat().st_size != expected_size:
                        errors.append(f"{page_file.name} size is {page_file.stat().st_size}; expected {expected_size} bytes")

    result = {
        "directory": str(root),
        "valid": not errors,
        "geometry": data,
        "storage_format_effective": storage_format,
        "expected_bytes_per_chip": (
            (data["page_bytes"] + data["spare_bytes"]) *
            data["pages_per_block"] * data["blocks_per_ce"]
            if all(type(data.get(k)) is int and data[k] > 0 for k in POSITIVE)
            and type(data.get("spare_bytes")) is int and data["spare_bytes"] >= 0
            else None
        ),
        "errors": errors,
        "limitations": [
            "Validation only; no NAND geometry is inferred for iPhone2,1/N88AP.",
            "A structurally valid store is not proof of correct chip ID, ECC/OOB, bad-block layout, or bootability.",
            "This tool does not read, decrypt, reconstruct, or modify NAND contents."
        ]
    }
    return result, errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="directory containing geometry.json and busN-ceN.pages")
    parser.add_argument("--json", dest="json_path", type=Path, help="also write report JSON")
    args = parser.parse_args(argv)
    result, _ = inspect_store(args.directory)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(rendered + "\\n", encoding="utf-8")
    return 0 if result.get("valid") else 2


if __name__ == "__main__":
    raise SystemExit(main())
