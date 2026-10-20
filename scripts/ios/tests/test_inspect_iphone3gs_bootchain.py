#!/usr/bin/env python3
"""Tests for the iPhone 3GS boot-chain inventory tool."""
import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "inspect-iphone3gs-bootchain.py"


class BootChainInventoryTests(unittest.TestCase):
    def make_ipsw(self, path, product="iPhone2,1"):
        info = {"ProductType": product, "ProductVersion": "6.0",
                "ProductBuildVersion": "10A403"}
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("Info.plist", plistlib.dumps(info))
            zf.writestr("BuildManifest.plist", plistlib.dumps({"test": True}))
            zf.writestr("Firmware/dfu/iBSS.n88ap.RELEASE.dfu", b"Img3test")
            zf.writestr("kernelcache.release.n88", b"kernel-test")
            zf.writestr("018-12345-001.dmg", b"rootfs-test")

    def test_inventory_hashes_and_img3_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ipsw, report = root / "test.ipsw", root / "report.json"
            self.make_ipsw(ipsw)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(ipsw), "--json", str(report)],
                text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["product"], "iPhone2,1")
            self.assertTrue(data["build_manifest_present"])
            self.assertTrue(any(p["stage"] == "iBSS" and p["img3_magic"]
                                for p in data["payloads"]))
            self.assertTrue(any(p["stage"] == "KernelCache"
                                for p in data["payloads"]))
            rootfs = [p for p in data["payloads"] if p["path"].endswith(".dmg")]
            self.assertEqual([p["stage"] for p in rootfs], ["RootFilesystem"])
            self.assertIn("no payload decryption", " ".join(data["limitations"]))

    def test_rejects_wrong_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            ipsw = Path(tmp) / "wrong.ipsw"
            self.make_ipsw(ipsw, product="iPhone1,2")
            result = subprocess.run([sys.executable, str(SCRIPT), str(ipsw)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("expected iPhone2,1", result.stderr)


if __name__ == "__main__":
    unittest.main()
