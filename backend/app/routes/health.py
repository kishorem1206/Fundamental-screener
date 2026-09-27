from fastapi import APIRouter
from app.infrastructure.database.client import check_database_health

router = APIRouter()


@router.get("/health")
def health():
    db_health = check_database_health()
    return {"status": "ok", "database": db_health}
