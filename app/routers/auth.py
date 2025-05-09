from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Example endpoint (you can remove later)
@router.get("/ping")
def ping():
    return {"msg": "auth router ready"}
