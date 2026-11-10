import json
import tempfile
import unittest
from pathlib import Path

from core import storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        storage._BACKUPS_CREATED.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "profiles.json"

    def tearDown(self):
        self.temp.cleanup()
        storage._BACKUPS_CREATED.clear()

    def test_atomic_save_writes_valid_json(self):
        payload = {"profiles": {"123": {"level": 9}}, "version": 2}
        storage.atomic_json_save(payload, self.path)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), payload)
        self.assertFalse(list(self.path.parent.glob("*.tmp")))

    def test_first_save_keeps_last_known_good_backup(self):
        original = {"profiles": {"123": {"level": 4}}}
        self.path.write_text(json.dumps(original), encoding="utf-8")
        storage.atomic_json_save({"profiles": {"123": {"level": 5}}}, self.path)
        backup = self.path.with_name("profiles.backup.json")
        self.assertEqual(json.loads(backup.read_text(encoding="utf-8")), original)

    def test_invalid_existing_file_is_not_promoted_to_backup(self):
        self.path.write_text("not json", encoding="utf-8")
        storage.atomic_json_save({"profiles": {}}, self.path)
        self.assertFalse(self.path.with_name("profiles.backup.json").exists())
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"profiles": {}})


if __name__ == "__main__":
    unittest.main()
