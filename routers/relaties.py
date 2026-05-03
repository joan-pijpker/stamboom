from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Persoon, Relatie, RelatieType


def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None

router = APIRouter(prefix="/relaties", tags=["relaties"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def relaties_lijst(request: Request, db: Session = Depends(get_db)):
    relaties = db.query(Relatie).order_by(Relatie.datum_start.desc()).all()
    return templates.TemplateResponse(
        request, "relaties_lijst.html", {"relaties": relaties}
    )


@router.get("/nieuw", response_class=HTMLResponse)
def relatie_nieuw_form(request: Request, db: Session = Depends(get_db)):
    personen = (
        db.query(Persoon).order_by(Persoon.achternaam, Persoon.voornaam).all()
    )
    return templates.TemplateResponse(
        request, "relatie_form.html",
        {
            "relatie": None,
            "personen": personen,
            "relatie_typen": list(RelatieType),
        },
    )


@router.post("/nieuw")
def relatie_aanmaken(
    persoon_a_id: int = Form(...),
    persoon_b_id: int = Form(...),
    type: str = Form(...),
    datum_start: str = Form(""),
    plaats_start: str = Form(""),
    datum_einde: str = Form(""),
    db: Session = Depends(get_db),
):
    if persoon_a_id == persoon_b_id:
        raise HTTPException(
            status_code=400, detail="Persoon A en B mogen niet dezelfde zijn"
        )
    relatie = Relatie(
        persoon_a_id=persoon_a_id,
        persoon_b_id=persoon_b_id,
        type=type,
        datum_start=_parse_date(datum_start),
        plaats_start=plaats_start or None,
        datum_einde=_parse_date(datum_einde),
    )
    db.add(relatie)
    db.commit()
    db.refresh(relatie)
    return RedirectResponse(url=f"/relaties/{relatie.id}", status_code=303)


@router.get("/{relatie_id}", response_class=HTMLResponse)
def relatie_detail(request: Request, relatie_id: int, db: Session = Depends(get_db)):
    relatie = db.get(Relatie, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    return templates.TemplateResponse(
        request, "relatie_detail.html", {"relatie": relatie}
    )


@router.get("/{relatie_id}/bewerken", response_class=HTMLResponse)
def relatie_bewerken_form(
    request: Request, relatie_id: int, db: Session = Depends(get_db)
):
    relatie = db.get(Relatie, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    personen = (
        db.query(Persoon).order_by(Persoon.achternaam, Persoon.voornaam).all()
    )
    return templates.TemplateResponse(
        request, "relatie_form.html",
        {
            "relatie": relatie,
            "personen": personen,
            "relatie_typen": list(RelatieType),
        },
    )


@router.post("/{relatie_id}/bewerken")
def relatie_bewerken(
    relatie_id: int,
    persoon_a_id: int = Form(...),
    persoon_b_id: int = Form(...),
    type: str = Form(...),
    datum_start: str = Form(""),
    plaats_start: str = Form(""),
    datum_einde: str = Form(""),
    db: Session = Depends(get_db),
):
    relatie = db.get(Relatie, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    relatie.persoon_a_id = persoon_a_id
    relatie.persoon_b_id = persoon_b_id
    relatie.type = type
    relatie.datum_start = _parse_date(datum_start)
    relatie.plaats_start = plaats_start or None
    relatie.datum_einde = _parse_date(datum_einde)
    db.commit()
    return RedirectResponse(url=f"/relaties/{relatie_id}", status_code=303)


@router.post("/{relatie_id}/verwijderen")
def relatie_verwijderen(
    relatie_id: int,
    terug_persoon_id: int = Form(0),
    db: Session = Depends(get_db),
):
    relatie = db.get(Relatie, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    db.delete(relatie)
    db.commit()
    if terug_persoon_id:
        return RedirectResponse(
            url=f"/personen/{terug_persoon_id}/verwijderen", status_code=303
        )
    return RedirectResponse(url="/relaties/", status_code=303)
