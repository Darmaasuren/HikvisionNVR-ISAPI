from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.dependencies import get_client
from app.exception_handlers import handle_hikvision_error
from app.schemas import DownloadRequest
from gateway.client import HikvisionClient
from gateway.errors import HikvisionError

router = APIRouter(prefix="/playback")


@router.get("/search")
def playback_search(
    camera_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    stream_type: str = Query("main", pattern="^(main|sub)$"),
    max_results: int = Query(40, ge=1, le=200),
    position: int = Query(0, ge=0),
    client: HikvisionClient = Depends(get_client),
) -> dict:
    try:
        data = client.search_playback(
            camera_id=camera_id,
            stream_type=stream_type,
            start_time=start_time,
            end_time=end_time,
            max_results=max_results,
            position=position,
        )
        return {"ok": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc


@router.post("/download")
def playback_download(
    request: DownloadRequest,
    client: HikvisionClient = Depends(get_client),
) -> FileResponse:
    try:
        output_path = Path("/tmp/hikvision-downloads") / Path(request.filename).name
        saved_path = client.download_recording(request.playback_uri, output_path)
        return FileResponse(
            saved_path,
            media_type="video/mp4",
            filename=saved_path.name,
        )
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
