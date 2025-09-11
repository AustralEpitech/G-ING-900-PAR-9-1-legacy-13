import argparse
from core.database import Database
from core.models import (
    CDate, Title, Relation, PersonalEvent, FamilyEvent, Ascend, Union, Descend, Couple, Person, Family
)

def parse_cdate(s):
    if not s:
        return None
    try:
        parts = s.split("-")
        if len(parts) == 3:
            y, m, d = map(int, parts)
            return CDate(year=y, month=m, day=d)
        elif len(parts) == 1:
            y = int(parts[0])
            return CDate(year=y)
    except Exception:
        print("Format de date invalide (attendu: YYYY-MM-DD ou YYYY)")
    return None

def add_person(database: Database, args):
    birth = parse_cdate(args.birth)
    death = parse_cdate(args.death)
    baptism = parse_cdate(args.baptism)
    person_id = database.add_person(
        first_name=args.first_name,
        surname=args.surname,
        occ=args.occ,
        image=args.image,
        public_name=args.public_name,
        qualifiers=args.qualifiers or [],
        aliases=args.aliases or [],
        first_names_aliases=args.first_names_aliases or [],
        surnames_aliases=args.surnames_aliases or [],
        titles=[],  # Ajout via add_title
        rparents=[],  # Ajout via add_relation
        related=[],  # Ajout via add_related
        occupation=args.occupation,
        sex=args.sex,
        access=args.access,
        birth=birth,
        birth_place=args.birth_place,
        birth_note=args.birth_note,
        birth_src=args.birth_src,
        baptism=baptism,
        baptism_place=args.baptism_place,
        baptism_note=args.baptism_note,
        baptism_src=args.baptism_src,
        death=death,
        death_place=args.death_place,
        death_note=args.death_note,
        death_src=args.death_src,
        burial=args.burial,
        burial_place=args.burial_place,
        burial_note=args.burial_note,
        burial_src=args.burial_src,
        pevents=[],  # Ajout via add_personal_event
        notes=args.notes,
        psources=args.psources,
        key_index=args.key_index,
        ascend=None,  # Ajout via add_ascend
        unions=[],  # Ajout via add_union
        families_as_parent=[],  # Ajout via add_family_as_parent
    )
    print(f"Person added with ID: {person_id}")

def add_family(database: Database, args):
    marriage = parse_cdate(args.marriage)
    family_id = database.add_family(
        marriage=marriage,
        marriage_place=args.marriage_place,
        marriage_note=args.marriage_note,
        marriage_src=args.marriage_src,
        witnesses=[],  # Ajout via add_family_witness
        relation=args.relation,
        divorce=args.divorce,
        fevents=[],  # Ajout via add_family_event
        comment=args.comment,
        origin_file=args.origin_file,
        fsources=args.fsources,
        fam_index=args.fam_index,
    )
    print(f"Family added with ID: {family_id}")

def add_title(database: Database, args):
    person = database.get_person(args.person_id)
    if not person:
        print(f"Person with ID {args.person_id} not found.")
        return
    title_id = database.add_title(
        name=args.name,
        ident=args.ident,
        place=args.place,
        date_start=parse_cdate(args.date_start),
        date_end=parse_cdate(args.date_end),
        nth=args.nth,
    )
    # Ajoute l'objet Title à la personne
    person.titles.append(database.get_title(title_id))
    database.save()
    print(f"Title added to person {args.person_id}")

def add_relation(database: Database, args):
    person = database.get_person(args.person_id)
    if not person:
        print(f"Person with ID {args.person_id} not found.")
        return
    relation_id = database.add_relation(
        r_type=args.r_type,
        father=database.get_person(args.father_id) if args.father_id else None,
        mother=database.get_person(args.mother_id) if args.mother_id else None,
        sources=args.sources,
    )
    person.rparents.append(database.get_relation(relation_id))
    database.save()
    print(f"Relation added to person {args.person_id}")

def add_personal_event(database: Database, args):
    person = database.get_person(args.person_id)
    if not person:
        print(f"Person with ID {args.person_id} not found.")
        return
    pevent_id = database.add_personal_event(
        name=args.name,
        date=parse_cdate(args.date),
        place=args.place,
        reason=args.reason,
        note=args.note,
        src=args.src,
        witnesses=[],
    )
    person.pevents.append(database.get_personal_event(pevent_id))
    database.save()
    print(f"Personal event added to person {args.person_id}")

