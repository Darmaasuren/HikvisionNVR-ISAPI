from pydantic import BaseModel


class ApiResponse(BaseModel):
    ok: bool = True
    data: object | None = None
