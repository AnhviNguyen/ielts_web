import httpx
from app.services.youtube_transcript_service import parse_timedtext_content

url = open("/app/caption_url.txt", encoding="utf-8").read().strip()
for label, headers in [
    ("plain", {}),
    ("origin", {"Origin": "https://linguaielts.site"}),
    ("referer", {"Referer": "https://www.youtube.com/watch?v=5MuIMqhT8DM"}),
]:
    r = httpx.get(url, headers=headers, timeout=20)
    segs = parse_timedtext_content(r.text)
    print(label, "status", r.status_code, "len", len(r.text), "segs", len(segs))
