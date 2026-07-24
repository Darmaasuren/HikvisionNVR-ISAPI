from datetime import datetime, timezone
from typing import Any
from xml.sax.saxutils import escape
import uuid

from gateway.http import HikvisionHttpClient
from gateway.services.cameras import CameraService
from gateway.xml_utils import find_text, local_name


class PlaybackService:
    def __init__(self, http: HikvisionHttpClient, cameras: CameraService):
        self.http = http
        self.cameras = cameras

    def hikvision_time(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return value.isoformat()

    #use start and end time between search video
    def search(
        self,
        camera_id: str | int,
        start_time: datetime,
        end_time: datetime,
        stream_type: str = "main",
        *,
        max_results: int = 40,
        position: int = 0,
    ) -> dict[str, Any]:
        start_time_text = self.hikvision_time(start_time)
        end_time_text = self.hikvision_time(end_time)

        if datetime.fromisoformat(start_time_text) >= datetime.fromisoformat(end_time_text):
            raise ValueError("start_time must be before end_time")

        track_id = self.cameras.build_track_id(camera_id, stream_type)
        search_id = str(uuid.uuid4())

        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<CMSearchDescription>
    <searchID>{search_id}</searchID>
    <trackIDList>
        <trackID>{track_id}</trackID>
    </trackIDList>
    <timeSpanList>
        <timeSpan>
            <startTime>{escape(start_time_text)}</startTime>
            <endTime>{escape(end_time_text)}</endTime>
        </timeSpan>
    </timeSpanList>
    <maxResults>{max_results}</maxResults>
    <searchResultPosition>{position}</searchResultPosition>
    <metadataList>
        <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
    </metadataList>
</CMSearchDescription>
"""
        endpoint = "/ISAPI/ContentMgmt/search"
        response = self.http.post_xml(endpoint, body)
        root = self.http.parse_xml(response, endpoint)

        records = []

        for item in root.iter():
            if local_name(item.tag) not in {"searchMatchItem", "CMSearchResultItem"}:
                continue

            records.append({
                "track_id": find_text(item, "trackID"),
                "start_time": find_text(item, "startTime"),
                "end_time": find_text(item, "endTime"),
                "playback_uri": find_text(item, "playbackURI"),
            })

        return {
            "search_id": search_id,
            "track_id": track_id,
            "position": position,
            "max_results": max_results,
            "count": len(records),
            "records": records,
        }
