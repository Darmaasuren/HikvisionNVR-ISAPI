from gateway.http import HikvisionHttpClient
from gateway.xml_utils import local_name

#get NVR info 
class DeviceService:
    def __init__(self, http: HikvisionHttpClient):
        self.http = http

    def get_info(self) -> dict[str, str]:
        endpoint = "/ISAPI/System/deviceInfo"
        response = self.http.get(endpoint)
        root = self.http.parse_xml(response, endpoint)

        info = {}

        for elem in root.iter():
            key = local_name(elem.tag)
            value = elem.text.strip() if elem.text else ""
            info[key] = value

        return info