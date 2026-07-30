from fastapi import APIRouter, Depends

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from gateway.client import HikvisionClient
from gateway.errors import HikvisionError

router = APIRouter(prefix="/storage")


@router.get("/hdd")
def storage_hdds(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_storage_hdds()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
