from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import storage as storage_mod
from ..models import Person, Family, CDate, Place, PersEvent
from typing import List, Optional, Dict, Any
from ..models import Note
import logging
from ..plugins import load_plugins
from ..config import load_config

app = FastAPI(title="geneweb-py")

# Ensure basic logging is configured so integration-test server logs at INFO are visible
logging.basicConfig(level=logging.INFO)

# Mount a static directory (created on demand)
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = Path("hd") / "etc"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


# Do not create the Storage instance at import time. Creating it on import
# caused accidental writes to the repository-local `data/` directory when the
# module was imported (for example during tests or tooling). Instead, set the
# module-level variable to None and create the Storage instance during the
# FastAPI startup event. Plugins are still discovered and registered at import
# time so tests that inspect routes continue to work; plugin handlers should
# access the real storage at request time via the `storage` global once the
# app has started.
# `storage` is a proxy exported by the storage module. It will forward calls
# to the Storage instance bound to the current request (via ContextVar) or to
# a process-global default storage. We keep the name `storage` here for
# backward-compatibility with existing code.
storage = storage_mod.storage

# StorageManager instance will be created at startup using the configured
# data directory. It manages multiple bases (one Storage per base name).
storage_manager: Optional[storage_mod.StorageManager] = None


# Load plugins now (registers routes and lifecycle hooks). We load config first.
cfg = load_config()
try:
    # Pass the storage proxy through; plugin registration should not perform
    # persistent writes during import. Plugin request handlers may use the
    # real storage at runtime after startup (the proxy will forward calls).
    load_plugins(app, storage, cfg, repo_root=Path("."), templates=templates)
except Exception:
    logging.exception("Failed to load plugins during module import")

# Workaround: some routes (docs/openapi) may have been registered without a response_class
# (for example if a plugin mistakenly registered a route with response_class=None).
# FastAPI's OpenAPI generator expects a response class for these routes, so set them
# explicitly if missing.
for _r in list(app.routes):
    try:
        nm = getattr(_r, "name", None)
        if nm == "openapi" and getattr(_r, "response_class", None) is None:
            _r.response_class = JSONResponse
        if nm in ("swagger_ui_html", "swagger_ui_redirect", "redoc_html") and getattr(_r, "response_class", None) is None:
            _r.response_class = HTMLResponse
    except Exception:
        # be defensive; if any route introspection fails, skip it
        pass


@app.on_event("startup")
def _create_storage_manager_on_startup():
    """Create the StorageManager during startup using the configured data dir.

    The manager allows handling multiple named bases (databases)."""
    global storage_manager
    try:
        storage_manager = storage_mod.StorageManager(cfg.data_dir)
        logging.info("StorageManager initialized at %s", str(cfg.data_dir))
    except Exception:
        logging.exception("Failed to initialize StorageManager on startup")



@app.middleware("http")
async def bind_storage_middleware(request: Request, call_next):
    """Bind a Storage to the current request based on query param `b` or
    cookie `gw_base`. If `b` query param is present we also set a cookie on
    the response so subsequent requests remember the choice (per-client).
    """
    token = None
    base_name = None
    try:
        # prefer explicit query param (for temporary override + choice)
        base_name = request.query_params.get("b") or request.cookies.get("gw_base")
        if base_name and storage_manager is not None:
            try:
                s = storage_manager.get_storage(base_name)
                token = storage_mod.bind_current_storage(s)
            except Exception:
                logging.exception("Failed to bind storage for base %s", base_name)
                token = None
    except Exception:
        logging.exception("Error while determining storage for request")

    # proceed with request handling
    response = await call_next(request)

    # If the base was provided as query param persist it in a cookie
    if request.query_params.get("b"):
        response.set_cookie(key="gw_base", value=request.query_params.get("b"), httponly=False)

    # reset contextvar to previous state
    if token is not None:
        try:
            storage_mod.CURRENT_STORAGE.reset(token)
        except Exception:
            # defensive: ignore reset errors
            pass

    return response



@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    # If the client hasn't chosen a base yet, present a selection page.
    # The middleware will bind a Storage if cookie `gw_base` or query param `b`
    # is present; use storage_mod.get_current_storage() to check.
    current = storage_mod.get_current_storage()
    if current is None:
        # present available bases and a simple form to choose one
        bases = storage_manager.list_bases() if storage_manager is not None else []
        return templates.TemplateResponse("choose_base.html", {"request": request, "bases": bases})
    return templates.TemplateResponse("welcome.html", {"request": request})



