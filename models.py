import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Geslacht(str, enum.Enum):
    M = "M"
    V = "V"
    X = "X"


class RelatieType(str, enum.Enum):
    getrouwd = "getrouwd"
    samenwonend = "samenwonend"
    gescheiden = "gescheiden"


class OuderschapType(str, enum.Enum):
    biologisch = "biologisch"
    adoptief = "adoptief"
    pleeg = "pleeg"


class BijlageType(str, enum.Enum):
    foto = "foto"
    document = "document"
    overig = "overig"


class Persoon(Base):
    __tablename__ = "persoon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    voornaam: Mapped[str] = mapped_column(String(100))
    achternaam: Mapped[str] = mapped_column(String(100))
    geboorte_datum: Mapped[date | None] = mapped_column(Date, nullable=True)
    geboorte_plaats: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sterf_datum: Mapped[date | None] = mapped_column(Date, nullable=True)
    sterf_plaats: Mapped[str | None] = mapped_column(String(200), nullable=True)
    begraven_locatie: Mapped[str | None] = mapped_column(String(300), nullable=True)
    geslacht: Mapped[Geslacht | None] = mapped_column(Enum(Geslacht), nullable=True)
    notities: Mapped[str | None] = mapped_column(Text, nullable=True)

    relaties_a: Mapped[list["Relatie"]] = relationship(
        "Relatie", foreign_keys="Relatie.persoon_a_id", back_populates="persoon_a"
    )
    relaties_b: Mapped[list["Relatie"]] = relationship(
        "Relatie", foreign_keys="Relatie.persoon_b_id", back_populates="persoon_b"
    )
    ouder_van: Mapped[list["Ouderschap"]] = relationship(
        "Ouderschap", foreign_keys="Ouderschap.ouder_id", back_populates="ouder"
    )
    kind_van: Mapped[list["Ouderschap"]] = relationship(
        "Ouderschap", foreign_keys="Ouderschap.kind_id", back_populates="kind"
    )
    bijlagen: Mapped[list["Bijlage"]] = relationship(
        "Bijlage", foreign_keys="Bijlage.persoon_id", back_populates="persoon"
    )

    @property
    def volledige_naam(self) -> str:
        return f"{self.voornaam} {self.achternaam}"

    @property
    def relaties(self) -> list["Relatie"]:
        return self.relaties_a + self.relaties_b


class Relatie(Base):
    __tablename__ = "relatie"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    persoon_a_id: Mapped[int] = mapped_column(Integer, ForeignKey("persoon.id"))
    persoon_b_id: Mapped[int] = mapped_column(Integer, ForeignKey("persoon.id"))
    type: Mapped[RelatieType] = mapped_column(Enum(RelatieType))
    datum_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    plaats_start: Mapped[str | None] = mapped_column(String(200), nullable=True)
    datum_einde: Mapped[date | None] = mapped_column(Date, nullable=True)

    persoon_a: Mapped["Persoon"] = relationship(
        "Persoon", foreign_keys=[persoon_a_id], back_populates="relaties_a"
    )
    persoon_b: Mapped["Persoon"] = relationship(
        "Persoon", foreign_keys=[persoon_b_id], back_populates="relaties_b"
    )
    bijlagen: Mapped[list["Bijlage"]] = relationship(
        "Bijlage", foreign_keys="Bijlage.relatie_id", back_populates="relatie"
    )


class Ouderschap(Base):
    __tablename__ = "ouderschap"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kind_id: Mapped[int] = mapped_column(Integer, ForeignKey("persoon.id"))
    ouder_id: Mapped[int] = mapped_column(Integer, ForeignKey("persoon.id"))
    type: Mapped[OuderschapType] = mapped_column(
        Enum(OuderschapType), default=OuderschapType.biologisch
    )

    kind: Mapped["Persoon"] = relationship(
        "Persoon", foreign_keys=[kind_id], back_populates="kind_van"
    )
    ouder: Mapped["Persoon"] = relationship(
        "Persoon", foreign_keys=[ouder_id], back_populates="ouder_van"
    )


class Bijlage(Base):
    __tablename__ = "bijlage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    persoon_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("persoon.id"), nullable=True
    )
    relatie_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("relatie.id"), nullable=True
    )
    bestandsnaam: Mapped[str] = mapped_column(String(255))
    bestandspad: Mapped[str] = mapped_column(String(500))
    type: Mapped[BijlageType] = mapped_column(Enum(BijlageType))
    omschrijving: Mapped[str | None] = mapped_column(Text, nullable=True)

    persoon: Mapped["Persoon | None"] = relationship(
        "Persoon", foreign_keys=[persoon_id], back_populates="bijlagen"
    )
    relatie: Mapped["Relatie | None"] = relationship(
        "Relatie", foreign_keys=[relatie_id], back_populates="bijlagen"
    )
