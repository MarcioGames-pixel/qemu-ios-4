#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "create-nand-image-store.py"
SPEC = importlib.util.spec_from_file_location("create_nand_image_store", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CreateNANDStoreTests(unittest.TestCase):
    def test_creates_geometry_and_sparse_erased_chip_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "nand"
            MODULE.create_store(
                root, chips=2, page_bytes=2048, spare_bytes=64,
                pages_per_block=64, blocks_per_chip=8, blank="ff",
            )
            geometry = json.loads((root / "geometry.json").read_text())
            self.assertEqual(geometry["storage_format"], "nand-xor-blank-v2")
            self.assertEqual(geometry["chip_selects"], 2)
            self.assertEqual(geometry["blank"], "ff")
            expected_size = (2048 + 64) * 64 * 8
            self.assertEqual((root / "cs0.pages").stat().st_size, expected_size)
            self.assertEqual((root / "cs1.pages").stat().st_size, expected_size)
            # XOR-blank encoding means erased records are represented by zeros.
            self.assertEqual((root / "cs0.pages").read_bytes()[:32], bytes(32))

    def test_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "nand"
            kwargs = dict(chips=1, page_bytes=512, spare_bytes=16,
                          pages_per_block=16, blocks_per_chip=4, blank="ff")
            MODULE.create_store(root, **kwargs)
            with self.assertRaises(FileExistsError):
                MODULE.create_store(root, **kwargs)

    def test_rejects_bad_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                MODULE.create_store(Path(tmp) / "nand", chips=9, page_bytes=512,
                                    spare_bytes=16, pages_per_block=16,
                                    blocks_per_chip=4, blank="ff")

    def test_n72_blank_requires_sufficient_spare(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                MODULE.create_store(Path(tmp) / "nand", chips=1, page_bytes=512,
                                    spare_bytes=8, pages_per_block=16,
                                    blocks_per_chip=4, blank="n72-generated")


if __name__ == "__main__":
    unittest.main()
