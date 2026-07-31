from pathlib import Path
from xml.sax.saxutils import escape

from gateway.config import DOWNLOAD_TIMEOUT_SECONDS, NvrConfig
from gateway.http import HikvisionHttpClient


#use playback uri to download video
class DownloadService:
    def __init__(self, config: NvrConfig, http: HikvisionHttpClient):
        self.config = config
        self.http = http

    def download_recording(self, playback_uri: str, output_path: str | Path) -> Path:
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<downloadRequest>
    <playbackURI>{escape(playback_uri)}</playbackURI>
</downloadRequest>
"""

        endpoint = "/ISAPI/ContentMgmt/download"
        response = self.http.post_xml(
            endpoint,
            body,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            stream=True,
        )
        content_type = response.headers.get("Content-Type", "").lower()
        if "xml" in content_type:
            self.http.parse_xml(response, endpoint)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

        return path
