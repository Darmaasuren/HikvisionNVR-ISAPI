import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


API_KEY_ENV_NAME = "API_KEY"

api_key_header = APIKeyHeader(
    name="API-Key",
    scheme_name="ApiKeyAuth",
    description="Hikvision Gateway API key",
    auto_error=False,
)


def require_api_key(
    provided_key: str | None = Security(api_key_header),
) -> None:
    expected_key = os.environ.get(API_KEY_ENV_NAME)
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if provided_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
