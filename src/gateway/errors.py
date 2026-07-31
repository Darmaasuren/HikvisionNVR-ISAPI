class HikvisionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "NVR_REQUEST_FAILED",
        status_code: int | None = None,
        endpoint: str = "",
        nvr_status_code: str = "",
        nvr_status_string: str = "",
        nvr_sub_status_code: str = "",
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.endpoint = endpoint
        self.nvr_status_code = nvr_status_code
        self.nvr_status_string = nvr_status_string
        self.nvr_sub_status_code = nvr_sub_status_code
