import pickle
from typing import Dict, List, Optional, Any
from .models import Person, Family, CDate, Title, Relation, PersonalEvent, FamilyEvent, Ascend, Union, Descend, Couple

class Database:
    """
    A database for managing genealogical data with persistent storage.
    """

    def __init__(self, storage_file: str = "database.pkl"):
        self.storage_file = storage_file
        self.persons: Dict[int, Person] = {}
        self.families: Dict[int, Family] = {}
        self.ascends: Dict[int, Ascend] = {}
        self.unions: Dict[int, Union] = {}
        self.descends: Dict[int, Descend] = {}
        self.couples: Dict[int, Couple] = {}
        self.titles: Dict[int, Title] = {}
        self.relations: Dict[int, Relation] = {}
        self.personal_events: Dict[int, PersonalEvent] = {}
        self.family_events: Dict[int, FamilyEvent] = {}

        self.next_person_id: int = 1
        self.next_family_id: int = 1
        self.next_ascend_id: int = 1
        self.next_union_id: int = 1
        self.next_descend_id: int = 1
        self.next_couple_id: int = 1
        self.next_title_id: int = 1
        self.next_relation_id: int = 1
        self.next_personal_event_id: int = 1
        self.next_family_event_id: int = 1

        self.load()

    # Person CRUD
    def add_person(self, **kwargs) -> int:
        person = Person(**kwargs)
        person_id = self.next_person_id
        self.persons[person_id] = person
        self.next_person_id += 1
        self.save()
        return person_id

    def update_person(self, person_id: int, **kwargs) -> bool:
        person = self.persons.get(person_id)
        if not person:
            return False
        for key, value in kwargs.items():
            if hasattr(person, key):
                setattr(person, key, value)
        self.save()
        return True

    def get_person(self, person_id: int) -> Optional[Person]:
        return self.persons.get(person_id)

    def list_persons(self) -> List[Person]:
        return list(self.persons.values())
    
    def delete_person(self, person_id: int) -> bool:
        person = self.persons.pop(person_id, None)
        if not person:
            return False
        # Remove from couples
        for couple in self.couples.values():
            if couple.husband and getattr(couple.husband, "id", None) == person_id:
                couple.husband = None
            if couple.wife and getattr(couple.wife, "id", None) == person_id:
                couple.wife = None
        # Remove from descends
        for descend in self.descends.values():
            descend.children = [c for c in descend.children if getattr(c, "id", None) != person_id]
        # Remove from relations
        for relation in self.relations.values():
            if relation.father and getattr(relation.father, "id", None) == person_id:
                relation.father = None
            if relation.mother and getattr(relation.mother, "id", None) == person_id:
                relation.mother = None
        # Remove from families (as witness, etc.)
        for family in self.families.values():
            if hasattr(family, "witnesses") and family.witnesses:
                family.witnesses = [w for w in family.witnesses if getattr(w, "id", None) != person_id]
        # Remove from events
        for pevent in self.personal_events.values():
            if hasattr(pevent, "witnesses") and pevent.witnesses:
                pevent.witnesses = [w for w in pevent.witnesses if getattr(w, "id", None) != person_id]
        self.save()
        return True

    # Family CRUD
    def add_family(self, **kwargs) -> int:
        family = Family(**kwargs)
        family_id = self.next_family_id
        self.families[family_id] = family
        self.next_family_id += 1
        self.save()
        return family_id

    def update_family(self, family_id: int, **kwargs) -> bool:
        family = self.families.get(family_id)
        if not family:
            return False
        for key, value in kwargs.items():
            if hasattr(family, key):
                setattr(family, key, value)
        self.save()
        return True

    def get_family(self, family_id: int) -> Optional[Family]:
        return self.families.get(family_id)

    def list_families(self) -> List[Family]:
        return list(self.families.values())
    
    def delete_family(self, family_id: int) -> bool:
        family = self.families.pop(family_id, None)
        if not family:
            return False
        # Remove from ascends
        for ascend in self.ascends.values():
            if ascend.parents and getattr(ascend.parents, "id", None) == family_id:
                ascend.parents = None
        # Remove from unions
        for union in self.unions.values():
            if hasattr(union, "families") and union.families:
                union.families = [f for f in union.families if getattr(f, "id", None) != family_id]
        self.save()
        return True

    # Ascend CRUD
    def add_ascend(self, parents_id: Optional[int] = None, person_id: Optional[int] = None, consang: Optional[float] = None, **kwargs) -> int:
        parents = self.get_family(parents_id) if parents_id else None
        ascend = Ascend(parents=parents, consang=consang)
        ascend_id = self.next_ascend_id
        self.ascends[ascend_id] = ascend
        self.next_ascend_id += 1
        # Automatic cross-link: add ascend to the person if person_id is provided
        if person_id:
            person = self.get_person(person_id)
            if person:
                if not hasattr(person, "ascend") or person.ascend is None:
                    person.ascend = ascend
        self.save()
        return ascend_id

    def get_ascend(self, ascend_id: int) -> Optional[Ascend]:
        return self.ascends.get(ascend_id)

    def list_ascends(self) -> List[Ascend]:
        return list(self.ascends.values())
    
    def delete_ascend(self, ascend_id: int) -> bool:
        return self.ascends.pop(ascend_id, None) is not None

    # Union CRUD
    def add_union(self, family_ids: Optional[list] = None, **kwargs) -> int:
        families = [self.get_family(fid) for fid in (family_ids or [])]
        if any(f is None for f in families):
            raise ValueError("One or more family IDs do not exist.")
        union = Union(families=families)
        union_id = self.next_union_id
        self.unions[union_id] = union
        self.next_union_id += 1
        self.save()
        return union_id

    def get_union(self, union_id: int) -> Optional[Union]:
        return self.unions.get(union_id)

    def list_unions(self) -> List[Union]:
        return list(self.unions.values())
    
    def delete_union(self, union_id: int) -> bool:
        return self.unions.pop(union_id, None) is not None

    # Descend CRUD
    def add_descend(self, children_ids: Optional[list] = None, family_id: Optional[int] = None, **kwargs) -> int:
        children = [self.get_person(pid) for pid in (children_ids or [])]
        if any(c is None for c in children):
            raise ValueError("One or more children IDs do not exist.")
        descend = Descend(children=children)
        descend_id = self.next_descend_id
        self.descends[descend_id] = descend
        self.next_descend_id += 1
        # Automatic cross-link: add children to the family if family_id is provided
        if family_id:
            family = self.get_family(family_id)
            if family:
                if not hasattr(family, "children") or family.children is None:
                    family.children = []
                for child in children:
                    if child not in family.children:
                        family.children.append(child)
        self.save()
        return descend_id

    def get_descend(self, descend_id: int) -> Optional[Descend]:
        return self.descends.get(descend_id)

    def list_descends(self) -> List[Descend]:
        return list(self.descends.values())
    
    def delete_descend(self, descend_id: int) -> bool:
        return self.descends.pop(descend_id, None) is not None

    # Couple CRUD
    def add_couple(self, husband_id: Optional[int] = None, wife_id: Optional[int] = None, **kwargs) -> int:
        husband = self.get_person(husband_id) if husband_id else None
        wife = self.get_person(wife_id) if wife_id else None
        if husband_id and not husband:
            raise ValueError(f"Husband with ID {husband_id} does not exist.")
        if wife_id and not wife:
            raise ValueError(f"Wife with ID {wife_id} does not exist.")
        couple = Couple(husband=husband, wife=wife)
        couple_id = self.next_couple_id
        self.couples[couple_id] = couple
        self.next_couple_id += 1
        self.save()
        return couple_id

    def get_couple(self, couple_id: int) -> Optional[Couple]:
        return self.couples.get(couple_id)

    def list_couples(self) -> List[Couple]:
        return list(self.couples.values())
    
    def delete_couple(self, couple_id: int) -> bool:
        return self.couples.pop(couple_id, None) is not None

    # Title CRUD
    def add_title(self, person_id: Optional[int] = None, **kwargs) -> int:
        title = Title(**kwargs)
        title_id = self.next_title_id
        self.titles[title_id] = title
        self.next_title_id += 1
        if person_id:
            person = self.get_person(person_id)
            if person:
                person.titles.append(title)
        self.save()
        return title_id

    def get_title(self, title_id: int) -> Optional[Title]:
        return self.titles.get(title_id)

    def list_titles(self) -> List[Title]:
        return list(self.titles.values())
    
    def delete_title(self, title_id: int) -> bool:
        # Remove from persons
        title = self.titles.pop(title_id, None)
        if not title:
            return False
        for person in self.persons.values():
            if hasattr(person, "titles") and title in person.titles:
                person.titles.remove(title)
        self.save()
        return True

    # Relation CRUD
    def add_relation(self, person_id: Optional[int] = None, **kwargs) -> int:
        relation = Relation(**kwargs)
        relation_id = self.next_relation_id
        self.relations[relation_id] = relation
        self.next_relation_id += 1
        if person_id:
            person = self.get_person(person_id)
            if person:
                person.rparents.append(relation)
        self.save()
        return relation_id

    def get_relation(self, relation_id: int) -> Optional[Relation]:
        return self.relations.get(relation_id)

    def list_relations(self) -> List[Relation]:
        return list(self.relations.values())
    
    def delete_relation(self, relation_id: int) -> bool:
        # Remove from persons
        relation = self.relations.pop(relation_id, None)
        if not relation:
            return False
        for person in self.persons.values():
            if hasattr(person, "rparents") and relation in person.rparents:
                person.rparents.remove(relation)
        self.save()
        return True

    # PersonalEvent CRUD
    def add_personal_event(self, person_id: Optional[int] = None, **kwargs) -> int:
        pevent = PersonalEvent(**kwargs)
        pevent_id = self.next_personal_event_id
        self.personal_events[pevent_id] = pevent
        self.next_personal_event_id += 1
        if person_id:
            person = self.get_person(person_id)
            if person:
                person.pevents.append(pevent)
        self.save()
        return pevent_id

    def get_personal_event(self, pevent_id: int) -> Optional[PersonalEvent]:
        return self.personal_events.get(pevent_id)

    def list_personal_events(self) -> List[PersonalEvent]:
        return list(self.personal_events.values())
    
    def delete_personal_event(self, pevent_id: int) -> bool:
        # Remove from persons
        pevent = self.personal_events.pop(pevent_id, None)
        if not pevent:
            return False
        for person in self.persons.values():
            if hasattr(person, "pevents") and pevent in person.pevents:
                person.pevents.remove(pevent)
        self.save()
        return True

    # FamilyEvent CRUD
    def add_family_event(self, family_id: Optional[int] = None, **kwargs) -> int:
        fevent = FamilyEvent(**kwargs)
        fevent_id = self.next_family_event_id
        self.family_events[fevent_id] = fevent
        self.next_family_event_id += 1
        if family_id:
            family = self.get_family(family_id)
            if family:
                family.fevents.append(fevent)
        self.save()
        return fevent_id

    def get_family_event(self, fevent_id: int) -> Optional[FamilyEvent]:
        return self.family_events.get(fevent_id)

    def list_family_events(self) -> List[FamilyEvent]:
        return list(self.family_events.values())
    
    def delete_family_event(self, fevent_id: int) -> bool:
        # Remove from families
        fevent = self.family_events.pop(fevent_id, None)
        if not fevent:
            return False
        for family in self.families.values():
            if hasattr(family, "fevents") and fevent in family.fevents:
                family.fevents.remove(fevent)
        self.save()
        return True

    def save(self):
        """
        Save the database to the storage file.
        """
        with open(self.storage_file, "wb") as f:
            pickle.dump(
                {
                    "persons": self.persons,
                    "families": self.families,
                    "ascends": self.ascends,
                    "unions": self.unions,
                    "descends": self.descends,
                    "couples": self.couples,
                    "titles": self.titles,
                    "relations": self.relations,
                    "personal_events": self.personal_events,
                    "family_events": self.family_events,
                    "next_person_id": self.next_person_id,
                    "next_family_id": self.next_family_id,
                    "next_ascend_id": self.next_ascend_id,
                    "next_union_id": self.next_union_id,
                    "next_descend_id": self.next_descend_id,
                    "next_couple_id": self.next_couple_id,
                    "next_title_id": self.next_title_id,
                    "next_relation_id": self.next_relation_id,
                    "next_personal_event_id": self.next_personal_event_id,
                    "next_family_event_id": self.next_family_event_id,
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
                self.persons = data.get("persons", {})
                self.families = data.get("families", {})
                self.ascends = data.get("ascends", {})
                self.unions = data.get("unions", {})
                self.descends = data.get("descends", {})
                self.couples = data.get("couples", {})
                self.titles = data.get("titles", {})
                self.relations = data.get("relations", {})
                self.personal_events = data.get("personal_events", {})
                self.family_events = data.get("family_events", {})
                self.next_person_id = data.get("next_person_id", 1)
                self.next_family_id = data.get("next_family_id", 1)
                self.next_ascend_id = data.get("next_ascend_id", 1)
                self.next_union_id = data.get("next_union_id", 1)
                self.next_descend_id = data.get("next_descend_id", 1)
                self.next_couple_id = data.get("next_couple_id", 1)
                self.next_title_id = data.get("next_title_id", 1)
                self.next_relation_id = data.get("next_relation_id", 1)
                self.next_personal_event_id = data.get("next_personal_event_id", 1)
                self.next_family_event_id = data.get("next_family_event_id", 1)
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty database
            pass