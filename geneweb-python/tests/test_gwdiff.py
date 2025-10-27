"""
Tests for gwdiff (database comparison) module.
"""
import unittest
import tempfile
import sys
import os
import json

# Ensure core module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import Database
from core.models import CDate, Ascend

# Import functions from gwdiff module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "geneweb_python")))
from geneweb_python.app.gwdiff import compare_databases, export_diff_json


class TestGwdiffIdentical(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db1_path = os.path.join(self.temp_dir.name, "test1.pkl")
        self.db2_path = os.path.join(self.temp_dir.name, "test2.pkl")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_identical_databases(self):
        """Test comparing two identical databases."""
        # Create two identical databases
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add same person to both
        db1.add_person(
            first_name="John",
            surname="Doe",
            sex="M",
            birth=CDate(year=1980),
            ascend=Ascend(),
        )
        db2.add_person(
            first_name="John",
            surname="Doe",
            sex="M",
            birth=CDate(year=1980),
            ascend=Ascend(),
        )

        # Compare
        report = compare_databases(db1, db2)

        # Verify no differences
        self.assertEqual(len(report["persons_added"]), 0)
        self.assertEqual(len(report["persons_removed"]), 0)
        self.assertEqual(len(report["persons_modified"]), 0)
        self.assertEqual(len(report["families_added"]), 0)
        self.assertEqual(len(report["families_removed"]), 0)
        self.assertEqual(len(report["families_modified"]), 0)


class TestGwdiffPersons(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db1_path = os.path.join(self.temp_dir.name, "test1.pkl")
        self.db2_path = os.path.join(self.temp_dir.name, "test2.pkl")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_person_added(self):
        """Test detecting a person added in db2."""
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add person only to db2
        db2.add_person(
            first_name="Jane",
            surname="Smith",
            sex="F",
            ascend=Ascend(),
        )

        # Compare
        report = compare_databases(db1, db2)

        # Verify person was detected as added
        self.assertEqual(len(report["persons_added"]), 1)
        self.assertEqual(len(report["persons_removed"]), 0)
        self.assertIn(1, report["persons_added"])

    def test_person_removed(self):
        """Test detecting a person removed in db2."""
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add person only to db1
        db1.add_person(
            first_name="Bob",
            surname="Johnson",
            sex="M",
            ascend=Ascend(),
        )

        # Compare
        report = compare_databases(db1, db2)

        # Verify person was detected as removed
        self.assertEqual(len(report["persons_added"]), 0)
        self.assertEqual(len(report["persons_removed"]), 1)
        self.assertIn(1, report["persons_removed"])

    def test_person_modified(self):
        """Test detecting a modified person."""
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add same person with different occupation
        db1.add_person(
            first_name="Alice",
            surname="Brown",
            sex="F",
            occupation="Teacher",
            ascend=Ascend(),
        )
        db2.add_person(
            first_name="Alice",
            surname="Brown",
            sex="F",
            occupation="Professor",
            ascend=Ascend(),
        )

        # Compare
        report = compare_databases(db1, db2)

        # Verify modification was detected
        self.assertEqual(len(report["persons_modified"]), 1)
        person_id, changes = report["persons_modified"][0]
        self.assertEqual(person_id, 1)
        self.assertIn("occupation", changes)
        self.assertEqual(changes["occupation"], ("Teacher", "Professor"))


class TestGwdiffFamilies(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db1_path = os.path.join(self.temp_dir.name, "test1.pkl")
        self.db2_path = os.path.join(self.temp_dir.name, "test2.pkl")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_family_added(self):
        """Test detecting a family added in db2."""
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add family only to db2
        db2.add_family(marriage_place="Paris")

        # Compare
        report = compare_databases(db1, db2)

        # Verify family was detected as added
        self.assertEqual(len(report["families_added"]), 1)
        self.assertEqual(len(report["families_removed"]), 0)
        self.assertIn(1, report["families_added"])

    def test_family_modified(self):
        """Test detecting a modified family."""
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add same family with different marriage place
        db1.add_family(marriage_place="Paris")
        db2.add_family(marriage_place="London")

        # Compare
        report = compare_databases(db1, db2)

        # Verify modification was detected
        self.assertEqual(len(report["families_modified"]), 1)
        family_id, changes = report["families_modified"][0]
        self.assertEqual(family_id, 1)
        self.assertIn("marriage_place", changes)
        self.assertEqual(changes["marriage_place"], ("Paris", "London"))


class TestGwdiffJsonExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db1_path = os.path.join(self.temp_dir.name, "test1.pkl")
        self.db2_path = os.path.join(self.temp_dir.name, "test2.pkl")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_json_export(self):
        """Test exporting diff report as JSON."""
        db1 = Database(storage_file=self.db1_path)
        db2 = Database(storage_file=self.db2_path)

        # Add person only to db2
        db2.add_person(
            first_name="Test",
            surname="User",
            sex="M",
            ascend=Ascend(),
        )

        # Compare and export
        report = compare_databases(db1, db2)
        json_file = os.path.join(self.temp_dir.name, "diff.json")
        export_diff_json(report, json_file)

        # Verify JSON file was created
        self.assertTrue(os.path.exists(json_file))

        # Read and verify JSON content
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data["persons_added"]), 1)
        self.assertEqual(data["persons_added"][0], 1)


if __name__ == "__main__":
    unittest.main()
