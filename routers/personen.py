import os
import shutil
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Bijlage, BijlageType, Geslacht, Ouderschap, Persoon, Relatie


def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None

router = APIRouter(prefix="/personen", tags=["personen"])
templates = Jinja2Templates(directory="templates")

UPLOADS_DIR = Path("uploads")


@router.get("/", response_class=HTMLResponse)
def personen_lijst(request: Request, zoek: str = "", db: Session = Depends(get_db)):
    query = db.query(Persoon)
    if zoek:
        zoek_term = f"%{zoek}%"
        query = query.filter(
            Persoon.voornaam.ilike(zoek_term) | Persoon.achternaam.ilike(zoek_term)
        )
    personen = query.order_by(Persoon.achternaam, Persoon.voornaam).all()
    return templates.TemplateResponse(
        request, "personen_lijst.html", {"personen": personen, "zoek": zoek}
    )


@router.get("/nieuw", response_class=HTMLResponse)
def persoon_nieuw_form(request: Request):
    return templates.TemplateResponse(
        request, "persoon_form.html",
        {"persoon": None, "geslacht_opties": list(Geslacht)},
    )


@router.post("/nieuw")
def persoon_aanmaken(
    voornaam: str = Form(...),
    achternaam: str = Form(...),
    geboorte_datum: str = Form(""),
    geboorte_plaats: str = Form(""),
    sterf_datum: str = Form(""),
    sterf_plaats: str = Form(""),
    begraven_locatie: str = Form(""),
    geslacht: str = Form(""),
    notities: str = Form(""),
    db: Session = Depends(get_db),
):
    persoon = Persoon(
        voornaam=voornaam,
        achternaam=achternaam,
        geboorte_datum=_parse_date(geboorte_datum),
        geboorte_plaats=geboorte_plaats or None,
        sterf_datum=_parse_date(sterf_datum),
        sterf_plaats=sterf_plaats or None,
        begraven_locatie=begraven_locatie or None,
        geslacht=geslacht or None,
        notities=notities or None,
    )
    db.add(persoon)
    db.commit()
    db.refresh(persoon)
    return RedirectResponse(url=f"/personen/{persoon.id}", status_code=303)


