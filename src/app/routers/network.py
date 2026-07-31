from fastapi import APIRouter, Body, Depends, HTTPException

from app.dependencies import get_client, get_config
from app.exception_handlers import handle_hikvision_error
from app.responses import success_response
from app.schemas import NetworkAddressRequest
from gateway.client import HikvisionClient
from gateway.config import NvrConfig
from gateway.database import save_active_nvr_config, update_active_nvr_ip
from gateway.errors import HikvisionError

router = APIRouter(prefix="/network")


def get_interface_ip_config(client: HikvisionClient, interface_id: str) -> dict:
    interfaces = client.get_network_interfaces()
    interface = next(
        (item for item in interfaces if str(item.get("id")) == str(interface_id)),
        None,
    )
    if interface is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NETWORK_INTERFACE_NOT_FOUND",
                "message": f"Network interface {interface_id} was not found",
            },
        )

    ip_config = interface.get("ip_address") or {}
    if not ip_config:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NETWORK_IP_CONFIG_NOT_FOUND",
                "message": f"Network interface {interface_id} has no IP configuration",
            },
        )
    return ip_config


@router.get("/interfaces")
def network_interfaces(client: HikvisionClient = Depends(get_client)) -> dict:
    try:
        items = client.get_network_interfaces()
        return success_response(
            "Network interfaces retrieved successfully",
            result=items,
            count=len(items),
        )
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc


@router.put("/interfaces/{interface_id}/ip-address")
def set_network_interface_ip_address(
    interface_id: str,
    request: NetworkAddressRequest = Body(...),
    config: NvrConfig = Depends(get_config),
    client: HikvisionClient = Depends(get_client),
) -> dict:
    try:
        values = {
            "ip_address": "",
            "subnet_mask": "",
            "default_gateway": "",
            "primary_dns": "",
            "secondary_dns": "",
        }
        if request.addressing_type == "static":
            current = get_interface_ip_config(client, interface_id)
            values = {
                "ip_address": request.ip_address or current.get("ip_address"),
                "subnet_mask": request.subnet_mask or current.get("subnet_mask"),
                "default_gateway": request.default_gateway or current.get("default_gateway"),
                "primary_dns": request.primary_dns or current.get("primary_dns"),
                "secondary_dns": request.secondary_dns
                or current.get("secondary_dns", ""),
            }
            missing_fields = [
                name
                for name in (
                    "ip_address",
                    "subnet_mask",
                    "default_gateway",
                    "primary_dns",
                )
                if not values[name]
            ]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "MISSING_STATIC_NETWORK_VALUES",
                        "message": "Missing required static network values",
                        "missing_fields": missing_fields,
                    },
                )

        data = client.set_interface_ip_address(
            interface_id,
            **values,
            addressing_type=request.addressing_type,
            ip_version=request.ip_version,
        )
        if request.addressing_type == "static":
            updated = update_active_nvr_ip(values["ip_address"])
            if not updated:
                save_active_nvr_config(
                    ip_address=values["ip_address"],
                    username=config.nvr_username,
                    password=config.nvr_password,
                    http_port=config.nvr_http_port,
                    rtsp_port=config.nvr_rtsp_port,
                )
        return success_response(
            "Network configuration updated successfully",
            result=data,
        )
    except HikvisionError as exc:
        raise handle_hikvision_error(exc) from exc
