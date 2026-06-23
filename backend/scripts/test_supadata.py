from app.services.youtube_transcript_service import fetch_caption_segments, fetch_youtube_transcript, cookies_debug_info

print("has_supadata", cookies_debug_info().get("has_supadata"))
for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ"]:
    s, l = fetch_caption_segments(vid)
    print(vid, "segments", len(s), l)
