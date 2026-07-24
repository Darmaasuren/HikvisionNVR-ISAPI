from pathlib import Path
from datetime import datetime

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gateway.client import HikvisionClient
from gateway.errors import HikvisionError
from gateway.config import ConfigNotConfiguredError, NvrConfig, load_config
from gateway.database import (
    get_active_nvr_config,
    public_config,
    save_active_nvr_config,
    update_active_nvr_ip,
)
from gateway.services.setup import SetupService

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


class NetworkAddressRequest(BaseModel):
    ip_address: str = Field(
        "",
        description="New NVR IP address. Leave empty to keep the current value.",
    )
    subnet_mask: str = Field(
        "",
        description="Subnet mask. Leave empty to keep the current value.",
    )
    default_gateway: str = Field(
        "",
        description="Default gateway. Leave empty to keep the current value.",
    )
    primary_dns: str = Field(
        "",
        description="Primary DNS. Leave empty to keep the current value.",
    )
    secondary_dns: str = Field(
        "",
        description="Secondary DNS. Leave empty to keep the current value.",
    )
    addressing_type: str = Field("static", pattern="^(static|dynamic|apipa)$")
    ip_version: str = Field("v4", pattern="^(v4|v6|dual)$")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ip_address": "",
                    "subnet_mask": "",
                    "default_gateway": "",
                    "primary_dns": "",
                    "secondary_dns": "",
                    "addressing_type": "static",
                    "ip_version": "v4",
                }
            ]
        }
    }


class NvrSetupRequest(BaseModel):
    ip_address: str = Field(..., min_length=1)
    username: str = Field("admin", min_length=1)
    password: str = ""
    http_port: int = Field(80, ge=1, le=65535)
    rtsp_port: int = Field(554, ge=1, le=65535)


def get_config() -> NvrConfig:
    try:
        return load_config()
    except ConfigNotConfiguredError as exc:
        raise HTTPException(
            status_code=428,
            detail={
                "message": str(exc),
                "setup_required": True,
            },
        ) from exc


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


def get_interface_ip_config(client: HikvisionClient, interface_id: str) -> dict:
    interfaces = client.get_network_interfaces()
    interface = next(
        (item for item in interfaces if str(item.get("id")) == str(interface_id)),
        None,
    )

    if interface is None:
        raise HTTPException(
            status_code=404,
            detail=f"Network interface {interface_id} was not found",
        )

    ip_config = interface.get("ip_address") or {}
    if not ip_config:
        raise HTTPException(
            status_code=404,
            detail=f"Network interface {interface_id} has no IP configuration",
        )

    return ip_config


#services check
@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "hikvision-gateway"}


#check active NVR setup status
@app.get("/nvr/status")
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
    except Exception as exc:
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


#register or update active NVR config
@app.post("/nvr/setup")
def setup_nvr(request: NvrSetupRequest) -> dict:
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
        raise handle_hikvision_error(exc)


#get active NVR config without password
@app.get("/nvr/config")
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


#update active NVR config manually
@app.put("/nvr/config/update")
def update_nvr_config(request: NvrSetupRequest) -> dict:
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
        raise handle_hikvision_error(exc)


#NVR info http endpoint
@app.get("/nvr/info")
def nvr_info(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_device_info()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)


#get NVR storage HDD list
@app.get("/storage/hdd")
def storage_hdds(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_storage_hdds()}
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


#get NVR network interfaces
@app.get("/network/interfaces")
def network_interfaces(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        return {"ok": True, "data": client.get_network_interfaces()}
    except HikvisionError as exc:
        raise handle_hikvision_error(exc)


#set NVR network interface IP config
@app.put("/network/interfaces/{interface_id}/ip-address")
def set_network_interface_ip_address(
    interface_id: str,
    request: NetworkAddressRequest = Body(
        ...,
        examples=[
            {
                "ip_address": "",
                "subnet_mask": "",
                "default_gateway": "",
                "primary_dns": "",
                "secondary_dns": "",
                "addressing_type": "static",
                "ip_version": "v4",
            }
        ],
    ),
    config: NvrConfig = Depends(get_config),
    client: HikvisionClient = Depends(get_client),
) -> dict:
    try:
        current_ip_config = get_interface_ip_config(client, interface_id)
        ip_address = request.ip_address or current_ip_config.get("ip_address")
        subnet_mask = request.subnet_mask or current_ip_config.get("subnet_mask")
        default_gateway = request.default_gateway or current_ip_config.get("default_gateway")
        primary_dns = request.primary_dns or current_ip_config.get("primary_dns")
        secondary_dns = request.secondary_dns or current_ip_config.get("secondary_dns", "")
        missing_fields = [
            field_name
            for field_name, value in {
                "ip_address": ip_address,
                "subnet_mask": subnet_mask,
                "default_gateway": default_gateway,
                "primary_dns": primary_dns,
            }.items()
            if not value
        ]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Missing required network values",
                    "missing_fields": missing_fields,
                },
            )

        data = client.set_interface_ip_address(
            interface_id,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            default_gateway=default_gateway,
            primary_dns=primary_dns,
            secondary_dns=secondary_dns or "",
            addressing_type=request.addressing_type,
            ip_version=request.ip_version,
        )
        if request.addressing_type == "static":
            updated = update_active_nvr_ip(ip_address)
            if not updated:
                save_active_nvr_config(
                    ip_address=ip_address,
                    username=config.nvr_username,
                    password=config.nvr_password,
                    http_port=config.nvr_http_port,
                    rtsp_port=config.nvr_rtsp_port,
                )
        return {"ok": True, "data": data}
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
