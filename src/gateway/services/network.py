from typing import Any
from xml.sax.saxutils import escape

from gateway.http import HikvisionHttpClient
from gateway.xml_utils import child_text, find_child, local_name


# get and update NVR network interface configuration
class NetworkService:
    def __init__(self, http: HikvisionHttpClient):
        self.http = http

    def _parse_ip_address(self, ip_address_node) -> dict[str, str]:
        default_gateway = find_child(ip_address_node, "DefaultGateway")
        primary_dns = find_child(ip_address_node, "PrimaryDNS")
        secondary_dns = find_child(ip_address_node, "SecondaryDNS")

        return {
            "ip_version": child_text(ip_address_node, "ipVersion"),
            "addressing_type": child_text(ip_address_node, "addressingType"),
            "ip_address": child_text(ip_address_node, "ipAddress"),
            "subnet_mask": child_text(ip_address_node, "subnetMask"),
            "default_gateway": child_text(default_gateway, "ipAddress") if default_gateway is not None else "",
            "primary_dns": child_text(primary_dns, "ipAddress") if primary_dns is not None else "",
            "secondary_dns": child_text(secondary_dns, "ipAddress") if secondary_dns is not None else "",
        }

    def _parse_response_status(self, root) -> dict[str, str]:
        return {
            "request_url": child_text(root, "requestURL"),
            "status_code": child_text(root, "statusCode"),
            "status_string": child_text(root, "statusString"),
            "sub_status_code": child_text(root, "subStatusCode"),
        }

    def list_interfaces(self) -> list[dict[str, Any]]:
        endpoint = "/ISAPI/System/Network/interfaces"
        response = self.http.get(endpoint)
        root = self.http.parse_xml(response, endpoint)

        interfaces = []

        for interface in root.iter():
            if local_name(interface.tag) != "NetworkInterface":
                continue

            ip_address_node = find_child(interface, "IPAddress")
            link_node = find_child(interface, "Link")

            item = {
                "id": child_text(interface, "id"),
                "mac_address": child_text(interface, "macAddress"),
                "default_connection": child_text(interface, "defaultConnection"),
                "ip_address": {},
                "link": {},
            }

            if ip_address_node is not None:
                item["ip_address"] = self._parse_ip_address(ip_address_node)

            if link_node is not None:
                item["link"] = {
                    "mac_address": child_text(link_node, "MACAddress"),
                    "auto_negotiation": child_text(link_node, "autoNegotiation"),
                    "speed": child_text(link_node, "speed"),
                    "duplex": child_text(link_node, "duplex"),
                    "mtu": child_text(link_node, "MTU"),
                }

            interfaces.append(item)

        return interfaces

    def set_ip_address(
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
        if addressing_type != "static":
            body = f"""<?xml version="1.0" encoding="UTF-8"?>
<IPAddress version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <ipVersion>{escape(ip_version)}</ipVersion>
    <addressingType>{escape(addressing_type)}</addressingType>
</IPAddress>
"""
            endpoint = f"/ISAPI/System/Network/interfaces/{interface_id}/ipAddress"
            response = self.http.put_xml(endpoint, body)
            root = self.http.parse_xml(response, endpoint)
            return self._parse_response_status(root)

        secondary_dns_xml = ""
        if secondary_dns:
            secondary_dns_xml = f"""
    <SecondaryDNS>
        <ipAddress>{escape(secondary_dns)}</ipAddress>
    </SecondaryDNS>"""

        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<IPAddress version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <ipVersion>{escape(ip_version)}</ipVersion>
    <addressingType>{escape(addressing_type)}</addressingType>
    <ipAddress>{escape(ip_address)}</ipAddress>
    <subnetMask>{escape(subnet_mask)}</subnetMask>
    <DefaultGateway>
        <ipAddress>{escape(default_gateway)}</ipAddress>
    </DefaultGateway>
    <PrimaryDNS>
        <ipAddress>{escape(primary_dns)}</ipAddress>
    </PrimaryDNS>{secondary_dns_xml}
</IPAddress>
"""

        endpoint = f"/ISAPI/System/Network/interfaces/{interface_id}/ipAddress"
        response = self.http.put_xml(endpoint, body)
        root = self.http.parse_xml(response, endpoint)
        return self._parse_response_status(root)