def add_family_event(database: Database, args):
    family = database.get_family(args.family_id)
    if not family:
        print(f"Family with ID {args.family_id} not found.")
        return
    fevent_id = database.add_family_event(
        name=args.name,
        date=parse_cdate(args.date),
        place=args.place,
        reason=args.reason,
        note=args.note,
        src=args.src,
        witnesses=[],
    )
    family.fevents.append(database.get_family_event(fevent_id))
    database.save()
    print(f"Family event added to family {args.family_id}")

def get_person(database: Database, args):
    person = database.get_person(args.person_id)
    if not person:
        print(f"Person with ID {args.person_id} not found.")
    else:
        print(f"ID: {args.person_id}")
        for attr in vars(person):
            value = getattr(person, attr)
            if attr == "titles":
                print("titles:")
                for t in value:
                    print(f"  - {t.name} ({t.ident})")
            elif attr == "rparents":
                print("relations:")
                for r in value:
                    print(f"  - {r.r_type} (father: {getattr(r.father, 'first_name', None)}, mother: {getattr(r.mother, 'first_name', None)})")
            elif attr == "pevents":
                print("personal events:")
                for e in value:
                    print(f"  - {e.name} ({e.date})")
            else:
                print(f"{attr}: {value}")

def get_family(database: Database, args):
    family = database.get_family(args.family_id)
    if not family:
        print(f"Family with ID {args.family_id} not found.")
    else:
        print(f"ID: {args.family_id}")
        for attr in vars(family):
            value = getattr(family, attr)
            if attr == "fevents":
                print("family events:")
                for e in value:
                    print(f"  - {e.name} ({e.date})")
            elif attr == "witnesses":
                print("witnesses:")
                for w in value:
                    print(f"  - {getattr(w, 'first_name', w)}")
            elif attr == "children":
                print("children:")
                for c in value:
                    print(f"  - {getattr(c, 'first_name', c)}")
            else:
                print(f"{attr}: {value}")

def add_ascend(database: Database, args):
    if not args.person_id:
        print("You must provide a person_id to attach the Ascend.")
        return
    ascend_id = database.add_ascend(
        parents_id=args.parents_id,
        person_id=args.person_id,
        consang=args.consang
    )
    person = database.get_person(args.person_id)
    if person:
        person.ascend = database.get_ascend(ascend_id)
        database.save()
    print(f"Ascend added and attached to person {args.person_id} (Ascend ID: {ascend_id})")

def add_descend(database: Database, args):
    if not args.family_id:
        print("You must provide a family_id to attach the Descend.")
        return
    descend_id = database.add_descend(
        children_ids=args.children_ids,
        family_id=args.family_id
    )
    family = database.get_family(args.family_id)
    if family:
        if not hasattr(family, "descends") or family.descends is None:
            family.descends = []
        family.descends.append(database.get_descend(descend_id))
        database.save()
    print(f"Descend added and attached to family {args.family_id} (Descend ID: {descend_id})")

def add_couple(database: Database, args):
    if not args.husband_id or not args.wife_id:
        print("You must provide both husband_id and wife_id to create a Couple.")
        return
    husband = database.get_person(args.husband_id)
    wife = database.get_person(args.wife_id)
    if not husband or not wife:
        print("Invalid husband_id or wife_id.")
        return
    couple_id = database.add_couple(husband=husband, wife=wife)
    # Optionally, you can link the couple to the persons here if your model supports it
    database.save()
    print(f"Couple added between person {args.husband_id} and {args.wife_id} (Couple ID: {couple_id})")

def add_union(database: Database, args):
    if not args.family_ids or len(args.family_ids) < 1:
        print("You must provide at least one family_id to create a Union.")
        return
    families = [database.get_family(fid) for fid in args.family_ids]
    if any(f is None for f in families):
        print("One or more family_ids are invalid.")
        return
    union_id = database.add_union(family_ids=args.family_ids)
    # Optionally, you can link the union to the families here if your model supports it
    database.save()
    print(f"Union added for families {args.family_ids} (Union ID: {union_id})")

def delete_person(database: Database, args):
    if database.delete_person(args.person_id):
        print(f"Person {args.person_id} deleted.")
    else:
        print(f"Person {args.person_id} not found.")

