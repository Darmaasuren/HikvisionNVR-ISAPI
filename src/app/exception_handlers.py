import logging

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from gateway.errors import HikvisionError

logger = logging.getLogger(__name__)


def handle_hikvision_error(error: HikvisionError) -> HTTPException:
    status_code = 504 if error.code == "NVR_TIMEOUT" else 502
    details = {
        key: value
        for key, value in {
            "endpoint": error.endpoint,
            "nvr_http_status": error.status_code,
            "nvr_status_code": error.nvr_status_code,
            "nvr_status_string": error.nvr_status_string,
            "nvr_sub_status_code": error.nvr_sub_status_code,
        }.items()
        if value not in {None, ""}
    }

    return HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": str(error),
            "details": details or None,
        },
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    if isinstance(exc.detail, dict):
        detail = dict(exc.detail)
        code = detail.pop("code", f"HTTP_{exc.status_code}")
        message = detail.pop("message", "Request failed")
        explicit_details = detail.pop("details", None)
        details = explicit_details if explicit_details is not None else detail or None
    else:
        code = f"HTTP_{exc.status_code}"
        message = str(exc.detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "messages": {
                "code": code,
                "message": message,
                "details": jsonable_encoder(details),
            },
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "messages": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
            },
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "messages": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
                "details": None,
            },
        },
    )
