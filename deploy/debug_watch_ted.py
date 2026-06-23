import json
import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

def extract_player(html: str):
    for marker in ("var ytInitialPlayerResponse = ", "ytInitialPlayerResponse = "):
        idx = html.find(marker)
        if idx < 0:
            continue
        start = idx + len(marker)
        depth = 0
        for i, ch in enumerate(html[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start : i + 1])
    return None

vid = "5MuIMqhT8DM"
r = httpx.get(
    f"https://www.youtube.com/watch?v={vid}",
    headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
    follow_redirects=True,
    timeout=25,
)
print("status", r.status_code, "len", len(r.text))
pr = extract_player(r.text)
if not pr:
    print("NO_PLAYER")
else:
    ps = pr.get("playabilityStatus", {})
    print("playability", ps.get("status"), ps.get("reason"))
    tracks = (
        pr.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    print("tracks", len(tracks))
    for t in tracks[:3]:
        print(" ", t.get("languageCode"), t.get("kind"))
