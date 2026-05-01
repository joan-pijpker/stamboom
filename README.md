# Stamboom

Een webapplicatie voor het bijhouden van genealogische gegevens. Leg familieleden, hun onderlinge relaties en ouderschappen vast, voeg foto's en documenten toe, en bekijk de stamboom als interactieve grafiek.

## Functies

- **Personen beheren** — Voornaam, achternaam, geboorte- en sterfgegevens, geslacht en notities
- **Relaties vastleggen** — Huwelijk, samenwonen of scheiding, met datum en plaats
- **Ouderschappen** — Biologisch, adopptief of pleegouderschap
- **Bijlagen** — Foto's en documenten koppelen aan personen of relaties
- **Stamboomvisualisatie** — Interactieve grafiek op basis van D3.js
- **GEDCOM-ondersteuning** — Importeer en exporteer naar het standaard genealogieformaat

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
uvicorn main:app --reload
```

De applicatie is daarna bereikbaar op [http://localhost:8000](http://localhost:8000).

## Voorbeelddatabase

De repository bevat `voorbeeld.db` met een fictieve familie over drie generaties. Start de app hiermee om de functionaliteit direct te kunnen verkennen:

```bash
DATABASE_URL=sqlite:///./voorbeeld.db uvicorn main:app --reload
```

Om de voorbeelddatabase opnieuw aan te maken:

```bash
python maak_voorbeeld_data.py
```

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
├── main.py                  # FastAPI-applicatie en startpunt
├── models.py                # SQLAlchemy-modellen
├── database.py              # Databaseverbinding
├── schemas.py               # Pydantic-validatieschema's
├── routers/
│   ├── personen.py          # Persoonbeheer
│   ├── relaties.py          # Relatiebeheer
│   └── gedcom.py            # GEDCOM import/export
├── services/
│   └── gedcom_service.py    # GEDCOM-verwerking
├── templates/               # Jinja2 HTML-templates
├── static/                  # CSS en JavaScript
├── alembic/                 # Databasemigraties
├── voorbeeld.db             # Voorbeelddatabase met fictieve data
└── maak_voorbeeld_data.py   # Script om voorbeelddatabase aan te maken
```

## Omgevingsvariabelen

| Variabele      | Standaard                  | Omschrijving                        |
|----------------|----------------------------|-------------------------------------|
| `DATABASE_URL` | `sqlite:///./stamboom.db`  | Verbindings-URL van de database     |
