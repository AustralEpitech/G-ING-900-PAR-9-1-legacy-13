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

1. **Add a person**:
   ```bash
   python -m cli.main add_person --first_name John --last_name Doe --birth_date 1980-01-01
   ```

2. **List all persons**:
   ```bash
   python -m cli.main list_persons
   ```

3. **Add a family**:
   ```bash
   python -m cli.main add_family --husband_id 1 --wife_id 2
   ```

4. **List all families**:
   ```bash
   python -m cli.main list_families
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
