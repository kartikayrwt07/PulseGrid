from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base."""


def _build_engine():
    settings = get_settings()
    url = settings.DATABASE_URL
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {"echo": False, "future": True}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        engine_kwargs.update({"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10})

    eng = create_engine(url, connect_args=connect_args, **engine_kwargs)

    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def _set_sqlite_pragmas(dbapi_conn: Any, _connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

    return eng


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a scoped SQLAlchemy session and close cleanly."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
