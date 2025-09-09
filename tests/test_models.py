import unittest
from core.models import Person, Family


class TestPerson(unittest.TestCase):
    def test_create_person(self):
        """
        Test creating a person with basic attributes.
        """
        person = Person(first_name="John", last_name="Doe", birth_date="1980-01-01", death_date="2020-01-01")
        self.assertEqual(person.first_name, "John")
        self.assertEqual(person.last_name, "Doe")
        self.assertEqual(person.birth_date, "1980-01-01")
        self.assertEqual(person.death_date, "2020-01-01")
        self.assertEqual(person.parents, [])
        self.assertEqual(person.children, [])

    def test_person_repr(self):
        """
        Test the string representation of a person.
        """
        person = Person(first_name="Jane", last_name="Smith")
        self.assertEqual(repr(person), "Person(Jane Smith)")


class TestFamily(unittest.TestCase):
    def test_create_family(self):
        """
        Test creating a family with a husband, wife, and children.
        """
        husband = Person(first_name="John", last_name="Doe")
        wife = Person(first_name="Jane", last_name="Doe")
        child1 = Person(first_name="Alice", last_name="Doe")
        child2 = Person(first_name="Bob", last_name="Doe")

        family = Family(husband=husband, wife=wife)
        family.children.extend([child1, child2])

        self.assertEqual(family.husband, husband)
        self.assertEqual(family.wife, wife)
        self.assertEqual(family.children, [child1, child2])

    def test_family_repr(self):
        """
        Test the string representation of a family.
        """
        husband = Person(first_name="John", last_name="Doe")
        wife = Person(first_name="Jane", last_name="Doe")
        family = Family(husband=husband, wife=wife)
        self.assertEqual(repr(family), "Family(Husband: John, Wife: Jane)")


if __name__ == "__main__":
    unittest.main()
