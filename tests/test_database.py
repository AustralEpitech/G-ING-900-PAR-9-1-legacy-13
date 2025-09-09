import unittest
from core.models import Person, Family
from core.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        """
        Set up a fresh database instance for each test.
        """
        self.db = Database()

    def test_add_person(self):
        """
        Test adding a person to the database.
        """
        person_id = self.db.add_person(
            first_name="John", last_name="Doe", birth_date="1980-01-01"
        )
        person = self.db.get_person(person_id)

        self.assertIsNotNone(person)
        self.assertEqual(person.first_name, "John")
        self.assertEqual(person.last_name, "Doe")
        self.assertEqual(person.birth_date, "1980-01-01")
        self.assertIsNone(person.death_date)

    def test_list_persons(self):
        """
        Test listing all persons in the database.
        """
        self.db.add_person(first_name="Alice", last_name="Smith")
        self.db.add_person(first_name="Bob", last_name="Brown")

        persons = self.db.list_persons()
        self.assertEqual(len(persons), 2)
        self.assertEqual(persons[0].first_name, "Alice")
        self.assertEqual(persons[1].first_name, "Bob")

    def test_add_family(self):
        """
        Test adding a family to the database.
        """
        husband_id = self.db.add_person(first_name="John", last_name="Doe")
        wife_id = self.db.add_person(first_name="Jane", last_name="Doe")

        family_id = self.db.add_family(husband_id=husband_id, wife_id=wife_id)
        family = self.db.get_family(family_id)

        self.assertIsNotNone(family)
        self.assertEqual(family.husband.first_name, "John")
        self.assertEqual(family.wife.first_name, "Jane")
        self.assertEqual(len(family.children), 0)

    def test_list_families(self):
        """
        Test listing all families in the database.
        """
        husband_id = self.db.add_person(first_name="John", last_name="Doe")
        wife_id = self.db.add_person(first_name="Jane", last_name="Doe")
        self.db.add_family(husband_id=husband_id, wife_id=wife_id)

        families = self.db.list_families()
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0].husband.first_name, "John")
        self.assertEqual(families[0].wife.first_name, "Jane")

    def test_add_family_with_no_spouse(self):
        """
        Test adding a family with no spouse specified.
        """
        family_id = self.db.add_family(husband_id=None, wife_id=None)
        family = self.db.get_family(family_id)

        self.assertIsNotNone(family)
        self.assertIsNone(family.husband)
        self.assertIsNone(family.wife)
        self.assertEqual(len(family.children), 0)


if __name__ == "__main__":
    unittest.main()
