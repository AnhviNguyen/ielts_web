import json
import httpx

vid = "5MuIMqhT8DM"
clients = [
    {"clientName": "ANDROID", "clientVersion": "20.10.38", "hl": "en", "gl": "US"},
    {"clientName": "IOS", "clientVersion": "20.10.38", "hl": "en", "gl": "US"},
    {"clientName": "TVHTML5", "clientVersion": "7.20240101.00.00", "hl": "en", "gl": "US"},
    {"clientName": "WEB", "clientVersion": "2.20260618.05.00", "hl": "en", "gl": "US"},
]
endpoint = "https://www.youtube.com/youtubei/v1/player"
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
}

for client in clients:
    body = {"context": {"client": client}, "videoId": vid}
    url = endpoint
    if client["clientName"] == "WEB":
        url += "?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    try:
        r = httpx.post(url, json=body, headers=headers, timeout=20)
        player = r.json()
        tracks = (
            player.get("captions", {})
            .get("playerCaptionsTracklistRenderer", {})
            .get("captionTracks", [])
        )
        status = player.get("playabilityStatus", {}).get("status")
        print(client["clientName"], "status", r.status_code, "playability", status, "tracks", len(tracks))
    except Exception as e:
        print(client["clientName"], "ERR", e)
