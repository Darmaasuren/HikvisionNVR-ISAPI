from fastapi import APIRouter

from app.responses import success_response


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return success_response(
        "Service is healthy",
        result={"service": "hikvision-gateway"},
    )
