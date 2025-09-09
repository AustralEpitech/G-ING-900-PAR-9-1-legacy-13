from typing import Dict, List, Optional
from .models import Person, Family


class Database:
    """
    A simple in-memory database for managing genealogical data.
    """

    def __init__(self):
        self.persons: Dict[int, Person] = {}  # Maps person IDs to Person objects
        self.families: Dict[int, Family] = {}  # Maps family IDs to Family objects
        self.next_person_id: int = 1  # Auto-incrementing ID for persons
        self.next_family_id: int = 1  # Auto-incrementing ID for families

    def add_person(
        self,
        first_name: str,
        last_name: str,
        birth_date: Optional[str] = None,
        death_date: Optional[str] = None,
    ) -> int:
        """
        Adds a new person to the database.

        :param first_name: The first name of the person.
        :param last_name: The last name of the person.
        :param birth_date: The birth date of the person (optional).
        :param death_date: The death date of the person (optional).
        :return: The ID of the newly added person.
        """
        person = Person(first_name, last_name, birth_date, death_date)
        person_id = self.next_person_id
        self.persons[person_id] = person
        self.next_person_id += 1
        return person_id

    def get_person(self, person_id: int) -> Optional[Person]:
        """
        Retrieves a person by their ID.

        :param person_id: The ID of the person.
        :return: The Person object if found, otherwise None.
        """
        return self.persons.get(person_id)

    def list_persons(self) -> List[Person]:
        """
        Lists all persons in the database.

        :return: A list of all Person objects.
        """
        return list(self.persons.values())

    def add_family(self, husband_id: Optional[int], wife_id: Optional[int]) -> int:
        """
        Adds a new family to the database.

        :param husband_id: The ID of the husband (optional).
        :param wife_id: The ID of the wife (optional).
        :return: The ID of the newly added family.
        """
        husband = self.get_person(husband_id) if husband_id else None
        wife = self.get_person(wife_id) if wife_id else None
        family = Family(husband, wife)
        family_id = self.next_family_id
        self.families[family_id] = family
        self.next_family_id += 1

        # Update relationships
        if husband:
            husband.children.extend(family.children)
        if wife:
            wife.children.extend(family.children)

        return family_id

    def get_family(self, family_id: int) -> Optional[Family]:
        """
        Retrieves a family by their ID.

        :param family_id: The ID of the family.
        :return: The Family object if found, otherwise None.
        """
        return self.families.get(family_id)

    def list_families(self) -> List[Family]:
        """
        Lists all families in the database.

        :return: A list of all Family objects.
        """
        return list(self.families.values())
