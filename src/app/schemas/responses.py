from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    messages: dict[str, Any]
