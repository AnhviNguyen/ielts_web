from app.services.youtube_transcript_service import fetch_caption_segments, cookies_debug_info

d = cookies_debug_info()
print("has_supadata", d.get("has_supadata"), "has_apify", d.get("has_apify"))
for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ"]:
    s, l = fetch_caption_segments(vid)
    print(vid, "OK", len(s), l)
