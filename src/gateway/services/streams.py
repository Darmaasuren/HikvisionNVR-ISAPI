from urllib.parse import urlsplit, urlunsplit

from gateway.config import NvrConfig
from gateway.http import HikvisionHttpClient
from gateway.services.cameras import CameraService
from gateway.xml_utils import child_text, local_name


#get live stream 
class StreamService:
    def __init__(
        self,
        config: NvrConfig,
        http: HikvisionHttpClient,
        cameras: CameraService,
    ):
        self.config = config
        self.http = http
        self.cameras = cameras

    def build_rtsp_url_by_track_id(
        self,
        track_id: str,
        *,
        include_password: bool = False,
    ) -> str:
        password = self.config.nvr_password if include_password else "<password>"
        return (
            f"rtsp://{self.config.nvr_username}:{password}"
            f"@{self.config.nvr_ip}:{self.config.nvr_rtsp_port}"
            f"/Streaming/channels/{track_id}"
        )

#use camera id (channels) and stream type to build rtsp url
    def build_live_url(
        self,
        camera_id: str | int,
        stream_type: str = "main",
        *,
        include_password: bool = False,
    ) -> str:
        camera_id = str(camera_id)

        cameras = self.cameras.list()
        camera = next(
            (item for item in cameras if str(item.get("id")) == camera_id),
            None,
        )

        if camera is None:
            raise ValueError(f"Camera id {camera_id} was not found")

        track_id = camera["main_track_id"] if stream_type == "main" else camera["sub_track_id"]

        return self.build_rtsp_url_by_track_id(
            track_id,
            include_password=include_password,
        )

    def list_channels(self) -> list[dict[str, str]]:
        endpoint = "/ISAPI/Streaming/channels"
        response = self.http.get(endpoint)
        root = self.http.parse_xml(response, endpoint)

        channels = []

        for channel in root.iter():
            if local_name(channel.tag) != "StreamingChannel":
                continue

            channel_id = child_text(channel, "id")
            channels.append({
                "id": channel_id,
                "name": child_text(channel, "channelName"),
                "enabled": child_text(channel, "enabled"),
                "transport_protocol": child_text(channel, "transportProtocol"),
                "video_codec": child_text(channel, "videoCodecType"),
                "resolution": (
                    f"{child_text(channel, 'videoResolutionWidth')}"
                    f"{child_text(channel, 'videoResolutionHeight')}"
                ),
                "rtsp_url": self.build_rtsp_url_by_track_id(
                    channel_id,
                    include_password=False,
                ),
            })

        return channels

    def add_rtsp_credentials(self, rtsp_url: str) -> str:
        parsed = urlsplit(rtsp_url)
        if "@" in parsed.netloc:
            return rtsp_url

        host = parsed.netloc or f"{self.config.nvr_ip}:{self.config.nvr_rtsp_port}"
        netloc = f"{self.config.nvr_username}:{self.config.nvr_password}@{host}"
        return urlunsplit((parsed.scheme or "rtsp", netloc, parsed.path, parsed.query, parsed.fragment))