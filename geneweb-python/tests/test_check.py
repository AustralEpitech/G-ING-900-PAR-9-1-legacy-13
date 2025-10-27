import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the geneweb-python package can be imported when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geneweb_python.app.check import check_database, CheckIssue

try:
    from core.database import Database
    from core.models import CDate, Ascend
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Tests must run from repo root where core.database is importable") from exc


class TestCheck(unittest.TestCase):
    def test_check_finds_orphan_persons(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)
            db.add_person(first_name="Orphan", surname="Test", sex="M")

            issues = check_database(db)
            orphans = [i for i in issues if i.category == "orphan"]
            self.assertEqual(len(orphans), 1)
            self.assertIn("Orphan Test", orphans[0].message)

    def test_check_finds_death_before_birth(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)
            db.add_person(
                first_name="Invalid",
                surname="Dates",
                sex="M",
                birth=CDate(year=2000),
                death=CDate(year=1990),
            )

            issues = check_database(db)
            date_issues = [i for i in issues if i.category == "date"]
            self.assertEqual(len(date_issues), 1)
            self.assertIn("died before birth", date_issues[0].message)

    def test_check_finds_duplicate_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)
            db.add_person(first_name="John", surname="Doe", sex="M")
            db.add_person(first_name="John", surname="Doe", sex="M")

            issues = check_database(db)
            dup_issues = [i for i in issues if i.category == "duplicate"]
            self.assertEqual(len(dup_issues), 1)
            self.assertIn("Duplicate name", dup_issues[0].message)


if __name__ == "__main__":
    unittest.main()
