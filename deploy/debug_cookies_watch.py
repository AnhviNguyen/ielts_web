from app.services.youtube_transcript_service import cookies_debug_info, _extract_player_response_from_watch_page, _caption_tracks_from_player

print("cookies", cookies_debug_info())
for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ"]:
    pr = _extract_player_response_from_watch_page(vid)
    if not pr:
        print(vid, "no player")
        continue
    print(vid, "playability", pr.get("playabilityStatus", {}).get("status"), "tracks", len(_caption_tracks_from_player(pr)))
