import argparse
from core import Database


def add_person(database: Database, args):
    person_id = database.add_person(
        first_name=args.first_name,
        last_name=args.last_name,
        birth_date=args.birth_date,
        death_date=args.death_date,
    )
    print(f"Person added with ID: {person_id}")


def list_persons(database: Database, args):
    persons = database.list_persons()
    if not persons:
        print("No persons found.")
    else:
        print("List of persons:")
        for person_id, person in database.persons.items():
            print(f"ID: {person_id}, Name: {person.first_name} {person.last_name}")


def add_family(database: Database, args):
    family_id = database.add_family(husband_id=args.husband_id, wife_id=args.wife_id)
    print(f"Family added with ID: {family_id}")


def list_families(database: Database, args):
    families = database.list_families()
    if not families:
        print("No families found.")
    else:
        print("List of families:")
        for family_id, family in database.families.items():
            husband = family.husband.first_name if family.husband else "Unknown"
            wife = family.wife.first_name if family.wife else "Unknown"
            print(f"ID: {family_id}, Husband: {husband}, Wife: {wife}")


def main():
    parser = argparse.ArgumentParser(description="GeneWeb Proof of Concept CLI")
    parser.add_argument(
        "--db-file",
        default="database.pkl",
        help="Path to the database file (default: database.pkl)",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Add person command
    parser_add_person = subparsers.add_parser("add_person", help="Add a new person")
    parser_add_person.add_argument("--first_name", required=True, help="First name")
    parser_add_person.add_argument("--last_name", required=True, help="Last name")
    parser_add_person.add_argument("--birth_date", help="Birth date (optional)")
    parser_add_person.add_argument("--death_date", help="Death date (optional)")
    parser_add_person.set_defaults(func=add_person)

    # List persons command
    parser_list_persons = subparsers.add_parser("list_persons", help="List all persons")
    parser_list_persons.set_defaults(func=list_persons)

    # Add family command
    parser_add_family = subparsers.add_parser("add_family", help="Add a new family")
    parser_add_family.add_argument("--husband_id", type=int, help="ID of the husband")
    parser_add_family.add_argument("--wife_id", type=int, help="ID of the wife")
    parser_add_family.set_defaults(func=add_family)

    # List families command
    parser_list_families = subparsers.add_parser("list_families", help="List all families")
    parser_list_families.set_defaults(func=list_families)

    # Parse arguments and execute the appropriate function
    args = parser.parse_args()
    database = Database(storage_file=args.db_file)
    if args.command:
        args.func(database, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
