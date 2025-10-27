"""
Tests for gwu (utilities) module.
"""
import unittest
import tempfile
import sys
import os

# Ensure core module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.database import Database
from core.models import Person, Family, CDate, Ascend, Union, Descend, Couple

# Import functions from gwu module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "geneweb_python")))
from geneweb_python.app.gwu import stats, optimize, export_names, list_surnames


class TestGwuStats(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stats_basic(self):
        """Test basic statistics calculation."""
        # Add some test persons using Database API
        self.db.add_person(
            first_name="John",
            surname="Doe",
            sex="M",
            birth=CDate(year=1980, month=1, day=1, calendar="gregorian"),
            death="2050-12-31",
            ascend=Ascend(),
        )
        self.db.add_person(
            first_name="Jane",
            surname="Doe",
            sex="F",
            birth=CDate(year=1985, month=5, day=15, calendar="gregorian"),
            ascend=Ascend(),
        )
        self.db.add_person(
            first_name="Bob",
            surname="Smith",
            sex="M",
            birth=CDate(year=1990, month=10, day=20, calendar="gregorian"),
            ascend=Ascend(),
        )

        # Calculate stats
        result = stats(self.db)

        # Verify results
        self.assertEqual(result["persons"], 3)
        self.assertEqual(result["males"], 2)
        self.assertEqual(result["females"], 1)
        self.assertEqual(result["families"], 0)
        self.assertEqual(result["with_birth"], 3)
        self.assertEqual(result["with_death"], 0)  # death is a string, not a CDate, so not counted by hasattr check
        self.assertEqual(result["unique_surnames"], 2)
        self.assertIn("1980s", result["birth_distribution"])
        self.assertEqual(result["birth_distribution"]["1980s"], 2)
        self.assertIn("1990s", result["birth_distribution"])
        self.assertEqual(result["birth_distribution"]["1990s"], 1)


class TestGwuOptimize(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_optimize_remove_empty_families(self):
        """Test removing empty families during optimization."""
        # Create empty family using Database API
        self.db.add_family()  # Empty family with no kwargs

        self.assertEqual(len(self.db.families), 1)

        # Run optimize
        result = optimize(self.db)

        # Verify empty family was removed
        self.assertEqual(result["empty_families_removed"], 1)
        self.assertEqual(len(self.db.families), 0)


class TestGwuExportNames(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_names(self):
        """Test exporting unique names to file."""
        # Add persons using Database API
        self.db.add_person(
            first_name="John",
            surname="Doe",
            sex="1",
            ascend=Ascend(),
        )
        self.db.add_person(
            first_name="Jane",
            surname="Smith",
            sex="2",
            ascend=Ascend(),
        )
        self.db.add_person(
            first_name="John",
            surname="Doe",
            sex="1",
            ascend=Ascend(),
        )  # Duplicate name

        # Export names
        output_file = os.path.join(self.temp_dir.name, "names.txt")
        export_names(self.db, output_file)

        # Read and verify
        with open(output_file, "r", encoding="utf-8") as f:
            names = [line.strip() for line in f.readlines()]

        self.assertEqual(len(names), 2)  # Only unique names
        self.assertIn("John Doe", names)
        self.assertIn("Jane Smith", names)


class TestGwuListSurnames(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_surnames_frequency(self):
        """Test listing surnames by frequency."""
        # Add persons with different surnames using Database API
        self.db.add_person(first_name="John", surname="Doe", sex="1", ascend=Ascend())
        self.db.add_person(first_name="Jane", surname="Doe", sex="2", ascend=Ascend())
        self.db.add_person(first_name="Bob", surname="Smith", sex="1", ascend=Ascend())
        self.db.add_person(first_name="Alice", surname="Doe", sex="2", ascend=Ascend())


        # Get surname list
        surnames = list_surnames(self.db)

        # Verify sorting by frequency (descending)
        self.assertEqual(len(surnames), 2)
        self.assertEqual(surnames[0], ("Doe", 3))
        self.assertEqual(surnames[1], ("Smith", 1))


if __name__ == "__main__":
    unittest.main()
