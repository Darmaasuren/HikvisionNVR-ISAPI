from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from app.responses import success_response
from gateway.client import HikvisionClient
from gateway.errors import HikvisionError

router = APIRouter()


@router.get("/streaming/channels")
def streaming_channels(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        items = client.get_streaming_channels()
        return success_response(
            "Streaming channels retrieved successfully",
            result=items,
            count=len(items),
        )
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc


@router.get("/streams")
def live_stream_url(
    camera_id: str = Query(...),
    stream_type: str = Query("main", pattern="^(main|sub)$"),
    include_password: bool = Query(False),
    client: HikvisionClient = Depends(get_client),
) -> dict:
    try:
        rtsp_url = client.build_live_rtsp_url(
            camera_id,
            stream_type,
            include_password=include_password,
        )
        return success_response(
            "Live stream URL created successfully",
            result={
                "camera_id": camera_id,
                "stream_type": stream_type,
                "rtsp_url": rtsp_url,
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CAMERA_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
