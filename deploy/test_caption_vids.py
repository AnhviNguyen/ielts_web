#!/usr/bin/env python3
"""Quick test caption resolution on VPS."""
from app.services.youtube_transcript_service import get_innertube_caption_url

for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ", "jNQXAC9IVRw"]:
    try:
        url, lang = get_innertube_caption_url(vid)
        print(vid, "OK", lang, url[:90])
    except Exception as e:
        print(vid, "FAIL", type(e).__name__, str(e)[:150])
