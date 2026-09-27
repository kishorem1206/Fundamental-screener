from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import config
from app.logger import logger

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.database_url,
            pool_size=config.database_pool_min,
            max_overflow=config.database_pool_max - config.database_pool_min,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _session_factory


def get_db() -> Session:
    return get_session_factory()()


def check_database_health() -> dict:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def close_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
