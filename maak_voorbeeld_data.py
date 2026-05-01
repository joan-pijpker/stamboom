"""
Maakt een voorbeelddatabase aan met fictieve familiegegevens.

Gebruik:
    python maak_voorbeeld_data.py

Hiermee wordt voorbeeld.db aangemaakt. Om de app met deze database te starten:
    DATABASE_URL=sqlite:///./voorbeeld.db uvicorn main:app --reload
"""

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import Geslacht, OuderschapType, Ouderschap, Persoon, Relatie, RelatieType

DATABASE_URL = "sqlite:///./voorbeeld.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

with Session() as db:
    # --- Generatie 1: Grootouders vaderszijde ---
    hendrik = Persoon(
        voornaam="Hendrik",
        achternaam="de Vries",
        geslacht=Geslacht.M,
        geboorte_datum=date(1920, 3, 14),
        geboorte_plaats="Groningen",
        sterf_datum=date(1995, 11, 2),
        sterf_plaats="Groningen",
        notities="Werkte als timmerman bij de scheepsbouw.",
    )
    maria = Persoon(
        voornaam="Maria",
        achternaam="van den Berg",
        geslacht=Geslacht.V,
        geboorte_datum=date(1923, 7, 8),
        geboorte_plaats="Groningen",
        sterf_datum=date(2010, 4, 20),
        sterf_plaats="Groningen",
    )

    # --- Generatie 1: Grootouders moederszijde ---
    pieter = Persoon(
        voornaam="Pieter",
        achternaam="Jansen",
        geslacht=Geslacht.M,
        geboorte_datum=date(1918, 12, 1),
        geboorte_plaats="Rotterdam",
        sterf_datum=date(1988, 6, 15),
        sterf_plaats="Rotterdam",
    )
    cornelia = Persoon(
        voornaam="Cornelia",
        achternaam="Smit",
        geslacht=Geslacht.V,
        geboorte_datum=date(1921, 2, 28),
        geboorte_plaats="Rotterdam",
        sterf_datum=date(2005, 9, 3),
        sterf_plaats="Rotterdam",
        notities="Actief in de kerk en het buurtcomité.",
    )

    # --- Generatie 2: Ouders ---
    willem = Persoon(
        voornaam="Willem",
        achternaam="de Vries",
        geslacht=Geslacht.M,
        geboorte_datum=date(1950, 5, 22),
        geboorte_plaats="Groningen",
    )
    anna = Persoon(
        voornaam="Anna",
        achternaam="Jansen",
        geslacht=Geslacht.V,
        geboorte_datum=date(1952, 9, 10),
        geboorte_plaats="Rotterdam",
    )

    # --- Generatie 3: Kinderen ---
    thomas = Persoon(
        voornaam="Thomas",
        achternaam="de Vries",
        geslacht=Geslacht.M,
        geboorte_datum=date(1980, 1, 30),
        geboorte_plaats="Utrecht",
    )
    sophie = Persoon(
        voornaam="Sophie",
        achternaam="de Vries",
        geslacht=Geslacht.V,
        geboorte_datum=date(1982, 6, 17),
        geboorte_plaats="Utrecht",
    )
    lucas = Persoon(
        voornaam="Lucas",
        achternaam="de Vries",
        geslacht=Geslacht.M,
        geboorte_datum=date(1985, 11, 4),
        geboorte_plaats="Utrecht",
    )

    # --- Partner van Thomas ---
    lisa = Persoon(
        voornaam="Lisa",
        achternaam="Bakker",
        geslacht=Geslacht.V,
        geboorte_datum=date(1981, 3, 22),
        geboorte_plaats="Amsterdam",
    )

    db.add_all([hendrik, maria, pieter, cornelia, willem, anna, thomas, sophie, lucas, lisa])
    db.flush()

    # --- Relaties ---
    relatie_grootouders_v = Relatie(
        persoon_a_id=hendrik.id,
        persoon_b_id=maria.id,
        type=RelatieType.getrouwd,
        datum_start=date(1948, 6, 5),
        plaats_start="Groningen",
    )
    relatie_grootouders_m = Relatie(
        persoon_a_id=pieter.id,
        persoon_b_id=cornelia.id,
        type=RelatieType.getrouwd,
        datum_start=date(1946, 8, 12),
        plaats_start="Rotterdam",
    )
    relatie_ouders = Relatie(
        persoon_a_id=willem.id,
        persoon_b_id=anna.id,
        type=RelatieType.getrouwd,
        datum_start=date(1978, 5, 19),
        plaats_start="Utrecht",
    )
    relatie_thomas_lisa = Relatie(
        persoon_a_id=thomas.id,
        persoon_b_id=lisa.id,
        type=RelatieType.getrouwd,
        datum_start=date(2008, 9, 6),
        plaats_start="Amsterdam",
    )

    db.add_all([relatie_grootouders_v, relatie_grootouders_m, relatie_ouders, relatie_thomas_lisa])
    db.flush()

    # --- Ouderschappen ---
    ouderschappen = [
        # Willem is kind van Hendrik en Maria
        Ouderschap(kind_id=willem.id, ouder_id=hendrik.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=willem.id, ouder_id=maria.id, type=OuderschapType.biologisch),
        # Anna is kind van Pieter en Cornelia
        Ouderschap(kind_id=anna.id, ouder_id=pieter.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=anna.id, ouder_id=cornelia.id, type=OuderschapType.biologisch),
        # Thomas, Sophie en Lucas zijn kinderen van Willem en Anna
        Ouderschap(kind_id=thomas.id, ouder_id=willem.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=thomas.id, ouder_id=anna.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=sophie.id, ouder_id=willem.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=sophie.id, ouder_id=anna.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=lucas.id, ouder_id=willem.id, type=OuderschapType.biologisch),
        Ouderschap(kind_id=lucas.id, ouder_id=anna.id, type=OuderschapType.biologisch),
    ]
    db.add_all(ouderschappen)
    db.commit()

print("Voorbeelddatabase aangemaakt: voorbeeld.db")
print("  10 personen, 4 relaties, 10 ouderschappen")
print()
print("Start de app met deze database:")
print("  DATABASE_URL=sqlite:///./voorbeeld.db uvicorn main:app --reload")
