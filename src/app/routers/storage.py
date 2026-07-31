from fastapi import APIRouter, Depends

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from app.responses import success_response
from gateway.client import HikvisionClient
from gateway.errors import HikvisionError

router = APIRouter(prefix="/storage")


@router.get("/hdd")
def storage_hdds(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        items = client.get_storage_hdds()
        return success_response(
            "Storage devices retrieved successfully",
            result=items,
            count=len(items),
        )
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
