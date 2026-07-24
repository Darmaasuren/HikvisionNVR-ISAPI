import xml.etree.ElementTree as ET

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth
from urllib3.util.retry import Retry

from gateway.config import NvrConfig
from gateway.errors import HikvisionError


class HikvisionHttpClient:
    def __init__(self, config: NvrConfig):
        self.config = config
        self.auth = HTTPDigestAuth(config.nvr_username, config.nvr_password)
        self.session = self._build_session()

    def _build_session(self) -> Session:
        session = requests.Session()
        retry = Retry(
            total=2,
            connect=2,
            read=1,
            backoff_factor=0.3,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset({"GET", "POST", "PUT"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def url(self, path: str) -> str:
        return f"{self.config.nvr_base_url}{path}"

    def _raise_for_bad_response(self, response: Response, endpoint: str) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise HikvisionError(
                f"Hikvision request failed: HTTP {response.status_code}",
                status_code=response.status_code,
                endpoint=endpoint,
            ) from exc

#
    def get(self, path: str) -> Response:
        try:
            response = self.session.get(
                self.url(path),
                auth=self.auth,
                timeout=self.config.request_timeout_seconds,
            )
        except requests.RequestException as exc:
            raise HikvisionError(f"Hikvision GET failed: {path}", endpoint=path) from exc

        self._raise_for_bad_response(response, path)
        return response

    def post_xml(
        self,
        path: str,
        body: str,
        *,
        timeout: float | None = None,
        stream: bool = False,
    ) -> Response:
        try:
            response = self.session.post(
                self.url(path),
                data=body.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                auth=self.auth,
                timeout=timeout or self.config.request_timeout_seconds,
                stream=stream,
            )
        except requests.RequestException as exc:
            raise HikvisionError(f"Hikvision POST failed: {path}", endpoint=path) from exc

        self._raise_for_bad_response(response, path)
        return response

    def put_xml(
        self,
        path: str,
        body: str,
        *,
        timeout: float | None = None,
    ) -> Response:
        try:
            response = self.session.put(
                self.url(path),
                data=body.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                auth=self.auth,
                timeout=timeout or self.config.request_timeout_seconds,
            )
        except requests.RequestException as exc:
            raise HikvisionError(f"Hikvision PUT failed: {path}", endpoint=path) from exc

        self._raise_for_bad_response(response, path)
        return response

    def parse_xml(self, response: Response, endpoint: str) -> ET.Element:
        try:
            return ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise HikvisionError(
                "Hikvision returned invalid XML",
                status_code=response.status_code,
                endpoint=endpoint,
            ) from exc
