"""Test Apify YouTube transcript actor (reads APIFY_API_TOKEN from settings)."""
from app.services.youtube_transcript_service import (
    _fetch_transcript_via_apify,
    cookies_debug_info,
)

print("debug", {k: cookies_debug_info().get(k) for k in ("has_supadata", "has_apify")})
for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ"]:
    s, l = _fetch_transcript_via_apify(vid)
    print(vid, len(s), l, s[0] if s else None)
