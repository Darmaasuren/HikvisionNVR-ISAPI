from fastapi import Depends, HTTPException

from gateway.client import HikvisionClient
from gateway.config import ConfigNotConfiguredError, NvrConfig, load_config


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
