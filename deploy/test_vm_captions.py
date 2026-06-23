from app.services.youtube_transcript_service import fetch_caption_segments

for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ", "jNQXAC9IVRw"]:
    try:
        s, l = fetch_caption_segments(vid)
        print(vid, "OK", len(s), l)
    except Exception as e:
        print(vid, "FAIL", type(e).__name__, str(e)[:120])
