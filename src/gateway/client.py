from pathlib import Path
from datetime import datetime
from typing import Any

from gateway.config import NvrConfig
from gateway.http import HikvisionHttpClient
from gateway.services.cameras import CameraService
from gateway.services.device import DeviceService
from gateway.services.download import DownloadService
from gateway.services.network import NetworkService
from gateway.services.playback import PlaybackService
from gateway.services.storage import StorageService
from gateway.services.streams import StreamService


class HikvisionClient:
    def __init__(self, config: NvrConfig):
        self.config = config
        self.http = HikvisionHttpClient(config)

        self.device = DeviceService(self.http)
        self.cameras = CameraService(self.http)
        self.streams = StreamService(config, self.http, self.cameras)
        self.playback = PlaybackService(self.http, self.cameras)
        self.download = DownloadService(config, self.http)
        self.network = NetworkService(self.http)
        self.storage = StorageService(self.http)

    def get_device_info(self) -> dict[str, str]:
        return self.device.get_info()

    def get_cameras(self) -> list[dict[str, str]]:
        return self.cameras.list()

    def get_streaming_channels(self) -> list[dict[str, str]]:
        return self.streams.list_channels()

    def build_live_rtsp_url(
        self,
        camera_id: str | int,
        stream_type: str = "main",
        *,
        include_password: bool = False,
    ) -> str:
        return self.streams.build_live_url(
            camera_id,
            stream_type,
            include_password=include_password,
        )

    def search_playback(
        self,
        camera_id: str | int,
        start_time: datetime,
        end_time: datetime,
        stream_type: str = "main",
        *,
        max_results: int = 40,
        position: int = 0,
    ) -> dict[str, Any]:
        return self.playback.search(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            stream_type=stream_type,
            max_results=max_results,
            position=position,
        )

    def download_recording(self, playback_uri: str, output_path: str | Path) -> Path:
        return self.download.download_recording(playback_uri, output_path)

    def get_network_interfaces(self) -> list[dict[str, Any]]:
        return self.network.list_interfaces()

    def get_storage_hdds(self) -> list[dict[str, Any]]:
        return self.storage.list_hdds()

    def set_interface_ip_address(
        self,
        interface_id: str | int,
        *,
        ip_address: str,
        subnet_mask: str,
        default_gateway: str,
        primary_dns: str,
        secondary_dns: str = "",
        addressing_type: str = "static",
        ip_version: str = "v4",
    ) -> dict[str, str]:
        return self.network.set_ip_address(
            interface_id,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            default_gateway=default_gateway,
            primary_dns=primary_dns,
            secondary_dns=secondary_dns,
            addressing_type=addressing_type,
            ip_version=ip_version,
        )
