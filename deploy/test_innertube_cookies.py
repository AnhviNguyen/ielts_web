import httpx
import os

vid = "5MuIMqhT8DM"
cookie_path = "/home/appuser/.cache/yt_cookies.txt"
print("cookie exists", os.path.isfile(cookie_path), os.path.getsize(cookie_path) if os.path.isfile(cookie_path) else 0)

cookies = {}
if os.path.isfile(cookie_path):
    for line in open(cookie_path, encoding="utf-8", errors="replace"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            cookies[parts[5]] = parts[6]

endpoint = "https://www.youtube.com/youtubei/v1/player"
body = {
    "context": {
        "client": {
            "clientName": "ANDROID",
            "clientVersion": "20.10.38",
            "hl": "en",
            "gl": "US",
        }
    },
    "videoId": vid,
}
headers = {
    "Content-Type": "application/json",
    "User-Agent": "com.google.android.youtube/20.10.38 (Linux; U; Android 14) gzip",
}
r = httpx.post(endpoint, json=body, headers=headers, cookies=cookies, timeout=20)
player = r.json()
tracks = (
    player.get("captions", {})
    .get("playerCaptionsTracklistRenderer", {})
    .get("captionTracks", [])
)
print("playability", player.get("playabilityStatus", {}).get("status"))
print("tracks", len(tracks))
if tracks:
    url = tracks[0]["baseUrl"]
    r2 = httpx.get(url + "&fmt=json3", timeout=20)
    print("timedtext len", len(r2.text))
