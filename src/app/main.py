from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import cameras, health, network, playback, setup, storage, streams
from app.security import require_api_key


def create_app() -> FastAPI:
    application = FastAPI(
        title="Hikvision Gateway",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )
    application.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)

    application.include_router(health.router)

    protected = [Depends(require_api_key)]
    application.include_router(setup.router, dependencies=protected)
    application.include_router(cameras.router, dependencies=protected)
    application.include_router(streams.router, dependencies=protected)
    application.include_router(playback.router, dependencies=protected)
    application.include_router(storage.router, dependencies=protected)
    application.include_router(network.router, dependencies=protected)
    return application


app = create_app()
