from app.services.youtube_transcript_service import (
    get_innertube_caption_url,
    parse_timedtext_content,
    fetch_youtube_transcript,
)
import httpx

vid = "5MuIMqhT8DM"

url, lang = get_innertube_caption_url(vid, ["en"])
print("innertube_url", lang, len(url))

r = httpx.get(url, timeout=20)
segs = parse_timedtext_content(r.text)
print("server_fetch_segments", len(segs), segs[0] if segs else None)

try:
    s, l = fetch_youtube_transcript(vid, ["en"])
    print("server_ytdlp", len(s), l)
except Exception as e:
    print("server_ytdlp FAIL", type(e).__name__, str(e)[:200])
