import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared_human import resolve_asset, asset_sha256

class AssetPathTests(unittest.TestCase):
    def test_missing_is_actionable(self):
        with self.assertRaisesRegex(FileNotFoundError, 'rebuild_human.py'):
            resolve_asset('/nonexistent/shared-human.blend')

    def test_explicit_path_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'human.blend'
            path.write_bytes(b'asset')
            with patch.dict(os.environ, {'HUMAN_BLEND': '/nonexistent/override.blend'}):
                self.assertEqual(resolve_asset(path), path.resolve())
            self.assertEqual(asset_sha256(path), hashlib.sha256(b'asset').hexdigest())

    def test_environment_override(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'human.blend'
            path.touch()
            with patch.dict(os.environ, {'HUMAN_BLEND': str(path)}):
                self.assertEqual(resolve_asset(), path.resolve())

if __name__ == '__main__':
    unittest.main()
