from app.services.youtube_transcript_service import fetch_caption_segments, cookies_debug_info

print("debug", cookies_debug_info())
for vid in ["II5h6uJPvvs", "5MuIMqhT8DM"]:
    try:
        s, l = fetch_caption_segments(vid)
        print(vid, "OK", len(s), l)
    except Exception as e:
        print(vid, "FAIL", type(e).__name__, str(e)[:200])
