import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the geneweb-python package can be imported when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geneweb_python.app.ged2gwb import import_gedcom
from geneweb_python.app.gwb2ged import export_gedcom_to_string

try:
    from core.database import Database
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Tests must run from repo root where core.database is importable") from exc


class TestGED2GWB(unittest.TestCase):
    def test_import_simple_gedcom_with_one_person(self):
        gedcom_content = """\
0 HEAD
1 GEDC
2 VERS 5.5
0 @I1@ INDI
1 NAME Alice /Smith/
1 SEX F
1 BIRT
2 DATE 1990
2 PLAC Paris
0 TRLR
"""
        with tempfile.TemporaryDirectory() as tmp:
            ged_path = os.path.join(tmp, "test.ged")
            with open(ged_path, "w", encoding="utf-8") as f:
                f.write(gedcom_content)

            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)
            import_gedcom(ged_path, db)

            persons = list(db.persons.values())
            self.assertEqual(len(persons), 1)
            self.assertEqual(persons[0].first_name, "Alice")
            self.assertEqual(persons[0].surname, "Smith")
            self.assertEqual(persons[0].sex, "F")
            self.assertIsNotNone(persons[0].birth)
            self.assertEqual(persons[0].birth.year, 1990)
            self.assertEqual(persons[0].birth_place, "Paris")

    def test_roundtrip_export_then_import(self):
        """Export a DB to GEDCOM, then import it back and verify data."""
        from core.models import CDate, Ascend

        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)

            # Create a family with two parents and a child
            pid1 = db.add_person(first_name="Bob", surname="Jones", sex="M")
            pid2 = db.add_person(first_name="Carol", surname="White", sex="F")
            pid3 = db.add_person(first_name="Dave", surname="Jones", sex="M")
            fid = db.add_family(marriage=CDate(year=2005), marriage_place="NYC")

            p1 = db.get_person(pid1)
            p2 = db.get_person(pid2)
            c = db.get_person(pid3)
            fam = db.get_family(fid)
            p1.families_as_parent.append(fam)
            p2.families_as_parent.append(fam)
            fam.children.append(c)
            c.ascend = Ascend(parents=fam)
            db.save()

            # Export to GEDCOM
            ged_path = os.path.join(tmp, "export.ged")
            with open(ged_path, "w", encoding="utf-8") as f:
                from geneweb_python.app.gwb2ged import export_gedcom
                export_gedcom(db, f)

            # Import into a new DB
            db2_path = os.path.join(tmp, "db2.pkl")
            db2 = Database(storage_file=db2_path)
            import_gedcom(ged_path, db2)

            # Verify imported data
            self.assertEqual(len(db2.persons), 3)
            self.assertEqual(len(db2.families), 1)

            # Check persons
            persons = list(db2.persons.values())
            names = {(p.first_name, p.surname) for p in persons}
            self.assertIn(("Bob", "Jones"), names)
            self.assertIn(("Carol", "White"), names)
            self.assertIn(("Dave", "Jones"), names)

            # Check family
            fam2 = list(db2.families.values())[0]
            self.assertIsNotNone(fam2.marriage)
            self.assertEqual(fam2.marriage.year, 2005)
            self.assertEqual(fam2.marriage_place, "NYC")
            self.assertEqual(len(fam2.children), 1)


if __name__ == "__main__":
    unittest.main()