@app.post("/select_base")
def select_base(request: Request, base: str = Form(...)):
    """Handle base selection from the HTML form. Redirect using a query
    parameter `b` which the middleware will persist as a cookie and bind the
    per-request storage instance."""
    # redirect to root with ?b=base so middleware binds and response will set cookie
    return RedirectResponse(url=f"/?b={base}", status_code=303)


@app.post("/create_base")
def create_base(request: Request, name: str = Form(...)):
    """Create a new base directory under the configured data dir and redirect
    to root with ?b=<name> so the middleware binds and sets the cookie.
    """
    # basic sanitization: use the final path name component and disallow path separators
    safe_name = Path(name).name
    if not safe_name or safe_name != name:
        # invalid name or attempted traversal
        return templates.TemplateResponse("choose_base.html", {"request": request, "bases": storage_manager.list_bases() if storage_manager else [], "error": "Invalid base name"})
    try:
        # Ensure storage manager exists and create the storage (initializes DB)
        if storage_manager is None:
            raise RuntimeError("StorageManager not initialized")
        storage_manager.get_storage(safe_name)
    except Exception:
        logging.exception("Failed to create base %s", safe_name)
        return templates.TemplateResponse(
            "choose_base.html",
            {"request": request, "bases": storage_manager.list_bases() if storage_manager else [], "error": "Failed to create base"},
        )
    # Redirect to root with ?b= so the middleware will set cookie and bind
    return RedirectResponse(url=f"/?b={safe_name}", status_code=303)


@app.get("/change_db")
def change_db(request: Request):
    """Clear the gw_base cookie for the client and redirect to root where
    the choose-base page will be shown."""
    resp = RedirectResponse(url="/", status_code=303)
    # Delete cookie so subsequent requests won't pick a base
    resp.delete_cookie(key="gw_base")
    return resp


@app.get("/people", response_class=HTMLResponse)
def people_list(request: Request):
    persons = storage.list_persons()
    return templates.TemplateResponse("people_list.html", {"request": request, "persons": persons})


@app.get("/families", response_class=HTMLResponse)
def families_list(request: Request):
    families = list(storage.families.values())
    # Build a display-friendly list of parent family names for each family
    def format_parent_names(names):
        # names: list of surname strings (ordered)
        # keep unique while preserving order
        seen = set()
        out = []
        for n in names:
            if not n:
                continue
            if n not in seen:
                seen.add(n)
                out.append(n)
        if len(out) == 0:
            return "(unknown)"
        if len(out) == 1:
            return out[0]
        if len(out) == 2:
            return f"{out[0]} and {out[1]}"
        # 3+ names: comma separated with 'and' before last
        return ", ".join(out[:-1]) + f" and {out[-1]}"

    families_display = []
    for f in families:
        husband = storage.get_person(f.husband_id) if f.husband_id else None
        wife = storage.get_person(f.wife_id) if f.wife_id else None
        # collect surnames from parents in husband->wife order
        names = []
        if husband:
            names.append(husband.surname or "")
        if wife:
            names.append(wife.surname or "")
        label = format_parent_names(names)
        families_display.append({"id": f.id, "label": label})

    return templates.TemplateResponse("families_list.html", {"request": request, "families": families_display})


@app.get("/person/create", response_class=HTMLResponse)
def create_person_form(request: Request, event_rows: int = 1):
    return templates.TemplateResponse("create_person.html", {"request": request, "event_rows": event_rows})


