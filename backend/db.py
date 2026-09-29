from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./lab.db")
engine = create_engine(DATABASE_URL, future=True,
                       connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _sqlite_fk_on(dbapi_conn, _):          # match PostgreSQL: enforce foreign keys in tests too
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass
