from pathlib import Path
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gateway.client import HikvisionClient
from gateway.errors import HikvisionError
from gateway.config import NvrConfig, load_config

app = FastAPI(
    title="Hikvision Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)


class ApiResponse(BaseModel):
    ok: bool = True
    data: object | None = None


class DownloadRequest(BaseModel):
    playback_uri: str = Field(..., min_length=1)
    filename: str = Field("recording.mp4", min_length=1)


def get_config() -> NvrConfig:
    return load_config()


def get_client(config: NvrConfig = Depends(get_config)) -> HikvisionClient:
    return HikvisionClient(config)


def handle_hikvision_error(error: HikvisionError) -> HTTPException:
    status_code = 502
    if error.status_code in {401, 403}:
        status_code = 502
    elif error.status_code == 404:
        status_code = 404

    return HTTPException(
        status_code=status_code,
        detail={
            "message": str(error),
            "endpoint": error.endpoint,
            "nvr_status_code": error.status_code,
        },
    )

#services check
@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "hikvision-gateway"}

#NVR info http endpoint
@app.get("/nvr/info")
def nvr_info(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_device_info()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)

#get camera list http endpoint
@app.get("/cameras")
def cameras(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_cameras()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)

#get cameras metadata http endpoint
@app.get("/streaming/channels")
def streaming_channels(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_streaming_channels()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)


#live stream http endpoint
@app.get("/streams")
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
        return {
            "ok": True,
            "data": {
                "camera_id": camera_id,
                "stream_type": stream_type,
                "rtsp_url": rtsp_url,
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)

#playback
@app.get("/playback/search")
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
        raise HTTPException(status_code=400, detail=str(exc))
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)

#download
@app.post("/playback/download")
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
        raise handle_hikvision_error(exc)
