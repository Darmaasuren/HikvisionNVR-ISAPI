from fastapi import APIRouter, Depends

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from app.responses import success_response
from gateway.client import HikvisionClient
from gateway.errors import HikvisionError

router = APIRouter()


@router.get("/cameras")
def cameras(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        items = client.get_cameras()
        return success_response(
            "Cameras retrieved successfully",
            result=items,
            count=len(items),
        )
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
