import json
import re
import httpx
import http.cookiejar
import os

vid = "5MuIMqhT8DM"
cookie_path = "/home/appuser/.cache/yt_cookies.txt"
kwargs = {}
if os.path.isfile(cookie_path):
    jar = http.cookiejar.MozillaCookieJar(cookie_path)
    jar.load(ignore_discard=True, ignore_expires=True)
    cookies = httpx.Cookies()
    for c in jar:
        cookies.set(c.name, (c.value or "").strip(), domain=c.domain, path=c.path)
    kwargs["cookies"] = cookies

watch = f"https://www.youtube.com/watch?v={vid}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en",
}
r = httpx.get(watch, headers=headers, timeout=25, follow_redirects=True, **kwargs)
html = r.text
print("watch status", r.status_code, "len", len(html), "login_required", "LOGIN_REQUIRED" in html)
for pattern in [
    r"var ytInitialPlayerResponse = ({.*?});",
    r"ytInitialPlayerResponse\s*=\s*({.*?});",
]:
    m = re.search(pattern, html)
    if m:
        player = json.loads(m.group(1))
        tracks = (
            player.get("captions", {})
            .get("playerCaptionsTracklistRenderer", {})
            .get("captionTracks", [])
        )
        print("pattern ok tracks", len(tracks), "playability", player.get("playabilityStatus", {}).get("status"))
        if tracks:
            url = tracks[0]["baseUrl"]
            r2 = httpx.get(url + "&fmt=json3", headers=headers, timeout=20, **kwargs)
            print("timedtext", len(r2.text))
        break
else:
    print("no player response found")
