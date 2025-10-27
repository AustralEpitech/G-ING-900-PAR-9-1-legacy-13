import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the geneweb-python package can be imported when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geneweb_python.app.gwb2ged import export_gedcom_to_string

try:
    from core.database import Database
except Exception as exc:  # pragma: no cover - test should run from repo root
    raise RuntimeError("Tests must run from repo root where core.database is importable") from exc


class TestGWB2GED(unittest.TestCase):
    def test_minimal_export_contains_head_and_trailer(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)

            # Add one person
            pid = db.add_person(first_name="Jean", surname="Dupont", sex="M")
            self.assertIsInstance(pid, int)

            txt = export_gedcom_to_string(db)
            self.assertIn("0 HEAD", txt)
            self.assertIn("0 TRLR", txt)
            self.assertIn("@I1@ INDI", txt)
            self.assertIn("1 NAME Jean /Dupont/", txt)

    def test_family_links_husb_wife_child_and_fams_famc(self):
        from core.models import CDate, Ascend, Family

        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "db.pkl")
            db = Database(storage_file=db_path)

            # Create persons
            pid1 = db.add_person(first_name="Adam", surname="Foo", sex="M")
            pid2 = db.add_person(first_name="Eve", surname="Bar", sex="F")
            pid3 = db.add_person(first_name="Kid", surname="FooBar", sex="M")

            # Create family with marriage
            fid = db.add_family(marriage=CDate(year=2000), marriage_place="Paris")
            fam = db.get_family(fid)

            # Link parents and child
            p1 = db.get_person(pid1)
            p2 = db.get_person(pid2)
            c = db.get_person(pid3)
            p1.families_as_parent.append(fam)
            p2.families_as_parent.append(fam)
            fam.children.append(c)
            c.ascend = Ascend(parents=fam)
            db.save()

            txt = export_gedcom_to_string(db)

            # Family record should reference HUSB, WIFE, CHIL
            self.assertIn(f"0 @F{fid}@ FAM", txt)
            self.assertIn(f"1 HUSB @I{pid1}@", txt)
            self.assertIn(f"1 WIFE @I{pid2}@", txt)
            self.assertIn(f"1 CHIL @I{pid3}@", txt)

            # INDI FAMS/FAMC links
            self.assertIn(f"0 @I{pid1}@ INDI", txt)
            self.assertIn(f"1 FAMS @F{fid}@", txt)
            self.assertIn(f"0 @I{pid2}@ INDI", txt)
            self.assertIn(f"1 FAMS @F{fid}@", txt)
            self.assertIn(f"0 @I{pid3}@ INDI", txt)
            self.assertIn(f"1 FAMC @F{fid}@", txt)


if __name__ == "__main__":
    unittest.main()
