from app.services.youtube_transcript_service import cookies_debug_info, get_innertube_caption_url

print("cookies", cookies_debug_info())
try:
    url, lang = get_innertube_caption_url("5MuIMqhT8DM", ["en"])
    print("innertube ok", lang, len(url))
except Exception as e:
    print("innertube fail", e)
