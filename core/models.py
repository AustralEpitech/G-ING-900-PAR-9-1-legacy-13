from typing import List, Optional, Union, Tuple


class CDate:
    def __init__(
        self,
        day: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        calendar: str = "gregorian",  # "gregorian", "julian", etc.
        precision: str = "",          # "about", "before", "after", etc.
        date2: Optional["CDate"] = None,  # Pour les intervalles
        text: Optional[str] = None,       # Pour la date brute si non structurée
    ):
        self.day = day
        self.month = month
        self.year = year
        self.calendar = calendar
        self.precision = precision
        self.date2 = date2
        self.text = text  # Pour stocker la date originale si besoin

    def __repr__(self):
        return (
            f"CDate({self.day}/{self.month}/{self.year}, "
            f"cal={self.calendar}, prec={self.precision})"
        )

class Title:
    def __init__(
        self,
        name: Union[str, None],
        ident: str,
        place: str,
        date_start: Optional[CDate] = None,
        date_end: Optional[CDate] = None,
        nth: int = 0,
    ):
        self.name = name
        self.ident = ident
        self.place = place
        self.date_start = date_start
        self.date_end = date_end
        self.nth = nth


class Relation:
    def __init__(
        self,
        r_type: str,
        father: Optional["Person"] = None,
        mother: Optional["Person"] = None,
        sources: str = "",
    ):
        self.r_type = r_type
        self.father = father
        self.mother = mother
        self.sources = sources


class PersonalEvent:
    def __init__(
        self,
        name: str,
        date: Optional[CDate] = None,
        place: str = "",
        reason: str = "",
        note: str = "",
        src: str = "",
        witnesses: Optional[List[Tuple["Person", str]]] = None,
    ):
        self.name = name
        self.date = date
        self.place = place
        self.reason = reason
        self.note = note
        self.src = src
        self.witnesses = witnesses or []


class FamilyEvent:
    def __init__(
        self,
        name: str,
        date: Optional[CDate] = None,
        place: str = "",
        reason: str = "",
        note: str = "",
        src: str = "",
        witnesses: Optional[List[Tuple["Person", str]]] = None,
    ):
        self.name = name
        self.date = date
        self.place = place
        self.reason = reason
        self.note = note
        self.src = src
        self.witnesses = witnesses or []


class Family:
    def __init__(
        self,
        marriage: Optional[CDate] = None,
        marriage_place: str = "",
        marriage_note: str = "",
        marriage_src: str = "",
        witnesses: Optional[List["Person"]] = None,
        relation: str = "",
        divorce: Optional[str] = None,
        fevents: Optional[List[FamilyEvent]] = None,
        comment: str = "",
        origin_file: str = "",
        fsources: str = "",
        fam_index: Optional[int] = None,
    ):
        self.marriage = marriage
        self.marriage_place = marriage_place
        self.marriage_note = marriage_note
        self.marriage_src = marriage_src
        self.witnesses = witnesses or []
        self.relation = relation
        self.divorce = divorce
        self.fevents = fevents or []
        self.comment = comment
        self.origin_file = origin_file
        self.fsources = fsources
        self.fam_index = fam_index
        self.children: List["Person"] = []  # Linked via Descend


class Ascend:
    def __init__(
        self,
        parents: Optional[Family] = None,
        consang: Optional[float] = None,
    ):
        self.parents = parents
        self.consang = consang


class Union:
    def __init__(self, families: Optional[List[Family]] = None):
        self.families = families or []


class Descend:
    def __init__(self, children: Optional[List["Person"]] = None):
        self.children = children or []


class Couple:
    def __init__(self, husband: Optional["Person"], wife: Optional["Person"]):
        self.husband = husband
        self.wife = wife


class Person:
    def __init__(
        self,
        first_name: str,
        surname: str,
        occ: int = 0,
        image: str = "",
        public_name: str = "",
        qualifiers: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        first_names_aliases: Optional[List[str]] = None,
        surnames_aliases: Optional[List[str]] = None,
        titles: Optional[List[Title]] = None,
        rparents: Optional[List[Relation]] = None,
        related: Optional[List["Person"]] = None,
        occupation: str = "",
        sex: str = "",
        access: str = "",
        birth: Optional[CDate] = None,
        birth_place: str = "",
        birth_note: str = "",
        birth_src: str = "",
        baptism: Optional[CDate] = None,
        baptism_place: str = "",
        baptism_note: str = "",
        baptism_src: str = "",
        death: Optional[str] = None,
        death_place: str = "",
        death_note: str = "",
        death_src: str = "",
        burial: Optional[str] = None,
        burial_place: str = "",
        burial_note: str = "",
        burial_src: str = "",
        pevents: Optional[List[PersonalEvent]] = None,
        notes: str = "",
        psources: str = "",
        key_index: Optional[int] = None,
        ascend: Optional[Ascend] = None,
        unions: Optional[List[Union]] = None,
        families_as_parent: Optional[List[Family]] = None,
    ):
        self.first_name = first_name
        self.surname = surname
        self.occ = occ
        self.image = image
        self.public_name = public_name
        self.qualifiers = qualifiers or []
        self.aliases = aliases or []
        self.first_names_aliases = first_names_aliases or []
        self.surnames_aliases = surnames_aliases or []
        self.titles = titles or []
        self.rparents = rparents or []
        self.related = related or []
        self.occupation = occupation
        self.sex = sex
        self.access = access
        self.birth = birth
        self.birth_place = birth_place
        self.birth_note = birth_note
        self.birth_src = birth_src
        self.baptism = baptism
        self.baptism_place = baptism_place
        self.baptism_note = baptism_note
        self.baptism_src = baptism_src
        self.death = death
        self.death_place = death_place
        self.death_note = death_note
        self.death_src = death_src
        self.burial = burial
        self.burial_place = burial_place
        self.burial_note = burial_note
        self.burial_src = burial_src
        self.pevents = pevents or []
        self.notes = notes
        self.psources = psources
        self.key_index = key_index
        self.ascend = ascend  # Ascend (parents)
        self.unions = unions or []  # List of Union (families as spouse)
        self.families_as_parent = families_as_parent or []  # Families where this person is a parent

    def __repr__(self):
        return f"Person({self.first_name} {self.surname})"