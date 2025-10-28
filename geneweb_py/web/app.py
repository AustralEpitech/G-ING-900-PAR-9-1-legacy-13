from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..storage import Storage
from ..models import Person, Family
from typing import List, Optional
from ..models import Note
import logging
from ..plugins import load_plugins
from ..config import load_config

app = FastAPI(title="geneweb-py (prototype)")

# Mount a static directory (created on demand)
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = Path("hd") / "etc"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Simple storage instance (file-based JSON in ./data)
storage = Storage(Path("data"))


def ensure_sample_data():
    # Create minimal sample data if storage empty so the UI shows something
    if len(storage.list_persons()) == 0:
        p = Person(first_name="John", surname="Doe", sex="M")
        q = Person(first_name="Jane", surname="Doe", sex="F")
        storage.add_person(p)
        storage.add_person(q)
        f = Family(husband_id=p.id, wife_id=q.id, children_ids=[])
        storage.add_family(f)

# Load plugins now (registers routes and lifecycle hooks). We load config first.
cfg = load_config()
try:
    load_plugins(app, storage, cfg, repo_root=Path("."), templates=templates)
except Exception:
    logging.exception("Failed to load plugins during module import")



@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


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
def create_person_form(request: Request):
    return templates.TemplateResponse("create_person.html", {"request": request})


@app.post("/person/create")
def create_person(
    first_name: str = Form(...), surname: str = Form(...), sex: Optional[str] = Form(None)
):
    p = Person(first_name=first_name, surname=surname, sex=sex)
    storage.add_person(p)
    logging.info("Created person %s; persons now: %s", p.id, list(storage.persons.keys()))
    return RedirectResponse(url=f"/person/{p.id}", status_code=303)


@app.get("/person/{pid}/edit", response_class=HTMLResponse)
def edit_person_form(request: Request, pid: str):
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return templates.TemplateResponse("edit_person.html", {"request": request, "person": p})


@app.post("/person/{pid}/edit")
def edit_person(pid: str, first_name: str = Form(...), surname: str = Form(...), sex: Optional[str] = Form(None)):
    p = storage.get_person(pid)
    if p is None:
        raise HTTPException(status_code=404, detail="Person not found")
    p.first_name = first_name
    p.surname = surname
    p.sex = sex
    storage.update_person(p)
    return RedirectResponse(url=f"/person/{pid}", status_code=303)


@app.post("/person/{pid}/delete")
def delete_person(pid: str):
    ok = storage.delete_person(pid)
    if not ok:
        raise HTTPException(status_code=404, detail="Person not found")
    return RedirectResponse(url="/", status_code=303)


@app.get("/family/create", response_class=HTMLResponse)
def create_family_form(request: Request):
    persons = storage.list_persons()
    return templates.TemplateResponse("create_family.html", {"request": request, "persons": persons})


@app.post("/family/create")
def create_family(
    husband_id: Optional[str] = Form(None),
    wife_id: Optional[str] = Form(None),
    children_ids: List[str] = Form([]),
):
    f = Family(husband_id=husband_id or None, wife_id=wife_id or None, children_ids=children_ids)
    storage.add_family(f)
    return RedirectResponse(url=f"/family/{f.id}", status_code=303)


@app.get("/family/{fid}/edit", response_class=HTMLResponse)
def edit_family_form(request: Request, fid: str):
    f = storage.get_family(fid)
    if f is None:
        raise HTTPException(status_code=404, detail="Family not found")
    persons = storage.list_persons()
    return templates.TemplateResponse("edit_family.html", {"request": request, "family": f, "persons": persons})


@app.post("/family/{fid}/edit")
def edit_family(
    fid: str,
    husband_id: Optional[str] = Form(None),
    wife_id: Optional[str] = Form(None),
    children_ids: List[str] = Form([]),
):
    f = storage.get_family(fid)
    if f is None:
        raise HTTPException(status_code=404, detail="Family not found")
    f.husband_id = husband_id or None
    f.wife_id = wife_id or None
    f.children_ids = children_ids
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
