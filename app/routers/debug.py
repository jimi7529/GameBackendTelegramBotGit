import os
from fastapi import APIRouter

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/db-path")
def get_db_path():
    return {"DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./game.db")}
