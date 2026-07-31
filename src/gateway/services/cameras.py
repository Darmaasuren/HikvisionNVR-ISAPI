from typing import Any

from gateway.http import HikvisionHttpClient
from gateway.xml_utils import child_text, find_child, local_name, to_int


#get cameras list in NVR
class CameraService:
    def __init__(self, http: HikvisionHttpClient):
        self.http = http

    def build_track_id(self, camera_id: str | int, stream_type: str = "main") -> str:
        if stream_type not in {"main", "sub"}:
            raise ValueError("stream_type must be 'main' or 'sub'")

        suffix = "01" if stream_type == "main" else "02"
        return f"{camera_id}{suffix}"

    def list(self) -> list[dict[str, Any]]:
        endpoint = "/ISAPI/ContentMgmt/InputProxy/channels"
        response = self.http.get(endpoint)
        root = self.http.parse_xml(response, endpoint)

        cameras = []

        for channel in root.iter():
            if local_name(channel.tag) != "InputProxyChannel":
                continue

            camera_id = child_text(channel, "id")
            source = find_child(channel, "sourceInputPortDescriptor")

            camera = {
                "id": camera_id,
                "name": child_text(channel, "name"),
                "dev_index": to_int(child_text(channel, "devIndex")),
                "main_track_id": self.build_track_id(camera_id, "main"),
                "sub_track_id": self.build_track_id(camera_id, "sub"),
                "ip_address": "",
                "manage_port": None,
                "protocol": "",
                "username": "",
                "model": "",
                "serial_number": "",
                "firmware_version": "",
            }

            if source is not None:
                camera.update({
                    "ip_address": child_text(source, "ipAddress"),
                    "manage_port": to_int(child_text(source, "managePortNo")),
                    "protocol": child_text(source, "proxyProtocol"),
                    "username": child_text(source, "userName"),
                    "model": child_text(source, "model"),
                    "serial_number": child_text(source, "serialNumber"),
                    "firmware_version": child_text(source, "firmwareVersion"),
                })

            cameras.append(camera)

        return cameras
