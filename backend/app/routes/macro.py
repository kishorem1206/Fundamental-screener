"""Market & Macro page (app/macro/): context only, nothing here feeds a score."""
from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.macro.overview import overview

router = APIRouter(prefix="/api/macro")


@router.get("/overview")
def macro_overview():
    db = get_db()
    try:
        return overview(db)
    finally:
        db.close()
