import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import Config


class ConfigSaveTests(unittest.TestCase):
    def test_save_creates_parent_directories_and_persists_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nested" / "config.json"
            config = Config(config_path)

            config.set("default_mode", "raw")

            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["default_mode"], "raw")
            self.assertEqual(saved["groq_api_key"], "")

    def test_failed_save_preserves_existing_file_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            original_contents = '{"groq_api_key": "gsk_existing"}'
            config_path.write_text(original_contents, encoding="utf-8")
            config = Config(config_path)

            def partially_write_then_fail(data, file_obj, **kwargs):
                file_obj.write("{")
                raise OSError("simulated disk failure")

            with patch("src.config.json.dump", side_effect=partially_write_then_fail):
                config.set("groq_api_key", "gsk_new")

            self.assertEqual(
                config_path.read_text(encoding="utf-8"), original_contents
            )
            self.assertEqual(list(config_path.parent.glob(".config.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
