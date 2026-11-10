import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cogs import adventure

from core import storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "profiles.json"

    def tearDown(self):
        self.temp.cleanup()

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

    def test_backup_tracks_latest_valid_database_before_each_save(self):
        storage._BACKUPS_CREATED.clear()
        storage.atomic_json_save({"profiles": {"123": {"level": 1}}}, self.path)
        storage.atomic_json_save({"profiles": {"123": {"level": 2}}}, self.path)
        storage.atomic_json_save({"profiles": {"123": {"level": 3}}}, self.path)
        backup = self.path.with_name("profiles.backup.json")
        self.assertEqual(
            json.loads(backup.read_text(encoding="utf-8")),
            {"profiles": {"123": {"level": 2}}},
        )

    def test_invalid_existing_file_is_not_promoted_to_backup(self):
        self.path.write_text("not json", encoding="utf-8")
        storage.atomic_json_save({"profiles": {}}, self.path)
        self.assertFalse(self.path.with_name("profiles.backup.json").exists())
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"profiles": {}})


    def test_player_database_recovers_from_last_known_good_backup(self):
        root = Path(self.temp.name)
        database = root / "peak_game.json"
        backup = root / "peak_game.backup.json"
        broken = root / "peak_game.broken.json"
        expected = {"profiles": {"123": {"level": 900}}, "raids": {}, "custom_weapons": {}}
        database.write_text("{ damaged json", encoding="utf-8")
        backup.write_text(json.dumps(expected), encoding="utf-8")
        storage._BACKUPS_CREATED.clear()

        with patch.object(adventure, "ROOT", root), patch.object(adventure, "DB_FILE", database), patch.object(adventure, "OLD_DB", root / "missing.sqlite3"):
            recovered = adventure.load()

        self.assertEqual(recovered["profiles"]["123"]["level"], 900)
        self.assertTrue(broken.exists())
        self.assertEqual(json.loads(database.read_text(encoding="utf-8"))["profiles"]["123"]["level"], 900)

    def test_invalid_profile_shape_recovers_from_backup(self):
        root = Path(self.temp.name)
        database = root / "peak_game.json"
        backup = root / "peak_game.backup.json"
        expected = {"profiles": {"123": {"level": 900}}, "raids": {}, "custom_weapons": {}}
        database.write_text(json.dumps({"profiles": {"123": None}}), encoding="utf-8")
        backup.write_text(json.dumps(expected), encoding="utf-8")

        with patch.object(adventure, "ROOT", root), patch.object(adventure, "DB_FILE", database), patch.object(adventure, "OLD_DB", root / "missing.sqlite3"):
            recovered = adventure.load()

        self.assertEqual(recovered["profiles"]["123"]["level"], 900)

    def test_damaged_player_database_never_silently_becomes_empty(self):
        root = Path(self.temp.name)
        database = root / "peak_game.json"
        database.write_text("{ damaged json", encoding="utf-8")
        storage._BACKUPS_CREATED.clear()

        with patch.object(adventure, "ROOT", root), patch.object(adventure, "DB_FILE", database), patch.object(adventure, "OLD_DB", root / "missing.sqlite3"):
            with self.assertRaises(RuntimeError):
                adventure.load()

        self.assertTrue(database.exists())
        self.assertEqual(database.read_text(encoding="utf-8"), "{ damaged json")

if __name__ == "__main__":
    unittest.main()
