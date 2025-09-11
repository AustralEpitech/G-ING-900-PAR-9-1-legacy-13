# GeneWeb Python

This is a simplified proof of concept for the GeneWeb project, implemented in Python. It provides basic genealogical data management functionality, including the ability to add persons, create families, and list them via a command-line interface (CLI).

---

## Features

- **Person Management**:
  - Add persons with attributes like first name, last name, birth date, and death date.
  - List all persons in the database.

- **Family Management**:
  - Create families with a husband, wife, and children.
  - List all families in the database.

- **Command-Line Interface**:
  - Interact with the database using simple CLI commands.

---

## Project Structure

```
core/
├── __init__.py          # Core package initialization
├── database.py          # In-memory database logic
├── models.py            # Data models for persons and families
cli/
├── __init__.py          # CLI package initialization
├── main.py              # Command-line interface logic
tests/
├── test_database.py     # Unit tests for database operations
├── test_models.py       # Unit tests for data models
requirements.txt         # Project dependencies
README.md                # Project documentation
LICENSE                  # License file
```

---

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Run the CLI to interact with the database:

### Add a person

```bash
python -m cli.main add_person --first_name Jean --surname Dupont --birth 1980-01-01 --sex M
```

All fields of the `Person` model are available as options (see `python -m cli.main add_person --help`).

### Add a family

```bash
python -m cli.main add_family --marriage 2000-06-15 --marriage_place Paris
```

### Add a title to a person

```bash
python -m cli.main add_title --person_id 1 --name "Baron" --ident "baron" --place "Paris"
```

### Add a relation to a person

```bash
python -m cli.main add_relation --person_id 1 --r_type "biological" --father_id 2 --mother_id 3
```

### Add a child to a family

```bash
python -m cli.main add_personal_event --person_id 1 --name "Baptism" --date 1980-02-01 --place "Paris"
```

### Add an event to a family

```bash
python -m cli.main add_family_event --family_id 1 --name "Divorce" --date 2010-01-01 --place "Lyon"
```

### List all persons

```bash
python -m cli.main list_persons
```

### List all families

```bash
python -m cli.main list_families
```

### Display a person by their ID

```bash
python -m cli.main get_person --person_id 1
```

Show all fields of the person corresponding to the given ID.

### Display a family by its ID

```bash
python -m cli.main get_family --family_id 1
```

Show all fields of the family corresponding to the given ID.

### Add an Ascend to a person

```bash
python -m cli.main add_ascend --person_id 2 --parents_id 1 --consang 0.125
```
This will create an Ascend and attach it to the person with ID 2.

### Add a Descend to a family

```bash
python -m cli.main add_descend --family_id 1 --children_ids 3 4
```
This will create a Descend and attach it to the family with ID 1.

---

For each command, you can see all available options with `--help`, for example:

```bash
python -m cli.main add_person --help
```

---

## Testing

Run the test suite to ensure everything works as expected:

```bash
python -m unittest discover -s tests
```

---

## Future Work

- Add support for a web interface.
- Extend the CLI with more advanced genealogical features.
- Add support for importing/exporting GEDCOM files.