@router.get("/{persoon_id}", response_class=HTMLResponse)
def persoon_detail(request: Request, persoon_id: int, db: Session = Depends(get_db)):
    persoon = db.get(Persoon, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    alle_personen = (
        db.query(Persoon)
        .filter(Persoon.id != persoon_id)
        .order_by(Persoon.achternaam, Persoon.voornaam)
        .all()
    )
    return templates.TemplateResponse(
        request, "persoon_detail.html",
        {
            "persoon": persoon,
            "alle_personen": alle_personen,
            "ouderschap_typen": ["biologisch", "adoptief", "pleeg"],
        },
    )


@router.get("/{persoon_id}/bewerken", response_class=HTMLResponse)
def persoon_bewerken_form(
    request: Request, persoon_id: int, db: Session = Depends(get_db)
):
    persoon = db.get(Persoon, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    return templates.TemplateResponse(
        request, "persoon_form.html",
        {
            "persoon": persoon,
            "geslacht_opties": list(Geslacht),
        },
    )


@router.post("/{persoon_id}/bewerken")
def persoon_bewerken(
    persoon_id: int,
    voornaam: str = Form(...),
    achternaam: str = Form(...),
    geboorte_datum: str = Form(""),
    geboorte_plaats: str = Form(""),
    sterf_datum: str = Form(""),
    sterf_plaats: str = Form(""),
    begraven_locatie: str = Form(""),
    geslacht: str = Form(""),
    notities: str = Form(""),
    db: Session = Depends(get_db),
):
    persoon = db.get(Persoon, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    persoon.voornaam = voornaam
    persoon.achternaam = achternaam
    persoon.geboorte_datum = _parse_date(geboorte_datum)
    persoon.geboorte_plaats = geboorte_plaats or None
    persoon.sterf_datum = _parse_date(sterf_datum)
    persoon.sterf_plaats = sterf_plaats or None
    persoon.begraven_locatie = begraven_locatie or None
    persoon.geslacht = geslacht or None
    persoon.notities = notities or None
    db.commit()
    return RedirectResponse(url=f"/personen/{persoon_id}", status_code=303)


@router.get("/{persoon_id}/verwijderen", response_class=HTMLResponse)
def persoon_verwijderen_bevestig(
    request: Request, persoon_id: int, db: Session = Depends(get_db)
):
    persoon = db.get(Persoon, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    return templates.TemplateResponse(
        request, "persoon_verwijderen.html", {"persoon": persoon}
    )


@router.post("/{persoon_id}/verwijderen")
def persoon_verwijderen(
    persoon_id: int,
    force: str = Form(""),
    db: Session = Depends(get_db),
):
    persoon = db.get(Persoon, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")

    heeft_connecties = (
        persoon.relaties or persoon.ouder_van or persoon.kind_van or persoon.bijlagen
    )
    if heeft_connecties and not force:
        return RedirectResponse(
            url=f"/personen/{persoon_id}/verwijderen", status_code=303
        )

    if force:
        relaties = db.query(Relatie).filter(
            (Relatie.persoon_a_id == persoon_id) | (Relatie.persoon_b_id == persoon_id)
        ).all()
        for rel in relaties:
            for b in list(rel.bijlagen):
                if os.path.exists(b.bestandspad):
                    os.remove(b.bestandspad)
                db.delete(b)
            db.delete(rel)

        ouderschappen = db.query(Ouderschap).filter(
            (Ouderschap.ouder_id == persoon_id) | (Ouderschap.kind_id == persoon_id)
        ).all()
        for oud in ouderschappen:
            db.delete(oud)

        for b in list(persoon.bijlagen):
            if os.path.exists(b.bestandspad):
                os.remove(b.bestandspad)
            db.delete(b)

        db.flush()

    db.delete(persoon)
    db.commit()
    return RedirectResponse(url="/personen/", status_code=303)


@router.post("/{persoon_id}/bijlagen")
async def bijlage_uploaden(
    persoon_id: int,
    bestand: UploadFile = File(...),
    type: str = Form("foto"),
    omschrijving: str = Form(""),
    db: Session = Depends(get_db),
):
    persoon = db.get(Persoon, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")

    upload_map = UPLOADS_DIR / str(persoon_id)
    upload_map.mkdir(parents=True, exist_ok=True)

    bestandsnaam = f"{uuid.uuid4()}_{bestand.filename}"
    bestandspad = upload_map / bestandsnaam
    with bestandspad.open("wb") as f:
        shutil.copyfileobj(bestand.file, f)

    bijlage = Bijlage(
        persoon_id=persoon_id,
        bestandsnaam=bestand.filename,
        bestandspad=str(bestandspad),
        type=type,
        omschrijving=omschrijving or None,
    )
    db.add(bijlage)
    db.commit()
    return RedirectResponse(url=f"/personen/{persoon_id}", status_code=303)


@router.post("/{persoon_id}/bijlagen/{bijlage_id}/verwijderen")
def bijlage_verwijderen(
    persoon_id: int,
    bijlage_id: int,
    terug: str = Form(""),
    db: Session = Depends(get_db),
):
    bijlage = db.get(Bijlage, bijlage_id)
    if not bijlage or bijlage.persoon_id != persoon_id:
        raise HTTPException(status_code=404, detail="Bijlage niet gevonden")
    if os.path.exists(bijlage.bestandspad):
        os.remove(bijlage.bestandspad)
    db.delete(bijlage)
    db.commit()
    if terug == "verwijderen":
        return RedirectResponse(url=f"/personen/{persoon_id}/verwijderen", status_code=303)
    return RedirectResponse(url=f"/personen/{persoon_id}", status_code=303)


@router.post("/{persoon_id}/ouderschap")
def ouderschap_toevoegen(
    persoon_id: int,
    ouder_id: int = Form(...),
    type: str = Form("biologisch"),
    db: Session = Depends(get_db),
):
    bestaat = (
        db.query(Ouderschap)
        .filter_by(kind_id=persoon_id, ouder_id=ouder_id)
        .first()
    )
    if not bestaat:
        ouderschap = Ouderschap(kind_id=persoon_id, ouder_id=ouder_id, type=type)
        db.add(ouderschap)
        db.commit()
    return RedirectResponse(url=f"/personen/{persoon_id}", status_code=303)


@router.post("/{persoon_id}/ouderschap/{ouderschap_id}/verwijderen")
def ouderschap_verwijderen(
    persoon_id: int,
    ouderschap_id: int,
    terug: str = Form(""),
    db: Session = Depends(get_db),
):
    ouderschap = db.get(Ouderschap, ouderschap_id)
    if not ouderschap:
        raise HTTPException(status_code=404, detail="Ouderschap niet gevonden")
    db.delete(ouderschap)
    db.commit()
    if terug == "verwijderen":
        return RedirectResponse(url=f"/personen/{persoon_id}/verwijderen", status_code=303)
    return RedirectResponse(url=f"/personen/{persoon_id}", status_code=303)
