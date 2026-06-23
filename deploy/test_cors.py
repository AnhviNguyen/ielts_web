import httpx

r = httpx.options(
    "https://www.youtube.com/youtubei/v1/player",
    headers={
        "Origin": "https://linguaielts.site",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    },
    timeout=15,
)
print("OPTIONS", r.status_code)
for k, v in r.headers.items():
    if "access-control" in k.lower():
        print(k, v)

r2 = httpx.post(
    "https://www.youtube.com/youtubei/v1/player",
    json={
        "context": {"client": {"clientName": "ANDROID", "clientVersion": "20.10.38"}},
        "videoId": "5MuIMqhT8DM",
    },
    headers={"Origin": "https://linguaielts.site", "Content-Type": "application/json"},
    timeout=15,
)
print("POST", r2.status_code)
for k, v in r2.headers.items():
    if "access-control" in k.lower():
        print(k, v)
tracks = (
    r2.json().get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
)
print("tracks", len(tracks))