@app.post("/person/create")
def create_person(
    first_name: str = Form(...),
    surname: str = Form(...),
    sex: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None),
    birth_place: Optional[str] = Form(None),
    birth_note: Optional[str] = Form(None),
    death_date: Optional[str] = Form(None),
    death_place: Optional[str] = Form(None),
    death_note: Optional[str] = Form(None),
    pevent_kind: List[str] = Form([]),
    pevent_date: List[str] = Form([]),
    pevent_place: List[str] = Form([]),
    pevent_note: List[str] = Form([]),
):
    logging.info("create_person called with first_name=%s, surname=%s, sex=%s", first_name, surname, sex)
    p = Person(first_name=first_name, surname=surname, sex=sex)
    # parse optional structured fields from simple textual inputs
    if birth_date:
        p.birth_date = CDate.from_string(birth_date)
    if birth_place:
        p.birth_place = Place.from_simple(birth_place)
    if birth_note:
        p.birth_note = birth_note
    if death_date:
        p.death_date = CDate.from_string(death_date)
    if death_place:
        p.death_place = Place.from_simple(death_place)
    if death_note:
        p.death_note = death_note
    # parse person events from repeated form fields (server-side dynamic rows)
    evs: list[PersEvent] = []
    for i, kind in enumerate(pevent_kind or []):
        if not kind:
            continue
        date = CDate.from_string(pevent_date[i]) if i < len(pevent_date) and pevent_date[i] else None
        place = Place.from_simple(pevent_place[i]) if i < len(pevent_place) and pevent_place[i] else None
        note = pevent_note[i] if i < len(pevent_note) and pevent_note[i] else None
        evs.append(PersEvent(kind=kind, date=date, place=place, note=note))
    p.pevents = evs
    try:
        storage.add_person(p)
        logging.info("Created person %s; persons now: %s", p.id, list(storage.persons.keys()))
    except Exception:
        logging.exception("Failed to add person %s", p.id)
        raise
    logging.info("create_person completed for %s, redirecting to person page", p.id)
    return RedirectResponse(url=f"/person/{p.id}", status_code=303)


@app.get("/person/{pid}/edit", response_class=HTMLResponse)
def edit_person_form(request: Request, pid: str, event_rows: Optional[int] = None):
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")
    # determine how many event rows to render: provided event_rows overrides; otherwise base on existing events
    rows = max(event_rows, len(p.pevents)) if event_rows is not None else len(p.pevents)
    return templates.TemplateResponse("edit_person.html", {"request": request, "person": p, "event_rows": rows})


@app.post("/person/{pid}/edit")
def edit_person(
    pid: str,
    first_name: str = Form(...),
    surname: str = Form(...),
    sex: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None),
    birth_place: Optional[str] = Form(None),
    birth_note: Optional[str] = Form(None),
    death_date: Optional[str] = Form(None),
    death_place: Optional[str] = Form(None),
    death_note: Optional[str] = Form(None),
    pevent_kind: List[str] = Form([]),
    pevent_date: List[str] = Form([]),
    pevent_place: List[str] = Form([]),
    pevent_note: List[str] = Form([]),
    pevent_action: List[str] = Form([]),
):
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")
    p.first_name = first_name
    p.surname = surname
    p.sex = sex
    # parse optional structured fields
    if birth_date is not None:
        p.birth_date = CDate.from_string(birth_date)
    if birth_place is not None:
        p.birth_place = Place.from_simple(birth_place)
    if birth_note is not None:
        p.birth_note = birth_note
    if death_date is not None:
        p.death_date = CDate.from_string(death_date)
    if death_place is not None:
        p.death_place = Place.from_simple(death_place)
    if death_note is not None:
        p.death_note = death_note
    # parse pevents from repeated form fields (replace existing list)
    evs: list[PersEvent] = []
    for i, kind in enumerate(pevent_kind or []):
        action = pevent_action[i] if i < len(pevent_action) else ""
        if action == "remove":
            continue
        if not kind:
            continue
        date = CDate.from_string(pevent_date[i]) if i < len(pevent_date) and pevent_date[i] else None
        place = Place.from_simple(pevent_place[i]) if i < len(pevent_place) and pevent_place[i] else None
        note = pevent_note[i] if i < len(pevent_note) and pevent_note[i] else None
        evs.append(PersEvent(kind=kind, date=date, place=place, note=note))
    p.pevents = evs
    storage.update_person(p)
    return RedirectResponse(url=f"/person/{pid}", status_code=303)


