import json
import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
vid = "5MuIMqhT8DM"

for url in [
    f"https://www.youtube.com/watch?v={vid}",
    f"https://www.youtube.com/embed/{vid}",
    f"https://www.youtube-nocookie.com/embed/{vid}",
]:
    r = httpx.get(url, headers={"User-Agent": UA}, follow_redirects=True, timeout=25)
    print(url.split("/")[2], r.status_code, len(r.text))
    for marker in ("var ytInitialPlayerResponse = ", "ytInitialPlayerResponse = "):
        idx = r.text.find(marker)
        if idx >= 0:
            start = idx + len(marker)
            depth = 0
            for i, ch in enumerate(r.text[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        pr = json.loads(r.text[start : i + 1])
                        tr = len(
                            pr.get("captions", {})
                            .get("playerCaptionsTracklistRenderer", {})
                            .get("captionTracks", [])
                        )
                        print("  playability", pr.get("playabilityStatus", {}).get("status"), "tracks", tr)
                        break
            break
    else:
        print("  no player json")
