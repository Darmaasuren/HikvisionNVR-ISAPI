from dataclasses import dataclass
import os

from dotenv import load_dotenv

from gateway.database import get_active_nvr_config

load_dotenv()


class ConfigNotConfiguredError(RuntimeError):
    pass


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
    stored_config = get_active_nvr_config()
    if stored_config is not None:
        return NvrConfig(
            nvr_ip=stored_config.ip_address,
            nvr_username=stored_config.username,
            nvr_password=stored_config.password,
            nvr_http_port=stored_config.http_port,
            nvr_rtsp_port=stored_config.rtsp_port,
            request_timeout_seconds=float(os.getenv("NVR_REQUEST_TIMEOUT_SECONDS") or "10.0"),
        )

    raise ConfigNotConfiguredError("NVR config is not configured")