### Minimal JSON API additions: create/update person
@app.post("/api/person", status_code=201)
def api_create_person(data: Dict[str, Any]):
    # Accept JSON payload with simple textual fields for dates and places
    first_name = data.get("first_name", "")
    surname = data.get("surname", "")
    sex = data.get("sex")
    p = Person(first_name=first_name, surname=surname, sex=sex)
    bd = data.get("birth_date")
    if bd:
        p.birth_date = CDate.from_string(bd)
    bp = data.get("birth_place")
    if bp:
        p.birth_place = Place.from_simple(bp)
    if data.get("birth_note"):
        p.birth_note = data.get("birth_note")
    # parse pevents from JSON - accept list of simple textual lines or list of dicts
    if data.get("pevents"):
        pe = []
        for item in data.get("pevents"):
            if isinstance(item, str):
                parts = [x.strip() for x in item.split("|")]
                kind = parts[0] if len(parts) > 0 else ""
                date = CDate.from_string(parts[1]) if len(parts) > 1 and parts[1] else None
                place = Place.from_simple(parts[2]) if len(parts) > 2 and parts[2] else None
                note = parts[3] if len(parts) > 3 and parts[3] else None
                pe.append(PersEvent(kind=kind, date=date, place=place, note=note))
            elif isinstance(item, dict):
                pe.append(PersEvent.from_dict(item))
        p.pevents = pe
    dd = data.get("death_date")
    if dd:
        p.death_date = CDate.from_string(dd)
    dp = data.get("death_place")
    if dp:
        p.death_place = Place.from_simple(dp)
    if data.get("death_note"):
        p.death_note = data.get("death_note")
    storage.add_person(p)
    return p.to_dict()


@app.put("/api/person/{pid}")
def api_update_person(pid: str, data: Dict[str, Any]):
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")
    # update allowed fields
    if "first_name" in data:
        p.first_name = data.get("first_name")
    if "surname" in data:
        p.surname = data.get("surname")
    if "sex" in data:
        p.sex = data.get("sex")
    if "birth_date" in data:
        p.birth_date = CDate.from_string(data.get("birth_date")) if data.get("birth_date") else None
    if "birth_place" in data:
        p.birth_place = Place.from_simple(data.get("birth_place")) if data.get("birth_place") else None
    if "birth_note" in data:
        p.birth_note = data.get("birth_note")
    if "death_date" in data:
        p.death_date = CDate.from_string(data.get("death_date")) if data.get("death_date") else None
    if "death_place" in data:
        p.death_place = Place.from_simple(data.get("death_place")) if data.get("death_place") else None
    if "death_note" in data:
        p.death_note = data.get("death_note")
    # pevents: replace list if provided
    if "pevents" in data:
        if data.get("pevents") is None:
            p.pevents = []
        else:
            pe = []
            for item in data.get("pevents"):
                if isinstance(item, str):
                    parts = [x.strip() for x in item.split("|")]
                    kind = parts[0] if len(parts) > 0 else ""
                    date = CDate.from_string(parts[1]) if len(parts) > 1 and parts[1] else None
                    place = Place.from_simple(parts[2]) if len(parts) > 2 and parts[2] else None
                    note = parts[3] if len(parts) > 3 and parts[3] else None
                    pe.append(PersEvent(kind=kind, date=date, place=place, note=note))
                elif isinstance(item, dict):
                    pe.append(PersEvent.from_dict(item))
            p.pevents = pe
    storage.update_person(p)
    return p.to_dict()


@app.post("/person/{pid}/delete")
def delete_person(pid: str):
    ok = storage.delete_person(pid)
    if not ok:
        raise HTTPException(status_code=404, detail="Person not found")
    return RedirectResponse(url="/", status_code=303)


@app.get("/family/create", response_class=HTMLResponse)
def create_family_form(request: Request, fevent_rows: int = 1):
    persons = storage.list_persons()
    return templates.TemplateResponse("create_family.html", {"request": request, "persons": persons, "fevent_rows": fevent_rows})


@app.post("/family/create")
def create_family(
    husband_id: Optional[str] = Form(None),
    wife_id: Optional[str] = Form(None),
    children_ids: List[str] = Form([]),
    fevent_kind: List[str] = Form([]),
    fevent_date: List[str] = Form([]),
    fevent_place: List[str] = Form([]),
    fevent_note: List[str] = Form([]),
):
    f = Family(husband_id=husband_id or None, wife_id=wife_id or None, children_ids=children_ids)
    if fevent_kind:
        fes: list[PersEvent] = []
        for i, kind in enumerate(fevent_kind or []):
            if not kind:
                continue
            date = CDate.from_string(fevent_date[i]) if i < len(fevent_date) and fevent_date[i] else None
            place = Place.from_simple(fevent_place[i]) if i < len(fevent_place) and fevent_place[i] else None
            note = fevent_note[i] if i < len(fevent_note) and fevent_note[i] else None
            fes.append(PersEvent(kind=kind, date=date, place=place, note=note))
        f.fevents = fes
    storage.add_family(f)
    return RedirectResponse(url=f"/family/{f.id}", status_code=303)