def delete_family(database: Database, args):
    if database.delete_family(args.family_id):
        print(f"Family {args.family_id} deleted.")
    else:
        print(f"Family {args.family_id} not found.")

def main():
    parser = argparse.ArgumentParser(description="GeneWeb Proof of Concept CLI")
    parser.add_argument(
        "--db-file",
        default="database.pkl",
        help="Path to the database file (default: database.pkl)",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")


def main():
    parser = argparse.ArgumentParser(description="GeneWeb Proof of Concept CLI")
    parser.add_argument(
        "--db-file",
        default="database.pkl",
        help="Path to the database file (default: database.pkl)",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Add person
    parser_add_person = subparsers.add_parser("add_person", help="Add a new person")
    parser_add_person.add_argument("--first_name", required=True)
    parser_add_person.add_argument("--surname", required=True)
    parser_add_person.add_argument("--occ", type=int, default=0)
    parser_add_person.add_argument("--image", default="")
    parser_add_person.add_argument("--public_name", default="")
    parser_add_person.add_argument("--qualifiers", nargs="*", default=[])
    parser_add_person.add_argument("--aliases", nargs="*", default=[])
    parser_add_person.add_argument("--first_names_aliases", nargs="*", default=[])
    parser_add_person.add_argument("--surnames_aliases", nargs="*", default=[])
    parser_add_person.add_argument("--occupation", default="")
    parser_add_person.add_argument("--sex", default="")
    parser_add_person.add_argument("--access", default="")
    parser_add_person.add_argument("--birth", default=None)
    parser_add_person.add_argument("--birth_place", default="")
    parser_add_person.add_argument("--birth_note", default="")
    parser_add_person.add_argument("--birth_src", default="")
    parser_add_person.add_argument("--baptism", default=None)
    parser_add_person.add_argument("--baptism_place", default="")
    parser_add_person.add_argument("--baptism_note", default="")
    parser_add_person.add_argument("--baptism_src", default="")
    parser_add_person.add_argument("--death", default=None)
    parser_add_person.add_argument("--death_place", default="")
    parser_add_person.add_argument("--death_note", default="")
    parser_add_person.add_argument("--death_src", default="")
    parser_add_person.add_argument("--burial", default=None)
    parser_add_person.add_argument("--burial_place", default="")
    parser_add_person.add_argument("--burial_note", default="")
    parser_add_person.add_argument("--burial_src", default="")
    parser_add_person.add_argument("--notes", default="")
    parser_add_person.add_argument("--psources", default="")
    parser_add_person.add_argument("--key_index", type=int, default=None)
    parser_add_person.set_defaults(func=add_person)

    # Add family
    parser_add_family = subparsers.add_parser("add_family", help="Add a new family")
    parser_add_family.add_argument("--marriage", default=None)
    parser_add_family.add_argument("--marriage_place", default="")
    parser_add_family.add_argument("--marriage_note", default="")
    parser_add_family.add_argument("--marriage_src", default="")
    parser_add_family.add_argument("--relation", default="")
    parser_add_family.add_argument("--divorce", default=None)
    parser_add_family.add_argument("--comment", default="")
    parser_add_family.add_argument("--origin_file", default="")
    parser_add_family.add_argument("--fsources", default="")
    parser_add_family.add_argument("--fam_index", type=int, default=None)
    parser_add_family.set_defaults(func=add_family)

    # Add title to person
    parser_add_title = subparsers.add_parser("add_title", help="Add a title to a person")
    parser_add_title.add_argument("--person_id", type=int, required=True)
    parser_add_title.add_argument("--name", required=True)
    parser_add_title.add_argument("--ident", required=True)
    parser_add_title.add_argument("--place", default="")
    parser_add_title.add_argument("--date_start", default=None)
    parser_add_title.add_argument("--date_end", default=None)
    parser_add_title.add_argument("--nth", type=int, default=0)
    parser_add_title.set_defaults(func=add_title)

    # Add relation to person
    parser_add_relation = subparsers.add_parser("add_relation", help="Add a relation to a person")
    parser_add_relation.add_argument("--person_id", type=int, required=True)
    parser_add_relation.add_argument("--r_type", required=True)
    parser_add_relation.add_argument("--father_id", type=int, default=None)
    parser_add_relation.add_argument("--mother_id", type=int, default=None)
    parser_add_relation.add_argument("--sources", default="")
    parser_add_relation.set_defaults(func=add_relation)

    # Add personal event to person
    parser_add_pevent = subparsers.add_parser("add_personal_event", help="Add a personal event to a person")
    parser_add_pevent.add_argument("--person_id", type=int, required=True)
    parser_add_pevent.add_argument("--name", required=True)
    parser_add_pevent.add_argument("--date", default=None)
    parser_add_pevent.add_argument("--place", default="")
    parser_add_pevent.add_argument("--reason", default="")
    parser_add_pevent.add_argument("--note", default="")
    parser_add_pevent.add_argument("--src", default="")
    parser_add_pevent.set_defaults(func=add_personal_event)

    # Add family event to family
    parser_add_fevent = subparsers.add_parser("add_family_event", help="Add a family event to a family")
    parser_add_fevent.add_argument("--family_id", type=int, required=True)
    parser_add_fevent.add_argument("--name", required=True)
    parser_add_fevent.add_argument("--date", default=None)
    parser_add_fevent.add_argument("--place", default="")
    parser_add_fevent.add_argument("--reason", default="")
    parser_add_fevent.add_argument("--note", default="")
    parser_add_fevent.add_argument("--src", default="")
    parser_add_fevent.set_defaults(func=add_family_event)

    # List persons
    parser_list_persons = subparsers.add_parser("list_persons", help="List all persons")
    parser_list_persons.set_defaults(func=lambda db, args: [
        print(f"ID: {pid}, Name: {p.first_name} {p.surname}") for pid, p in db.persons.items()
    ] if db.persons else print("No persons found."))

    # List families
    parser_list_families = subparsers.add_parser("list_families", help="List all families")
    parser_list_families.set_defaults(func=lambda db, args: [
        print(f"ID: {fid}, Marriage: {f.marriage}, Place: {f.marriage_place}") for fid, f in db.families.items()
    ] if db.families else print("No families found."))

    # Get person by ID
    parser_get_person = subparsers.add_parser("get_person", help="Get a person by ID")
    parser_get_person.add_argument("--person_id", type=int, required=True)
    parser_get_person.set_defaults(func=get_person)

    # Get family by ID
    parser_get_family = subparsers.add_parser("get_family", help="Get a family by ID")
    parser_get_family.add_argument("--family_id", type=int, required=True)
    parser_get_family.set_defaults(func=get_family)

    # Add Ascend
    parser_add_ascend = subparsers.add_parser("add_ascend", help="Add an Ascend object")
    parser_add_ascend.add_argument("--parents_id", type=int, default=None, help="Family ID of the parents")
    parser_add_ascend.add_argument("--person_id", type=int, default=None, help="Person ID to link the ascend to")
    parser_add_ascend.add_argument("--consang", type=float, default=None, help="Consanguinity coefficient")
    parser_add_ascend.set_defaults(func=add_ascend)

    # Add Union
    parser_add_union = subparsers.add_parser("add_union", help="Add a Union object")
    parser_add_union.add_argument("--family_ids", type=int, nargs="*", default=[], help="List of family IDs")
    parser_add_union.set_defaults(func=add_union)

    # Add Descend
    parser_add_descend = subparsers.add_parser("add_descend", help="Add a Descend object")
    parser_add_descend.add_argument("--children_ids", type=int, nargs="*", default=[], help="List of children person IDs")
    parser_add_descend.add_argument("--family_id", type=int, default=None, help="Family ID to link children to")
    parser_add_descend.set_defaults(func=add_descend)

    # Add Couple
    parser_add_couple = subparsers.add_parser("add_couple", help="Add a Couple object")
    parser_add_couple.add_argument("--husband_id", type=int, default=None, help="Person ID of husband")
    parser_add_couple.add_argument("--wife_id", type=int, default=None, help="Person ID of wife")
    parser_add_couple.set_defaults(func=add_couple)

    # Delete person
    parser_delete_person = subparsers.add_parser("delete_person", help="Delete a person by ID")
    parser_delete_person.add_argument("--person_id", type=int, required=True)
    parser_delete_person.set_defaults(func=delete_person)

    # Delete family
    parser_delete_family = subparsers.add_parser("delete_family", help="Delete a family by ID")
    parser_delete_family.add_argument("--family_id", type=int, required=True)
    parser_delete_family.set_defaults(func=delete_family)

    args = parser.parse_args()
    database = Database(storage_file=args.db_file)
    if args.command:
        args.func(database, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()