from fastapi import APIRouter


router = APIRouter()


@router.get("/test-db")
def test_db():
    return {"status": "db ok"}
