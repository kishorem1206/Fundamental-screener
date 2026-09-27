"""Shared pytest fixtures for backend/tests.

This is the first pytest suite in this codebase (pytest has been a
configured-but-unused dev dependency until now). There is no separate test
database — `db` opens a connection against the real dev database, starts a
transaction, and rolls it back at teardown (the standard SQLAlchemy
"join an external transaction" pattern), so tests can freely call
`insert_metric_value`/etc. without leaving any residue, and can also read
real ingested data (P&L history for known companies) for realistic fixtures.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.client import get_engine


@pytest.fixture()
def db() -> Session:
    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
