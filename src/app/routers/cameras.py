from fastapi import APIRouter, Depends

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from gateway.client import HikvisionClient
from gateway.errors import HikvisionError

router = APIRouter()


@router.get("/cameras")
def cameras(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_cameras()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
