from datetime import date

from pydantic import BaseModel

from models import BijlageType, Geslacht, OuderschapType, RelatieType


class PersoonBase(BaseModel):
    voornaam: str
    achternaam: str
    geboorte_datum: date | None = None
    geboorte_plaats: str | None = None
    sterf_datum: date | None = None
    sterf_plaats: str | None = None
    begraven_locatie: str | None = None
    geslacht: Geslacht | None = None
    notities: str | None = None


class PersoonCreate(PersoonBase):
    pass


class PersoonUpdate(PersoonBase):
    pass


class PersoonOut(PersoonBase):
    id: int

    model_config = {"from_attributes": True}


class RelatieBase(BaseModel):
    persoon_a_id: int
    persoon_b_id: int
    type: RelatieType
    datum_start: date | None = None
    plaats_start: str | None = None
    datum_einde: date | None = None


class RelatieCreate(RelatieBase):
    pass


class RelatieUpdate(BaseModel):
    type: RelatieType | None = None
    datum_start: date | None = None
    plaats_start: str | None = None
    datum_einde: date | None = None


class RelatieOut(RelatieBase):
    id: int
    persoon_a: PersoonOut
    persoon_b: PersoonOut

    model_config = {"from_attributes": True}


class OuderschapCreate(BaseModel):
    kind_id: int
    ouder_id: int
    type: OuderschapType = OuderschapType.biologisch


class OuderschapOut(OuderschapCreate):
    id: int
    kind: PersoonOut
    ouder: PersoonOut

    model_config = {"from_attributes": True}


class BijlageOut(BaseModel):
    id: int
    persoon_id: int | None
    relatie_id: int | None
    bestandsnaam: str
    bestandspad: str
    type: BijlageType
    omschrijving: str | None

    model_config = {"from_attributes": True}
