"""gwd: GeneWeb daemon - minimal HTTP server for genealogical data.

Provides REST API endpoints:
  GET /persons       - List all persons
  GET /persons/<id>  - Get a person by ID
  GET /families      - List all families
  GET /families/<id> - Get a family by ID
"""
from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import urlparse

try:
    from core.database import Database
    from core.models import CDate
except Exception as exc:  # pragma: no cover
    raise RuntimeError("core modules not found. Run from repo root.") from exc


def _serialize_cdate(cdate: Optional[CDate]) -> Optional[Dict[str, Any]]:
    """Serialize a CDate to a JSON-friendly dict."""
    if cdate is None:
        return None
    return {
        "year": cdate.year,
        "month": cdate.month,
        "day": cdate.day,
        "calendar": getattr(cdate, "calendar", "gregorian"),
        "precision": getattr(cdate, "precision", ""),
    }


def _serialize_person(person, pid: int) -> Dict[str, Any]:
    """Serialize a Person to a JSON-friendly dict."""
    return {
        "id": pid,
        "first_name": person.first_name,
        "surname": person.surname,
        "sex": person.sex,
        "birth": _serialize_cdate(person.birth),
        "birth_place": person.birth_place,
        "death": _serialize_cdate(person.death) if hasattr(person.death, "year") else None,
        "death_place": person.death_place,
        "occupation": person.occupation,
        "notes": person.notes,
    }


def _serialize_family(family, fid: int) -> Dict[str, Any]:
    """Serialize a Family to a JSON-friendly dict."""
    return {
        "id": fid,
        "marriage": _serialize_cdate(family.marriage),
        "marriage_place": family.marriage_place,
        "relation": family.relation,
        "comment": family.comment,
    }


class GeneWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler for GeneWeb daemon."""

    db: Database = None  # Set by serve() before starting the server

    def do_GET(self):
        """Handle GET requests."""
        from urllib.parse import parse_qs
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        if path == "/persons":
            self._list_persons(query_params)
        elif path.startswith("/persons/"):
            pid_str = path.split("/")[-1]
            try:
                pid = int(pid_str)
                self._get_person(pid)
            except ValueError:
                self._send_error(400, "Invalid person ID")
        elif path == "/families":
            self._list_families()
        elif path.startswith("/families/"):
            fid_str = path.split("/")[-1]
            try:
                fid = int(fid_str)
                self._get_family(fid)
            except ValueError:
                self._send_error(400, "Invalid family ID")
        elif path == "/search":
            self._search_persons(query_params)
        else:
            self._send_error(404, "Not Found")

    def _list_persons(self, query_params=None):
        """List all persons, optionally filtered by query params."""
        persons = []
        for pid, person in self.db.persons.items():
            # Optional filter by surname
            if query_params and "surname" in query_params:
                target = query_params["surname"][0].lower()
                if target not in person.surname.lower():
                    continue
            persons.append(_serialize_person(person, pid))
        self._send_json(persons)

    def _get_person(self, pid: int):
        """Get a single person by ID."""
        person = self.db.get_person(pid)
        if person is None:
            self._send_error(404, "Person not found")
        else:
            self._send_json(_serialize_person(person, pid))

    def _list_families(self):
        """List all families."""
        families = []
        for fid, family in self.db.families.items():
            families.append(_serialize_family(family, fid))
        self._send_json(families)

    def _get_family(self, fid: int):
        """Get a single family by ID."""
        family = self.db.get_family(fid)
        if family is None:
            self._send_error(404, "Family not found")
        else:
            self._send_json(_serialize_family(family, fid))

    def _search_persons(self, query_params):
        """Search persons by name (first_name or surname substring match)."""
        q = query_params.get("q", [""])[0].lower()
        if not q:
            self._send_error(400, "Missing query parameter 'q'")
            return

        results = []
        for pid, person in self.db.persons.items():
            if q in person.first_name.lower() or q in person.surname.lower():
                results.append(_serialize_person(person, pid))
        self._send_json(results)

    def _send_json(self, data: Any):
        """Send a JSON response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _send_error(self, code: int, message: str):
        """Send an error response."""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"{self.address_string()} - {format % args}")


def serve(db: Database, host: str = "127.0.0.1", port: int = 2317):
    """Start the GeneWeb HTTP server."""
    GeneWebHandler.db = db
    server = HTTPServer((host, port), GeneWebHandler)
    print(f"GeneWeb daemon listening on http://{host}:{port}")
    print("Endpoints:")
    print(f"  GET http://{host}:{port}/persons")
    print(f"  GET http://{host}:{port}/persons?surname=<name>")
    print(f"  GET http://{host}:{port}/persons/<id>")
    print(f"  GET http://{host}:{port}/families")
    print(f"  GET http://{host}:{port}/families/<id>")
    print(f"  GET http://{host}:{port}/search?q=<query>")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
