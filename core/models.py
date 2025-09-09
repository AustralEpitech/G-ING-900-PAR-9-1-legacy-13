from typing import List, Optional


class Person:
    """
    Represents an individual in the genealogical database.
    """
    def __init__(
        self,
        first_name: str,
        last_name: str,
        birth_date: Optional[str] = None,
        death_date: Optional[str] = None,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.death_date = death_date
        self.parents: List["Person"] = []
        self.children: List["Person"] = []

    def __repr__(self):
        return f"Person({self.first_name} {self.last_name})"


class Family:
    """
    Represents a family in the genealogical database.
    """
    def __init__(
        self,
        husband: Optional[Person] = None,
        wife: Optional[Person] = None,
    ):
        self.husband = husband
        self.wife = wife
        self.children: List[Person] = []

    def __repr__(self):
        husband_name = self.husband.first_name if self.husband else "Unknown"
        wife_name = self.wife.first_name if self.wife else "Unknown"
        return f"Family(Husband: {husband_name}, Wife: {wife_name})"
