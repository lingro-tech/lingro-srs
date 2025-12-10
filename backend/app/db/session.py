from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings
from .base import Base


def _build_engine():
    engine_kwargs = {"pool_pre_ping": True}
    if settings.DATABASE_URL.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(settings.DATABASE_URL, **engine_kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_models() -> None:
    """Create database tables for all models."""
    from .. import models  # noqa: F401  # ensure model metadata is loaded

    Base.metadata.create_all(bind=engine)
