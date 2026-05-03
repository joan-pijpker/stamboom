# Stamboom

Een webapplicatie voor het bijhouden van genealogische gegevens. Leg familieleden, hun onderlinge relaties en ouderschappen vast, voeg foto's en documenten toe, en bekijk de stamboom als interactieve grafiek.

## Functies

- **Personen beheren** — Voornaam, achternaam, geboorte- en sterfgegevens, geslacht en notities
- **Relaties vastleggen** — Huwelijk, samenwonen of scheiding, met datum en plaats
- **Ouderschappen** — Biologisch, adoptief of pleegouderschap
- **Bijlagen** — Foto's en documenten koppelen aan personen of relaties
- **Stamboomvisualisatie** — Interactieve D3.js-grafiek met volledig overzicht en uitsnede-modus
- **GEDCOM-ondersteuning** — Importeer en exporteer naar het standaard genealogieformaat
- **Meerdere databases** — Beheer meerdere losse families in aparte databases

## Vereisten

- Python 3.12 of hoger
- [uv](https://docs.astral.sh/uv/) (aanbevolen) of pip

## Installatie

```bash
# Kloon de repository
git clone <repository-url>
cd stamboom

# Installeer afhankelijkheden met uv
uv sync

# Of met pip in een virtualenv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Starten

```bash
# Met uv
uv run uvicorn main:app --reload

# Of na activeren van de virtualenv
.venv/bin/uvicorn main:app --reload
```

De applicatie is daarna bereikbaar op [http://localhost:8000](http://localhost:8000).

## Voorbeelddatabase

De repository bevat `databases/voorbeeld.db` met een fictieve familie over drie generaties. Na het starten van de app kun je deze database kiezen via het database-menu in de navigatiebalk (het database-icoon rechtsboven).

Om de voorbeelddatabase opnieuw aan te maken:

```bash
python maak_voorbeeld_data.py
```

## Meerdere databases

De applicatie ondersteunt meerdere losse databases, zodat je verschillende families gescheiden kunt bijhouden.

**Wisselen via de interface**

Klik in de navigatiebalk op het database-icoon (rechtsboven). In het uitklapmenu zie je alle beschikbare databases. Klik op een naam om naar die database over te schakelen. De keuze wordt opgeslagen in een cookie en blijft actief bij de volgende sessie.

**Nieuwe database aanmaken via de interface**

Onderin hetzelfde uitklapmenu staat een tekstveld. Typ de naam van de nieuwe familie en klik op het plusje. De database wordt direct aangemaakt en geselecteerd. Toegestane tekens: letters, cijfers, `-` en `_`.

**Nieuwe database aanmaken via de bestandsmap**

Je kunt ook handmatig een leeg SQLite-bestand aanmaken in de map `databases/`:

```bash
# Naam mag alleen letters, cijfers, - en _ bevatten
touch databases/mijnfamilie.db
```

De app herkent het bestand bij de volgende herstart en vult het schema automatisch in.

**Databases en versiebeheer**

Alleen `databases/voorbeeld.db` wordt meegenomen in git. Alle andere `.db`-bestanden in `databases/` staan in `.gitignore` en worden nooit naar GitHub gepusht.

## Stamboomvisualisatie

De visualisatie heeft twee modi, te kiezen via de knoppen bovenaan de pagina:

- **Volledig overzicht** — Toont alle personen in de database in één boom. Aangetrouwde partners staan verticaal gestapeld onder hun partner uit de familielijn.
- **Uitsnede** — Kies een persoon en geef aan hoeveel generaties omhoog (voorouders) en omlaag (nakomelingen) je wilt zien. Bij 0 lagen omlaag worden alleen de focuspersoon en diens partner(s) getoond.

Navigeren kan door te slepen en te scrollen (zoom). Klikken op een persoonsvakje opent de detailpagina.

## Databasemigraties

Alembic wordt gebruikt voor schemabeheer. Na een schema-wijziging in `models.py`:

```bash
# Maak een nieuwe migratie aan
alembic revision --autogenerate -m "omschrijving"

# Pas de migratie toe
alembic upgrade head
```

## Projectstructuur

```
stamboom/
├── main.py                  # FastAPI-applicatie, routes en middleware
├── models.py                # SQLAlchemy-modellen
├── database.py              # Database-engine per familie, get_db dependency
├── schemas.py               # Pydantic-validatieschema's
├── routers/
│   ├── personen.py          # Persoonbeheer (CRUD, bijlagen, ouderschappen)
│   ├── relaties.py          # Relatiebeheer
│   └── gedcom.py            # GEDCOM import/export
├── services/
│   └── gedcom_service.py    # GEDCOM 5.5 parser en generator
├── templates/               # Jinja2 HTML-templates
├── static/                  # Statische bestanden
├── alembic/                 # Databasemigraties
├── databases/               # SQLite-bestanden (één per familie)
│   └── voorbeeld.db         # Voorbeelddatabase met fictieve data
├── uploads/                 # Geüploade foto's en documenten
└── maak_voorbeeld_data.py   # Script om voorbeelddatabase aan te maken
```
