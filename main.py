from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, Ouderschap, Persoon, Relatie
from routers import gedcom, personen, relaties

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stamboom", docs_url="/api/docs")

Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(personen.router)
app.include_router(relaties.router)
app.include_router(gedcom.router)

templates = Jinja2Templates(directory="templates")


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

    return templates.TemplateResponse(
        request, "stamboom.html",
        {
            "personen": alle_personen,
            "boom_data": {"nodes": nodes, "links": links},
            "focus": focus,
        },
    )
