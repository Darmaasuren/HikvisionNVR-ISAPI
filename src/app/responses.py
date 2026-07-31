from typing import Any


def success_response(
    message: str,
    *,
    result: Any = None,
    **metadata: Any,
) -> dict[str, Any]:
    messages = {
        "message": message,
        "result": result,
    }
    messages.update(metadata)
    return {
        "success": True,
        "messages": messages,
    }
