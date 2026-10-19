#!/usr/bin/env python3
"""Tests for the non-destructive NAND page-store inspector."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "inspect-iphone3gs-nand.py"


class NANDStoreInspectorTests(unittest.TestCase):
    def make_store(self, root: Path):
        geometry = {
            "page_bytes": 512, "spare_bytes": 16, "pages_per_block": 4,
            "blocks_per_ce": 2, "ce_per_bus": 1, "buses": 1,
            "chip_id": "ec75", "storage_format": "legacy-zero-blank-v1"
        }
        (root / "geometry.json").write_text(json.dumps(geometry), encoding="utf-8")
        (root / "bus0-ce0.pages").write_bytes(bytes((512 + 16) * 4 * 2))
        return geometry

    def run_inspector(self, root):
        return subprocess.run([sys.executable, str(SCRIPT), str(root)],
                              text=True, capture_output=True)

    def test_accepts_well_formed_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_store(Path(tmp))
            result = self.run_inspector(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["valid"])
            self.assertEqual(report["expected_bytes_per_chip"], 4224)

    def test_rejects_wrong_page_file_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_store(root)
            (root / "bus0-ce0.pages").write_bytes(b"short")
            result = self.run_inspector(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("expected 4224 bytes", result.stdout)

    def test_rejects_missing_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_inspector(Path(tmp))
            self.assertEqual(result.returncode, 2)
            self.assertIn("missing geometry.json", result.stdout)

    def test_rejects_unknown_storage_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            geometry = self.make_store(root)
            geometry["storage_format"] = "made-up-format"
            (root / "geometry.json").write_text(json.dumps(geometry), encoding="utf-8")
            result = self.run_inspector(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsupported storage_format", result.stdout)


if __name__ == "__main__":
    unittest.main()
