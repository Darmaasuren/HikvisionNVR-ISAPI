from gateway.config import NvrConfig
from gateway.database import StoredNvrConfig, save_active_nvr_config
from gateway.http import HikvisionHttpClient
from gateway.services.device import DeviceService


class SetupService:
    def test_and_save_nvr(
        self,
        *,
        ip_address: str,
        username: str,
        password: str,
        http_port: int = 80,
        rtsp_port: int = 554,
    ) -> StoredNvrConfig:
        config = NvrConfig(
            nvr_ip=ip_address,
            nvr_username=username,
            nvr_password=password,
            nvr_http_port=http_port,
            nvr_rtsp_port=rtsp_port,
        )
        device_info = DeviceService(HikvisionHttpClient(config)).get_info()

        return save_active_nvr_config(
            ip_address=ip_address,
            username=username,
            password=password,
            http_port=http_port,
            rtsp_port=rtsp_port,
            serial_number=device_info.get("serialNumber", ""),
            device_name=device_info.get("deviceName", ""),
            model=device_info.get("model", ""),
        )
