import pickle
from typing import Dict, List, Optional
from .models import Person, Family


class Database:
    """
    A database for managing genealogical data with persistent storage.
    """

    def __init__(self, storage_file: str = "database.pkl"):
        self.storage_file = storage_file
        self.persons: Dict[int, Person] = {}
        self.families: Dict[int, Family] = {}
        self.next_person_id: int = 1
        self.next_family_id: int = 1
        self.load()

    def add_person(
        self,
        first_name: str,
        last_name: str,
        birth_date: Optional[str] = None,
        death_date: Optional[str] = None,
    ) -> int:
        person = Person(first_name, last_name, birth_date, death_date)
        person_id = self.next_person_id
        self.persons[person_id] = person
        self.next_person_id += 1
        self.save()
        return person_id

    def get_person(self, person_id: int) -> Optional[Person]:
        return self.persons.get(person_id)

    def list_persons(self) -> List[Person]:
        return list(self.persons.values())

    def add_family(self, husband_id: Optional[int], wife_id: Optional[int]) -> int:
        husband = self.get_person(husband_id) if husband_id else None
        wife = self.get_person(wife_id) if wife_id else None
        family = Family(husband, wife)
        family_id = self.next_family_id
        self.families[family_id] = family
        self.next_family_id += 1
        self.save()
        return family_id

    def get_family(self, family_id: int) -> Optional[Family]:
        return self.families.get(family_id)

    def list_families(self) -> List[Family]:
        return list(self.families.values())

    def save(self):
        """
        Save the database to the storage file.
        """
        with open(self.storage_file, "wb") as f:
            pickle.dump(
                {
                    "persons": self.persons,
                    "families": self.families,
                    "next_person_id": self.next_person_id,
                    "next_family_id": self.next_family_id,
                },
                f,
            )

    def load(self):
        """
        Load the database from the storage file.
        """
        try:
            with open(self.storage_file, "rb") as f:
                data = pickle.load(f)
                self.persons = data["persons"]
                self.families = data["families"]
                self.next_person_id = data["next_person_id"]
                self.next_family_id = data["next_family_id"]
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty database
            pass
