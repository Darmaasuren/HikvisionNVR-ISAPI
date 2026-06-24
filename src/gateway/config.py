from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()

#Get config NVR
@dataclass(frozen=True)
class NvrConfig:
    nvr_ip: str
    nvr_username: str
    nvr_password: str
    nvr_http_port: int = 80
    nvr_rtsp_port: int = 554
    request_timeout_seconds: float = 10.0

    @property
    def nvr_base_url(self) -> str:
        return f"http://{self.nvr_ip}:{self.nvr_http_port}"


def load_config() -> NvrConfig:
    config = NvrConfig(
        nvr_ip=os.getenv("NVR_IP", "").strip(),
        nvr_username=(os.getenv("NVR_USERNAME") or "admin").strip(),
        nvr_password=(os.getenv("NVR_PASSWORD") or "").strip(),
        nvr_http_port=int(os.getenv("NVR_HTTP_PORT") or "80"),
        nvr_rtsp_port=int(os.getenv("NVR_RTSP_PORT") or "554"),
        request_timeout_seconds=float(os.getenv("NVR_REQUEST_TIMEOUT_SECONDS") or "10.0"),
    )

    if not config.nvr_ip:
        raise RuntimeError("Missing required environment variable: NVR_IP")

    # if not config.nvr_password:
    #     raise RuntimeError("Missing required environment variable: NVR_PASSWORD")

    return config
