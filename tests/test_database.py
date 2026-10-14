import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_path_patch = patch.object(database, "DB_PATH", self.db_path)
        self.db_path_patch.start()
        database.initialize_database()

    def tearDown(self) -> None:
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_add_and_get_health_log(self) -> None:
        log_id = database.add_health_log(
            systolic=120,
            diastolic=80,
            glucose=5.6,
            notes="Before breakfast",
        )

        entry = database.get_health_log(log_id)

        self.assertEqual(entry["id"], log_id)
        self.assertEqual(entry["systolic"], 120)
        self.assertEqual(entry["diastolic"], 80)
        self.assertEqual(entry["glucose"], 5.6)
        self.assertEqual(entry["notes"], "Before breakfast")
        self.assertIsNotNone(entry["recorded_at"])

        [queue_item] = database.get_pending_sync_items()
        self.assertEqual(queue_item["entity_type"], "health_log")
        self.assertEqual(queue_item["entity_id"], log_id)
        self.assertEqual(queue_item["operation"], "upsert")
        self.assertEqual(queue_item["synced"], 0)

    def test_recent_logs_are_sorted_newest_first_and_limited(self) -> None:
        first_id = database.add_health_log(glucose=5.2)
        second_id = database.add_health_log(glucose=6.1)
        third_id = database.add_health_log(glucose=5.8)

        entries = database.get_recent_logs(limit=2)

        self.assertEqual([entry["id"] for entry in entries], [third_id, second_id])
        self.assertNotIn(first_id, [entry["id"] for entry in entries])

    def test_delete_health_log(self) -> None:
        log_id = database.add_health_log(glucose=5.6)

        database.delete_health_log(log_id)

        self.assertIsNone(database.get_health_log(log_id))
        self.assertEqual(database.get_recent_logs(), [])
        pending = database.get_pending_sync_items()
        self.assertEqual([item["operation"] for item in pending], ["upsert", "delete"])
        self.assertEqual(pending[-1]["entity_id"], log_id)

    def test_clear_all_logs(self) -> None:
        first_id = database.add_health_log(systolic=120, diastolic=80)
        second_id = database.add_health_log(glucose=5.6)

        database.clear_all_logs()

        self.assertEqual(database.get_recent_logs(), [])
        deletes = [
            item
            for item in database.get_pending_sync_items()
            if item["operation"] == "delete"
        ]
        self.assertEqual([item["entity_id"] for item in deletes], [first_id, second_id])

    def test_mark_sync_item_as_synced(self) -> None:
        database.add_health_log(glucose=5.6)
        [queue_item] = database.get_pending_sync_items()

        self.assertTrue(database.mark_sync_item_synced(queue_item["id"]))
        self.assertFalse(database.mark_sync_item_synced(queue_item["id"]))
        self.assertEqual(database.get_pending_sync_items(), [])

    def test_pending_sync_limit_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            database.get_pending_sync_items(limit=0)

    def test_values_are_stored_as_parameters(self) -> None:
        notes = "'; DROP TABLE health_logs; --"
        database.add_health_log(glucose=5.6, notes=notes)

        self.assertEqual(database.get_recent_logs()[0]["notes"], notes)
        with closing(database.get_connection()) as connection:
            self.assertIsNotNone(
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE name = 'health_logs'"
                ).fetchone()
            )


if __name__ == "__main__":
    unittest.main()