@app.get("/family/{fid}/edit", response_class=HTMLResponse)
def edit_family_form(request: Request, fid: str, fevent_rows: Optional[int] = None):
    f = storage.get_family(fid)
    if f is None:
        raise HTTPException(status_code=404, detail="Family not found")
    persons = storage.list_persons()
    rows = max(fevent_rows, len(f.fevents)) if fevent_rows is not None else len(f.fevents)
    return templates.TemplateResponse("edit_family.html", {"request": request, "family": f, "persons": persons, "fevent_rows": rows})


@app.post("/family/{fid}/edit")
def edit_family(
    fid: str,
    husband_id: Optional[str] = Form(None),
    wife_id: Optional[str] = Form(None),
    children_ids: List[str] = Form([]),
    fevent_kind: List[str] = Form([]),
    fevent_date: List[str] = Form([]),
    fevent_place: List[str] = Form([]),
    fevent_note: List[str] = Form([]),
    fevent_action: List[str] = Form([]),
):
    f = storage.get_family(fid)
    if f is None:
        raise HTTPException(status_code=404, detail="Family not found")
    f.husband_id = husband_id or None
    f.wife_id = wife_id or None
    f.children_ids = children_ids
    # parse fevents if provided (replace existing list)
    fes: list[PersEvent] = []
    for i, kind in enumerate(fevent_kind or []):
        action = fevent_action[i] if i < len(fevent_action) else ""
        if action == "remove":
            continue
        if not kind:
            continue
        date = CDate.from_string(fevent_date[i]) if i < len(fevent_date) and fevent_date[i] else None
        place = Place.from_simple(fevent_place[i]) if i < len(fevent_place) and fevent_place[i] else None
        note = fevent_note[i] if i < len(fevent_note) and fevent_note[i] else None
        fes.append(PersEvent(kind=kind, date=date, place=place, note=note))
    f.fevents = fes
    storage.update_family(f)
    return RedirectResponse(url=f"/family/{fid}", status_code=303)


@app.post("/family/{fid}/delete")
def delete_family(fid: str):
    ok = storage.delete_family(fid)
    if not ok:
        raise HTTPException(status_code=404, detail="Family not found")
    return RedirectResponse(url="/", status_code=303)


@app.get("/person/{pid}", response_class=HTMLResponse)
def person_page(request: Request, pid: str):
    logging.info("person_page requested for %s; persons: %s", pid, list(storage.persons.keys()))
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")
    # collect related persons: spouses, parents, children using the index
    spouses = []
    parents = []
    children = []
    for fam in storage.families_of_person(pid):
        # spouses: if pid is husband, include wife; if pid is wife, include husband
        if fam.husband_id == pid and fam.wife_id:
            wp = storage.get_person(fam.wife_id)
            if wp:
                spouses.append(wp)
        if fam.wife_id == pid and fam.husband_id:
            hp = storage.get_person(fam.husband_id)
            if hp:
                spouses.append(hp)
        # parents: if pid is a child in this family, include parents
        if pid in fam.children_ids:
            if fam.husband_id:
                pp = storage.get_person(fam.husband_id)
                if pp:
                    parents.append(pp)
            if fam.wife_id:
                pp = storage.get_person(fam.wife_id)
                if pp:
                    parents.append(pp)
        # children: if pid is a spouse in this family, include children
        if fam.husband_id == pid or fam.wife_id == pid:
            for cid in fam.children_ids:
                cp = storage.get_person(cid)
                if cp:
                    children.append(cp)

    # unique by id while preserving order
    def unique_persons(lst):
        seen = set()
        out = []
        for x in lst:
            if x.id not in seen:
                seen.add(x.id)
                out.append(x)
        return out

    spouses = unique_persons(spouses)
    parents = unique_persons(parents)
    children = unique_persons(children)

    # families the person belongs to (using index)
    families = list(storage.families_of_person(pid))
    logging.info(
        "Rendering person_page for %s: spouses=%d parents=%d children=%d families=%d",
        pid,
        len(spouses),
        len(parents),
        len(children),
        len(families),
    )
    return templates.TemplateResponse(
        "person.html",
        {
            "request": request,
            "person": p,
            "spouses": spouses,
            "parents": parents,
            "children": children,
            "families": families,
        },
    )


