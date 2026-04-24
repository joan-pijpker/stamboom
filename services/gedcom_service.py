"""GEDCOM 5.5 import and export for the stamboom application."""

import re
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import IO

from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser
from sqlalchemy.orm import Session

from models import Geslacht, Ouderschap, Persoon, Relatie, RelatieType

MAANDEN_NL = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
MAANDEN_EN = {v: k for k, v in MAANDEN_NL.items()}

GEDCOM_GESLACHT = {"M": "M", "V": "F", "X": "U"}
IMPORT_GESLACHT = {"M": Geslacht.M, "F": Geslacht.V, "U": Geslacht.X}


def _parse_gedcom_datum(datum_str: str) -> date | None:
    if not datum_str:
        return None
    datum_str = datum_str.strip().upper()
    # "1 JAN 1990"
    m = re.match(r"(\d{1,2})\s+([A-Z]{3})\s+(\d{4})", datum_str)
    if m:
        try:
            return date(int(m.group(3)), MAANDEN_NL[m.group(2)], int(m.group(1)))
        except (KeyError, ValueError):
            pass
    # "JAN 1990"
    m = re.match(r"([A-Z]{3})\s+(\d{4})", datum_str)
    if m:
        try:
            return date(int(m.group(2)), MAANDEN_NL[m.group(1)], 1)
        except (KeyError, ValueError):
            pass
    # "1990"
    m = re.match(r"(\d{4})$", datum_str)
    if m:
        return date(int(m.group(1)), 1, 1)
    return None


def _datum_naar_gedcom(d: date | None) -> str:
    if not d:
        return ""
    return f"{d.day} {MAANDEN_EN[d.month]} {d.year}"


def importeer_gedcom(bestand: IO[bytes], db: Session) -> dict[str, int]:
    """Importeer een GEDCOM-bestand in de database. Geeft statistieken terug."""
    parser = Parser()
    parser.parse(bestand)

    indi_map: dict[str, int] = {}  # GEDCOM pointer → persoon.id

    for element in parser.get_root_child_elements():
        if not isinstance(element, IndividualElement):
            continue

        voornaam, achternaam = element.get_name()
        voornaam = voornaam.strip() or "Onbekend"
        achternaam = achternaam.strip() or "Onbekend"

        geboorte_datum_str, geboorte_plaats, _ = element.get_birth_data()
        sterf_datum_str, sterf_plaats, _ = element.get_death_data()
        begraaf_datum_str, begraaf_plaats, _ = element.get_burial_data()

        geslacht_str = element.get_gender().strip().upper()

        persoon = Persoon(
            voornaam=voornaam,
            achternaam=achternaam,
            geboorte_datum=_parse_gedcom_datum(geboorte_datum_str),
            geboorte_plaats=geboorte_plaats or None,
            sterf_datum=_parse_gedcom_datum(sterf_datum_str),
            sterf_plaats=sterf_plaats or None,
            begraven_locatie=begraaf_plaats or None,
            geslacht=IMPORT_GESLACHT.get(geslacht_str),
        )
        db.add(persoon)
        db.flush()
        indi_map[element.get_pointer()] = persoon.id

    # Families verwerken
    for element in parser.get_root_child_elements():
        if not isinstance(element, FamilyElement):
            continue

        echtgenoten = parser.get_family_members(element, "PARENTS")
        kinderen = parser.get_family_members(element, "CHIL")

        huwelijk_datum_str = ""
        huwelijk_plaats = ""
        for kind_el in element.get_child_elements():
            if kind_el.get_tag() == "MARR":
                for sub in kind_el.get_child_elements():
                    if sub.get_tag() == "DATE":
                        huwelijk_datum_str = sub.get_value()
                    if sub.get_tag() == "PLAC":
                        huwelijk_plaats = sub.get_value()

        persoon_ids = [
            indi_map[e.get_pointer()]
            for e in echtgenoten
            if e.get_pointer() in indi_map
        ]

        if len(persoon_ids) == 2:
            relatie = Relatie(
                persoon_a_id=persoon_ids[0],
                persoon_b_id=persoon_ids[1],
                type=RelatieType.getrouwd,
                datum_start=_parse_gedcom_datum(huwelijk_datum_str),
                plaats_start=huwelijk_plaats or None,
            )
            db.add(relatie)

        for ouder_el in echtgenoten:
            ouder_ptr = ouder_el.get_pointer()
            if ouder_ptr not in indi_map:
                continue
            for kind_el in kinderen:
                kind_ptr = kind_el.get_pointer()
                if kind_ptr not in indi_map:
                    continue
                ouderschap = Ouderschap(
                    ouder_id=indi_map[ouder_ptr],
                    kind_id=indi_map[kind_ptr],
                )
                db.add(ouderschap)

    db.commit()
    return {"personen": len(indi_map)}


def exporteer_gedcom(db: Session) -> bytes:
    """Exporteer de volledige database als GEDCOM 5.5 bytes."""
    personen = db.query(Persoon).all()
    relaties = db.query(Relatie).all()

    lines: list[str] = []

    def r(line: str) -> None:
        lines.append(line)

    r("0 HEAD")
    r("1 GEDC")
    r("2 VERS 5.5.1")
    r("2 FORM LINEAGE-LINKED")
    r("1 CHAR UTF-8")
    r(f"1 SOUR Stamboom")
    r(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}")

    for p in personen:
        r(f"0 @I{p.id}@ INDI")
        r(f"1 NAME {p.voornaam} /{p.achternaam}/")
        r(f"2 GIVN {p.voornaam}")
        r(f"2 SURN {p.achternaam}")
        if p.geslacht:
            r(f"1 SEX {GEDCOM_GESLACHT.get(p.geslacht.value, 'U')}")
        if p.geboorte_datum or p.geboorte_plaats:
            r("1 BIRT")
            if p.geboorte_datum:
                r(f"2 DATE {_datum_naar_gedcom(p.geboorte_datum)}")
            if p.geboorte_plaats:
                r(f"2 PLAC {p.geboorte_plaats}")
        if p.sterf_datum or p.sterf_plaats:
            r("1 DEAT")
            if p.sterf_datum:
                r(f"2 DATE {_datum_naar_gedcom(p.sterf_datum)}")
            if p.sterf_plaats:
                r(f"2 PLAC {p.sterf_plaats}")
        if p.begraven_locatie:
            r("1 BURI")
            r(f"2 PLAC {p.begraven_locatie}")
        if p.notities:
            r(f"1 NOTE {p.notities}")

    for rel in relaties:
        r(f"0 @F{rel.id}@ FAM")
        r(f"1 HUSB @I{rel.persoon_a_id}@")
        r(f"1 WIFE @I{rel.persoon_b_id}@")
        if rel.datum_start or rel.plaats_start:
            r("1 MARR")
            if rel.datum_start:
                r(f"2 DATE {_datum_naar_gedcom(rel.datum_start)}")
            if rel.plaats_start:
                r(f"2 PLAC {rel.plaats_start}")
        # Kinderen: vind via ouderschap
        from models import Ouderschap
        kind_ids_a = {
            o.kind_id
            for o in db.query(Ouderschap).filter_by(ouder_id=rel.persoon_a_id).all()
        }
        kind_ids_b = {
            o.kind_id
            for o in db.query(Ouderschap).filter_by(ouder_id=rel.persoon_b_id).all()
        }
        gedeelde_kinderen = kind_ids_a & kind_ids_b
        for kid_id in gedeelde_kinderen:
            r(f"1 CHIL @I{kid_id}@")

    r("0 TRLR")
    return "\n".join(lines).encode("utf-8")
