"""gwc: GeneWeb interactive console - REPL for database queries.

Provides:
- Interactive REPL with command history
- Commands: find, show, list, search, help, exit
"""
from __future__ import annotations

import sys
from typing import List, Optional

try:
    import readline  # For command history and completion
except ImportError:
    readline = None  # Windows fallback

try:
    from core.database import Database
    from core.models import Person, Family
except Exception as exc:  # pragma: no cover
    raise RuntimeError("core modules not found. Run from repo root.") from exc


class GeneWebConsole:
    """Interactive console for querying GeneWeb database."""
    
    def __init__(self, db: Database):
        self.db = db
        self.commands = {
            "find": self.cmd_find,
            "show": self.cmd_show,
            "list": self.cmd_list,
            "search": self.cmd_search,
            "stats": self.cmd_stats,
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }
        self.running = True
        
        # Setup readline if available
        if readline:
            readline.parse_and_bind("tab: complete")
            readline.set_completer(self.completer)
    
    def completer(self, text: str, state: int):
        """Tab completion for commands."""
        options = [cmd for cmd in self.commands.keys() if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    
    def run(self):
        """Run the interactive REPL."""
        print("\n=== GeneWeb Interactive Console ===")
        print(f"Database: {len(self.db.persons)} persons, {len(self.db.families)} families")
        print("Type 'help' for available commands, 'exit' to quit.\n")
        
        while self.running:
            try:
                line = input("geneweb> ").strip()
                if not line:
                    continue
                
                parts = line.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command in self.commands:
                    self.commands[command](args)
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except EOFError:
                print("\nGoodbye!")
                break
    
    def cmd_find(self, args: str):
        """Find a person by name.
        Usage: find <name>
        """
        if not args:
            print("Usage: find <name>")
            return
        
        search_term = args.lower()
        results = []
        
        for pid, person in self.db.persons.items():
            full_name = f"{person.first_name} {person.surname}".lower()
            if search_term in full_name:
                results.append((pid, person))
        
        if not results:
            print(f"No person found matching '{args}'")
            return
        
        print(f"\nFound {len(results)} person(s):")
        for pid, person in results:
            print(f"  [{pid}] {person.first_name} {person.surname} ({person.sex or '?'})")
    
    def cmd_show(self, args: str):
        """Show detailed information about a person or family.
        Usage: show person <id> | show family <id>
        """
        if not args:
            print("Usage: show person <id> | show family <id>")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("Usage: show person <id> | show family <id>")
            return
        
        obj_type = parts[0].lower()
        try:
            obj_id = int(parts[1])
        except ValueError:
            print(f"Invalid ID: {parts[1]}")
            return
        
        if obj_type == "person":
            person = self.db.get_person(obj_id)
            if not person:
                print(f"Person #{obj_id} not found")
                return
            
            self._show_person(obj_id, person)
        
        elif obj_type == "family":
            family = self.db.get_family(obj_id)
            if not family:
                print(f"Family #{obj_id} not found")
                return
            
            self._show_family(obj_id, family)
        
        else:
            print(f"Unknown type: {obj_type}. Use 'person' or 'family'.")
    
    def _show_person(self, pid: int, person: Person):
        """Display detailed person information."""
        print(f"\n=== Person #{pid} ===")
        print(f"Name: {person.first_name} {person.surname}")
        print(f"Sex: {person.sex or 'Unknown'}")
        
        if person.birth:
            birth_str = self._format_date(person.birth)
            place_str = f" in {person.birth_place}" if person.birth_place else ""
            print(f"Born: {birth_str}{place_str}")
        
        if person.death:
            death_str = self._format_date(person.death) if hasattr(person.death, "year") else str(person.death)
            place_str = f" in {person.death_place}" if person.death_place else ""
            print(f"Died: {death_str}{place_str}")
        
        if person.occupation:
            print(f"Occupation: {person.occupation}")
        
        if person.notes:
            print(f"Notes: {person.notes}")
    
    def _show_family(self, fid: int, family: Family):
        """Display detailed family information."""
        print(f"\n=== Family #{fid} ===")
        
        if family.marriage:
            marriage_str = self._format_date(family.marriage)
            place_str = f" in {family.marriage_place}" if family.marriage_place else ""
            print(f"Marriage: {marriage_str}{place_str}")
        
        if family.divorce:
            print(f"Divorce: {family.divorce}")
        
        if family.comment:
            print(f"Comment: {family.comment}")
    
    def cmd_list(self, args: str):
        """List persons or families.
        Usage: list persons [limit] | list families [limit]
        """
        if not args:
            print("Usage: list persons [limit] | list families [limit]")
            return
        
        parts = args.split()
        list_type = parts[0].lower()
        limit = int(parts[1]) if len(parts) > 1 else 10
        
        if list_type == "persons":
            persons = list(self.db.persons.items())[:limit]
            print(f"\nPersons (showing {len(persons)} of {len(self.db.persons)}):")
            for pid, person in persons:
                print(f"  [{pid}] {person.first_name} {person.surname} ({person.sex or '?'})")
        
        elif list_type == "families":
            families = list(self.db.families.items())[:limit]
            print(f"\nFamilies (showing {len(families)} of {len(self.db.families)}):")
            for fid, family in families:
                place = family.marriage_place or "Unknown location"
                print(f"  [{fid}] Marriage: {place}")
        
        else:
            print(f"Unknown type: {list_type}. Use 'persons' or 'families'.")
    
    def cmd_search(self, args: str):
        """Full-text search across all persons.
        Usage: search <query>
        """
        if not args:
            print("Usage: search <query>")
            return
        
        query = args.lower()
        results = []
        
        for pid, person in self.db.persons.items():
            searchable = " ".join([
                person.first_name or "",
                person.surname or "",
                person.occupation or "",
                person.birth_place or "",
                person.death_place or "",
                person.notes or "",
            ]).lower()
            
            if query in searchable:
                results.append((pid, person))
        
        if not results:
            print(f"No results found for '{args}'")
            return
        
        print(f"\nFound {len(results)} result(s):")
        for pid, person in results[:20]:  # Limit to 20
            print(f"  [{pid}] {person.first_name} {person.surname}")
    
    def cmd_stats(self, args: str):
        """Show database statistics."""
        males = sum(1 for p in self.db.persons.values() if p.sex and p.sex.upper()[0] == "M")
        females = sum(1 for p in self.db.persons.values() if p.sex and p.sex.upper()[0] == "F")
        
        print(f"\n=== Database Statistics ===")
        print(f"Total persons: {len(self.db.persons)}")
        print(f"  - Males: {males}")
        print(f"  - Females: {females}")
        print(f"  - Unknown: {len(self.db.persons) - males - females}")
        print(f"Total families: {len(self.db.families)}")
    
    def cmd_help(self, args: str):
        """Show available commands."""
        print("\n=== Available Commands ===")
        print("  find <name>              - Find a person by name")
        print("  show person <id>         - Show detailed person information")
        print("  show family <id>         - Show detailed family information")
        print("  list persons [limit]     - List persons (default limit: 10)")
        print("  list families [limit]    - List families (default limit: 10)")
        print("  search <query>           - Full-text search")
        print("  stats                    - Show database statistics")
        print("  help                     - Show this help")
        print("  exit / quit              - Exit console")
    
    def cmd_exit(self, args: str):
        """Exit the console."""
        print("Goodbye!")
        self.running = False
    
    def _format_date(self, date) -> str:
        """Format a date for display."""
        if not date:
            return ""
        
        if hasattr(date, "year"):
            parts = []
            if date.precision:
                parts.append(date.precision)
            if date.day:
                parts.append(f"{date.day:02d}")
            if date.month:
                parts.append(f"{date.month:02d}")
            if date.year:
                parts.append(str(date.year))
            return " ".join(parts) if parts else ""
        
        return str(date)


def run_console(db: Database):
    """Run the interactive console."""
    console = GeneWebConsole(db)
    console.run()
