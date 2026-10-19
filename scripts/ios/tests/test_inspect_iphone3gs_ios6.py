#!/usr/bin/env python3
"""Unit tests for the iPhone 3GS iOS 6 IPSW inspector."""
import hashlib
import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "inspect-iphone3gs-ios6.py"


class InspectIPSWTests(unittest.TestCase):
    def make_ipsw(self, path, *, product="iPhone2,1", version="6.0", build="10A403"):
        info = {
            "ProductType": product,
            "ProductVersion": version,
            "ProductBuildVersion": build,
        }
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Info.plist", plistlib.dumps(info))
            archive.writestr("BuildManifest.plist", plistlib.dumps({"test": True}))
            archive.writestr(
                "Firmware/all_flash/all_flash.n88ap.production/iBoot.n88ap.RELEASE.dfu",
                b"fake-iBoot-test-payload",
            )
            archive.writestr("kernelcache.release.n88", b"fake-kernelcache-test-payload")
            archive.writestr("Payload/not-needed.txt", b"not selected")

    def test_extracts_expected_firmware_and_hash_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ipsw = root / "test.ipsw"
            out = root / "out"
            self.make_ipsw(ipsw)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(ipsw), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            boot = out / "Firmware/all_flash/all_flash.n88ap.production/iBoot.n88ap.RELEASE.dfu"
            self.assertEqual(boot.read_bytes(), b"fake-iBoot-test-payload")
            self.assertTrue((out / "BuildManifest.plist").is_file())
            self.assertFalse((out / "Payload/not-needed.txt").exists())
            sums = (out / "SHA256SUMS.txt").read_text()
            self.assertIn(hashlib.sha256(b"fake-iBoot-test-payload").hexdigest(), sums)

    def test_rejects_wrong_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ipsw = root / "wrong.ipsw"
            self.make_ipsw(ipsw, product="iPhone1,2")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(ipsw), "--out", str(root / "out")],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ProductType mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
