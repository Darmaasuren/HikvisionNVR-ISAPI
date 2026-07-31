from typing import Any

from gateway.http import HikvisionHttpClient
from gateway.xml_utils import child_text, find_child, local_name, to_int


# get NVR storage HDD information
class StorageService:
    def __init__(self, http: HikvisionHttpClient):
        self.http = http

    def _parse_data_modes(self, hdd_node) -> list[dict[str, Any]]:
        data_mode_list = find_child(hdd_node, "DataModeList")
        if data_mode_list is None:
            return []

        data_modes = []
        for data_mode in data_mode_list:
            if local_name(data_mode.tag) != "DataMode":
                continue

            data_modes.append(
                {
                    "type": child_text(data_mode, "type"),
                    "occupancy_rate": to_int(
                        child_text(data_mode, "occupancyRate")
                    ),
                }
            )

        return data_modes

    def _parse_encryption(self, hdd_node) -> dict[str, Any]:
        encryption = find_child(hdd_node, "Encryption")
        if encryption is None:
            return {}

        password_len = find_child(encryption, "passwordLen")

        return {
            "password_min_length": to_int(password_len.get("min", ""))
            if password_len is not None
            else None,
            "password_max_length": to_int(password_len.get("max", ""))
            if password_len is not None
            else None,
            "encryption_status": child_text(encryption, "encryptionStatus"),
            "encrypt_format_type": child_text(encryption, "encryptFormatType"),
        }

    def _parse_hdd(self, hdd_node) -> dict[str, Any]:
        return {
            "id": child_text(hdd_node, "id"),
            "name": child_text(hdd_node, "hddName"),
            "path": child_text(hdd_node, "hddPath"),
            "type": child_text(hdd_node, "hddType"),
            "status": child_text(hdd_node, "status"),
            "capacity_mb": to_int(child_text(hdd_node, "capacity")),
            "free_space_mb": to_int(child_text(hdd_node, "freeSpace")),
            "property": child_text(hdd_node, "property"),
            "group": to_int(child_text(hdd_node, "group")),
            "format_type": child_text(hdd_node, "formatType"),
            "encryption_status": child_text(hdd_node, "encryptionStatus"),
            "data_modes": self._parse_data_modes(hdd_node),
            "encryption": self._parse_encryption(hdd_node),
        }

    def list_hdds(self) -> list[dict[str, Any]]:
        endpoint = "/ISAPI/ContentMgmt/Storage/hdd"
        response = self.http.get(endpoint)
        root = self.http.parse_xml(response, endpoint)

        hdds = []
        for hdd_node in root.iter():
            if local_name(hdd_node.tag) == "hdd":
                hdds.append(self._parse_hdd(hdd_node))

        return hdds
