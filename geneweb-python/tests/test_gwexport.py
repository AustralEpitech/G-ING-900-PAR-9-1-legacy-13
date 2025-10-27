"""
Tests for gwexport (multi-format export) module.
"""
import unittest
import tempfile
import sys
import os
import json
import csv
from pathlib import Path

# Ensure the geneweb-python package can be imported when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geneweb_python.app.gwexport import export_csv, export_json, export_html

try:
    from core.database import Database
    from core.models import CDate, Ascend
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Tests must run from repo root where core.database is importable") from exc


class TestGwexportCSV(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_csv_creates_files(self):
        """Test that CSV export creates persons.csv and families.csv."""
        # Add test data
        self.db.add_person(
            first_name="Alice",
            surname="Smith",
            sex="F",
            birth=CDate(year=1990),
            occupation="Engineer",
            ascend=Ascend(),
        )
        self.db.add_family(marriage_place="Paris")

        # Export
        output_dir = self.temp_dir.name
        export_csv(self.db, output_dir)

        # Verify files exist
        persons_file = Path(output_dir) / "persons.csv"
        families_file = Path(output_dir) / "families.csv"
        self.assertTrue(persons_file.exists())
        self.assertTrue(families_file.exists())

        # Verify persons.csv content
        with open(persons_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["First Name"], "Alice")
            self.assertEqual(rows[0]["Surname"], "Smith")
            self.assertEqual(rows[0]["Sex"], "F")
            self.assertEqual(rows[0]["Occupation"], "Engineer")

        # Verify families.csv content
        with open(families_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Marriage Place"], "Paris")


class TestGwexportJSON(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_json_creates_file(self):
        """Test that JSON export creates a valid JSON file."""
        # Add test data
        self.db.add_person(
            first_name="Bob",
            surname="Johnson",
            sex="M",
            birth=CDate(year=1985, month=6, day=15),
            birth_place="London",
            ascend=Ascend(),
        )
        self.db.add_family(
            marriage_place="New York",
            marriage=CDate(year=2010, month=7, day=20),
        )

        # Export
        output_file = os.path.join(self.temp_dir.name, "test.json")
        export_json(self.db, output_file)

        # Verify file exists
        self.assertTrue(os.path.exists(output_file))

        # Verify JSON structure
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("persons", data)
        self.assertIn("families", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["total_persons"], 1)
        self.assertEqual(data["metadata"]["total_families"], 1)

        # Verify person data
        person = data["persons"]["1"]
        self.assertEqual(person["first_name"], "Bob")
        self.assertEqual(person["surname"], "Johnson")
        self.assertEqual(person["sex"], "M")
        self.assertEqual(person["birth"]["place"], "London")

        # Verify family data
        family = data["families"]["1"]
        self.assertEqual(family["marriage"]["place"], "New York")


class TestGwexportHTML(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_html_creates_file(self):
        """Test that HTML export creates a valid HTML file."""
        # Add test data
        self.db.add_person(
            first_name="Charlie",
            surname="Brown",
            sex="M",
            birth=CDate(year=1975),
            birth_place="Boston",
            occupation="Doctor",
            ascend=Ascend(),
        )

        # Export
        output_file = os.path.join(self.temp_dir.name, "test.html")
        export_html(self.db, output_file)

        # Verify file exists
        self.assertTrue(os.path.exists(output_file))

        # Verify HTML content
        with open(output_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Check for key HTML elements
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("<title>GeneWeb Family Tree</title>", html_content)
        self.assertIn("Charlie Brown", html_content)
        self.assertIn("Boston", html_content)
        self.assertIn("Doctor", html_content)
        self.assertIn("Total Persons:", html_content)


class TestGwexportEmptyDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.pkl")
        self.db = Database(storage_file=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_empty_database(self):
        """Test exporting an empty database."""
        # Export CSV
        output_dir = self.temp_dir.name
        export_csv(self.db, output_dir)

        persons_file = Path(output_dir) / "persons.csv"
        self.assertTrue(persons_file.exists())

        # Verify CSV has header but no data rows
        with open(persons_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)  # Only header

        # Export JSON
        json_file = os.path.join(self.temp_dir.name, "empty.json")
        export_json(self.db, json_file)

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["total_persons"], 0)
        self.assertEqual(data["metadata"]["total_families"], 0)

        # Export HTML
        html_file = os.path.join(self.temp_dir.name, "empty.html")
        export_html(self.db, html_file)

        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.assertIn("No persons in database", html_content)
        self.assertIn("No families in database", html_content)


if __name__ == "__main__":
    unittest.main()
