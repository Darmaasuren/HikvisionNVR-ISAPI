from pathlib import Path
from xml.sax.saxutils import escape

from gateway.config import NvrConfig
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

        response = self.http.post_xml(
            "/ISAPI/ContentMgmt/download",
            body,
            timeout=120,
            stream=True,
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

        return path
