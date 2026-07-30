from fastapi import HTTPException

from gateway.errors import HikvisionError


def handle_hikvision_error(error: HikvisionError) -> HTTPException:
    status_code = 404 if error.status_code == 404 else 502

    return HTTPException(
        status_code=status_code,
        detail={
            "message": str(error),
            "endpoint": error.endpoint,
            "nvr_status_code": error.status_code,
        },
    )
