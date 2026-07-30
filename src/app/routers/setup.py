from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from app.schemas import NvrSetupRequest
from gateway.client import HikvisionClient
from gateway.config import load_config
from gateway.database import get_active_nvr_config, public_config
from gateway.errors import HikvisionError
from gateway.services.setup import SetupService

router = APIRouter()


@router.get("/nvr/status")
def setup_status() -> dict:
    stored_config = get_active_nvr_config()
    if stored_config is None:
        return {
            "ok": True,
            "data": {
                "configured": False,
                "source": "database",
                "setup_required": True,
            },
        }

    reachable = True
    error = ""
    try:
        HikvisionClient(load_config()).get_device_info()
    except HikvisionError as exc:
        reachable = False
        error = str(exc)

    return {
        "ok": True,
        "data": {
            "configured": True,
            "source": "database",
            "reachable": reachable,
            "error": error,
            "config": public_config(stored_config),
        },
    }


def _test_and_save(request: NvrSetupRequest) -> dict:
    try:
        stored_config = SetupService().test_and_save_nvr(
            ip_address=request.ip_address,
            username=request.username,
            password=request.password,
            http_port=request.http_port,
            rtsp_port=request.rtsp_port,
        )
        return {"ok": True, "data": public_config(stored_config)}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc


@router.post("/nvr/setup")
def setup_nvr(request: NvrSetupRequest) -> dict:
    return _test_and_save(request)


@router.get("/nvr/config")
def nvr_config() -> dict:
    stored_config = get_active_nvr_config()
    if stored_config is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "NVR config is not saved in database",
                "setup_required": True,
            },
        )

    return {"ok": True, "data": public_config(stored_config)}


@router.put("/nvr/config/update")
def update_nvr_config(request: NvrSetupRequest) -> dict:
    return _test_and_save(request)


@router.get("/nvr/info")
def nvr_info(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_device_info()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
