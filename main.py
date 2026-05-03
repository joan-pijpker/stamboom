import os
import re
import shutil
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import DB_DIR, get_db, get_engine_for, list_databases
from models import Base, Ouderschap, Persoon, Relatie  # noqa: F401 – registreert modellen bij Base
from routers import gedcom, personen, relaties

# ── Databases-map aanmaken en bestaande bestanden migreren ────────────────
os.makedirs(DB_DIR, exist_ok=True)
for _bestand in ["stamboom.db", "voorbeeld.db"]:
    _src, _dst = _bestand, os.path.join(DB_DIR, _bestand)
    if os.path.exists(_src) and not os.path.exists(_dst):
        shutil.copy2(_src, _dst)

# Zorg dat de standaarddatabase altijd bestaat
get_engine_for("stamboom")

app = FastAPI(title="Stamboom", docs_url="/api/docs")

Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(personen.router)
app.include_router(relaties.router)
app.include_router(gedcom.router)

templates = Jinja2Templates(directory="templates")


# ── Middleware: actieve database beschikbaar stellen in alle templates ─────
@app.middleware("http")
async def add_db_state(request: Request, call_next):
    actief = request.cookies.get("actief_db", "stamboom")
    if not os.path.exists(os.path.join(DB_DIR, f"{actief}.db")):
        actief = "stamboom"
    request.state.actief_db = actief
    request.state.databases = list_databases()
    return await call_next(request)


# ── Database-beheer ────────────────────────────────────────────────────────
@app.post("/databases/selecteer")
def selecteer_database(naam: str = Form(...)):
    if not os.path.exists(os.path.join(DB_DIR, f"{naam}.db")):
        naam = "stamboom"
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("actief_db", naam, max_age=365 * 24 * 3600)
    return response


@app.post("/databases/nieuw")
def nieuw_database(naam: str = Form(...)):
    naam = re.sub(r"[^a-zA-Z0-9_-]", "", naam)[:50]
    if not naam:
        return RedirectResponse(url="/", status_code=303)
    get_engine_for(naam)  # maakt bestand + schema aan
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("actief_db", naam, max_age=365 * 24 * 3600)
    return response


# ── Paginaroutes ───────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "index.html",
        {
            "aantal_personen": db.query(Persoon).count(),
            "aantal_relaties": db.query(Relatie).count(),
        },
    )


@app.get("/stamboom", response_class=HTMLResponse)
def stamboom(request: Request, focus: int = 0, db: Session = Depends(get_db)):
    alle_personen = db.query(Persoon).order_by(Persoon.achternaam, Persoon.voornaam).all()
    ouderschappen = db.query(Ouderschap).all()

    nodes = [
        {
            "id": p.id,
            "voornaam": p.voornaam,
            "achternaam": p.achternaam,
            "geslacht": p.geslacht.value if p.geslacht else None,
            "geboorte_jaar": p.geboorte_datum.year if p.geboorte_datum else None,
            "sterf_jaar": p.sterf_datum.year if p.sterf_datum else None,
        }
        for p in alle_personen
    ]

    links = [
        {"source": o.ouder_id, "target": o.kind_id}
        for o in ouderschappen
    ]

    alle_relaties = db.query(Relatie).all()
    partners = [
        {"a": r.persoon_a_id, "b": r.persoon_b_id}
        for r in alle_relaties
    ]

    return templates.TemplateResponse(
        request, "stamboom.html",
        {
            "personen": alle_personen,
            "boom_data": {"nodes": nodes, "links": links, "partners": partners},
            "focus": focus,
        },
    )
