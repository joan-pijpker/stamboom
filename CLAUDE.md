# Stamboom – projectdocumentatie voor coding agents

## Stack
- **Backend**: FastAPI + SQLAlchemy (SQLite via `stamboom.db`)
- **Templates**: Jinja2 in `templates/`
- **Frontend**: Bootstrap 5 + Bootstrap Icons (CDN), D3.js v7 (CDN, alleen stamboom.html)
- **GEDCOM**: import/export via `services/gedcom_service.py`
- **Migraties**: Alembic (`alembic/`)
- **Starten**: `.venv/bin/uvicorn main:app --reload`

## Bestandsstructuur

```
main.py                  # app-instantie, home- en stamboomroute
database.py              # engine + get_db dependency
models.py                # SQLAlchemy ORM-modellen
schemas.py               # Pydantic-schema's
routers/
  personen.py            # CRUD personen, bijlagen, ouderschappen
  relaties.py            # CRUD relaties (partnerschappen)
  gedcom.py              # import/export
services/
  gedcom_service.py      # GEDCOM 5.5 parser & generator
templates/
  base.html              # navbar, thema-toggle, Bootstrap
  stamboom.html          # D3.js-visualisatie (volledig + uitsnede)
  personen_lijst.html    # zoekbare personenlijst
  persoon_detail.html    # detailpagina met ouders/kinderen/relaties/bijlagen
  persoon_form.html      # aanmaken/bewerken persoon
  relaties_lijst.html
  relatie_detail.html
  relatie_form.html
  gedcom.html
uploads/                 # geüploade foto's en documenten
```

## Datamodellen

### Persoon
Velden: `id, voornaam, achternaam, geboorte_datum, geboorte_plaats, sterf_datum, sterf_plaats, begraven_locatie, geslacht (M/V/X), notities`
Property: `volledige_naam`, `relaties` (= relaties_a + relaties_b)

### Relatie (partnerschap)
`id, persoon_a_id, persoon_b_id, type (getrouwd/samenwonend/gescheiden), datum_start, plaats_start, datum_einde`
Koppelt twee personen als stel. Symmetrisch: beide kanten zijn gelijkwaardig.

### Ouderschap
`id, kind_id, ouder_id, type (biologisch/adoptief/pleeg)`
Eén record per ouder-kind-paar. Een kind kan max. 2 ouders hebben (wordt afgedwongen in de visualisatie, niet in de database).

### Bijlage
`id, persoon_id (nullable), relatie_id (nullable), bestandsnaam, bestandspad, type (foto/document/overig), omschrijving`
Gekoppeld aan ofwel een persoon ofwel een relatie.

## Routes

| Methode | Pad | Functie |
|---------|-----|---------|
| GET | `/` | Homepagina met statistieken |
| GET | `/stamboom?focus=<id>` | Stamboomvisualisatie (focus schakelt naar uitsnede-modus) |
| GET/POST | `/personen/` | Lijst + zoeken |
| GET/POST | `/personen/nieuw` | Aanmaken |
| GET/POST | `/personen/<id>` | Detail / bewerken / verwijderen |
| POST | `/personen/<id>/bijlagen` | Upload bijlage |
| POST | `/personen/<id>/ouderschap` | Ouder-kind-koppeling toevoegen |
| GET/POST | `/relaties/` | Lijst relaties |
| GET/POST | `/relaties/nieuw` | Nieuwe relatie |
| GET/POST | `/relaties/<id>` | Detail / bewerken / verwijderen |
| GET/POST | `/gedcom/` | GEDCOM import/export pagina |
| GET | `/gedcom/exporteer` | Download .ged bestand |

## Stamboomvisualisatie (stamboom.html)

### Data vanuit backend (`main.py /stamboom`)
```python
boom_data = {
    "nodes": [{"id", "voornaam", "achternaam", "geslacht", "geboorte_jaar", "sterf_jaar"}, ...],
    "links": [{"source": ouder_id, "target": kind_id}, ...],   # Ouderschap-records
    "partners": [{"a": persoon_a_id, "b": persoon_b_id}, ...], # Relatie-records
}
focus = int  # 0 = geen focus (volledig overzicht)
```

### JavaScript-structuren
- `nodeMap`: `id → node-object`
- `parentMap`: `kind_id → [ouder_id, ...]` (max 2)
- `childMap`: `ouder_id → [kind_id, ...]`
- `partnerMap`: `id → [partner_id, ...]` (bidirectioneel)

### Twee weergavemodi (radio-buttons)

**Volledig overzicht** (`drawFullTree`):
1. Generatieniveau per persoon = langste pad van root (iteratief totdat stabiel)
2. Roots (geen ouders) top-down geplaatst via `subtreeW()` + `placeNode()`
3. Reeds geplaatste nodes worden overgeslagen (lost gedeelde kinderen op)
4. Verbindingslijnen gegroepeerd per gezinsgroep (unieke ouder-combinatie → één bus-lijn)
5. Auto-fit zoom: past schaal en offset aan op bounding box van alle posities

**Uitsnede** (`drawFilteredTree(focusId, maxUp, maxDown)`):
- `maxUp`: lagen voorouders omhoog (slot-gebaseerd binaire boom)
- `maxDown`: lagen nakomelingen omlaag; **0 = alleen focuspersoon + partner**, 1 = ook kinderen, etc.
- Partner(s) van focuspersoon worden naast hem/haar geplaatst (rechts, `+ SLOT_W` per partner)
- Nakomelingen gecentreerd op middelpunt tussen focuspersoon en laatste partner
- Koppellijn getekend tussen focuspersoon en partner(s)
- Verbindingslijnen nakomelingen: gezinsgroepen (voorkomt dubbele lijnen)
- Zoom: focuspersoon gecentreerd horizontaal

### Layout-constanten
```javascript
BOX_W = 158, BOX_H = 70, BOX_R = 7  // persoonsvakje
GEN_H = 160                           // verticale afstand tussen generaties
SLOT_W = BOX_W + 45 = 203            // horizontale slotbreedte
```

### Thema
Dark mode is de standaard. Voorkeur opgeslagen in `localStorage('theme')`.
CSS-variabelen in `base.html`: `--tree-line`, `--tree-text`, `--tree-bg`, `--box-bg-M/V/X`, `--box-border-M/V/X`.
Geslacht-kleuren: M = blauw, V = roze, X = grijs.
