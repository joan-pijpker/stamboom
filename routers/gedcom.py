from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from services.gedcom_service import exporteer_gedcom, importeer_gedcom

router = APIRouter(prefix="/gedcom", tags=["gedcom"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def gedcom_pagina(request: Request):
    return templates.TemplateResponse(request, "gedcom.html")


@router.post("/importeer")
async def gedcom_importeer(
    bestand: UploadFile = File(...), db: Session = Depends(get_db)
):
    inhoud = await bestand.read()
    statistieken = importeer_gedcom(inhoud, db)
    return RedirectResponse(
        url=f"/gedcom/?import_ok={statistieken['personen']}", status_code=303
    )


@router.get("/exporteer")
def gedcom_exporteer(db: Session = Depends(get_db)):
    inhoud = exporteer_gedcom(db)
    return Response(
        content=inhoud,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=stamboom.ged"},
    )
