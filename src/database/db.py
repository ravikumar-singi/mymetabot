from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import config
from src.database.models import Base
from src.logger import get_logger

log = get_logger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
            echo=False,
        )
    return _engine


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    log.info("Database initialized.")


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal()