@app.get("/family/{fid}", response_class=HTMLResponse)
def family_page(request: Request, fid: str):
    logging.info("family_page requested for %s; families_count: %d", fid, len(storage.families))
    f = storage.get_family(fid)
    if f is None:
        raise HTTPException(status_code=404, detail="Family not found")
    husband = storage.get_person(f.husband_id) if f.husband_id else None
    wife = storage.get_person(f.wife_id) if f.wife_id else None
    children = [storage.get_person(cid) for cid in f.children_ids]
    return templates.TemplateResponse(
        "family.html",
        {"request": request, "family": f, "husband": husband, "wife": wife, "children": children},
    )


# Notes routes
@app.get("/notes", response_class=HTMLResponse)
def notes_list(request: Request):
    notes = list(storage.list_notes())
    return templates.TemplateResponse("notes_list.html", {"request": request, "notes": notes})


@app.get("/notes/create", response_class=HTMLResponse)
def create_note_form(request: Request):
    return templates.TemplateResponse("edit_note.html", {"request": request, "note": None})


@app.post("/notes/create")
def create_note(nid: str = Form(...), title: str = Form(""), text: str = Form("")):
    # nid is the identifier (path-like, without .txt)
    storage.commit_note(nid, title, text)
    return RedirectResponse(url=f"/notes/{nid}", status_code=303)


@app.get("/notes/{nid}", response_class=HTMLResponse)
def note_view(request: Request, nid: str):
    n = storage.get_note(nid)
    if n is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return templates.TemplateResponse("note_view.html", {"request": request, "note": n})


@app.get("/notes/{nid}/edit", response_class=HTMLResponse)
def edit_note_form(request: Request, nid: str):
    n = storage.get_note(nid)
    if n is None:
        # present create form prefilled with id
        return templates.TemplateResponse("edit_note.html", {"request": request, "note": Note(id=nid, title="", text="")})
    return templates.TemplateResponse("edit_note.html", {"request": request, "note": n})


@app.post("/notes/{nid}/edit")
def edit_note(nid: str, title: str = Form(""), text: str = Form("")):
    storage.commit_note(nid, title, text)
    return RedirectResponse(url=f"/notes/{nid}", status_code=303)


@app.post("/notes/{nid}/delete")
def delete_note(nid: str):
    ok = storage.delete_note(nid)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")
    return RedirectResponse(url="/notes", status_code=303)


### Minimal JSON API (programmatic access)
@app.get("/api/person/{pid}")
def api_person(pid: str):
    """Return JSON representation of a person and immediate relations."""
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")

    spouses = []
    parents = []
    children = []
    families = []

    for fam in storage.families_of_person(pid):
        families.append(fam.to_dict())
        # spouses
        if fam.husband_id == pid and fam.wife_id:
            wp = storage.get_person(fam.wife_id)
            if wp:
                spouses.append(wp.to_dict())
        if fam.wife_id == pid and fam.husband_id:
            hp = storage.get_person(fam.husband_id)
            if hp:
                spouses.append(hp.to_dict())
        # parents
        if pid in fam.children_ids:
            if fam.husband_id:
                pp = storage.get_person(fam.husband_id)
                if pp:
                    parents.append(pp.to_dict())
            if fam.wife_id:
                pp = storage.get_person(fam.wife_id)
                if pp:
                    parents.append(pp.to_dict())
        # children
        if fam.husband_id == pid or fam.wife_id == pid:
            for cid in fam.children_ids:
                cp = storage.get_person(cid)
                if cp:
                    children.append(cp.to_dict())

    # deduplicate by id
    def uniq_by_id(objs):
        seen = set()
        out = []
        for o in objs:
            oid = o.get("id")
            if oid and oid not in seen:
                seen.add(oid)
                out.append(o)
        return out

    return {
        "person": p.to_dict(),
        "spouses": uniq_by_id(spouses),
        "parents": uniq_by_id(parents),
        "children": uniq_by_id(children),
        "families": families,
    }


@app.get("/api/family/{fid}")
def api_family(fid: str):
    f = storage.get_family(fid)
    if f is None:
        raise HTTPException(status_code=404, detail="Family not found")
    husband = storage.get_person(f.husband_id) if f.husband_id else None
    wife = storage.get_person(f.wife_id) if f.wife_id else None
    children = [storage.get_person(cid).to_dict() for cid in f.children_ids if storage.get_person(cid)]
    return {
        "family": f.to_dict(),
        "husband": husband.to_dict() if husband else None,
        "wife": wife.to_dict() if wife else None,
        "children": children,
    }
