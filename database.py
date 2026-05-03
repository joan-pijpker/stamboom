import os
from typing import Optional

from fastapi import Cookie
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_DIR = "databases"
DATABASE_URL = f"sqlite:///{DB_DIR}/stamboom.db"  # bewaard voor Alembic-compatibiliteit


class Base(DeclarativeBase):
    pass


_engines: dict = {}


def get_engine_for(db_name: str):
    if db_name not in _engines:
        path = os.path.join(DB_DIR, f"{db_name}.db")
        engine = create_engine(
            f"sqlite:///{path}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        _engines[db_name] = engine
    return _engines[db_name]


def _valid_db_name(name: Optional[str]) -> str:
    if name and os.path.exists(os.path.join(DB_DIR, f"{name}.db")):
        return name
    return "stamboom"


def list_databases() -> list[str]:
    if not os.path.exists(DB_DIR):
        return ["stamboom"]
    return sorted(f[:-3] for f in os.listdir(DB_DIR) if f.endswith(".db"))


def get_db(actief_db: Optional[str] = Cookie(default=None)):
    db_name = _valid_db_name(actief_db)
    engine = get_engine_for(db_name)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()
