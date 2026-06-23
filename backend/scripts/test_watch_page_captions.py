#!/usr/bin/env python3
"""Test watch-page caption extraction (run inside api container)."""
import re
import json
import httpx

def extract_player(html: str):
    marker = "var ytInitialPlayerResponse = "
    idx = html.find(marker)
    if idx < 0:
        marker = "ytInitialPlayerResponse = "
        idx = html.find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    depth = 0
    for i, ch in enumerate(html[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : i + 1])
    return None

for vid in ["5MuIMqhT8DM", "dQw4w9WgXcQ", "jNQXAC9IVRw"]:
    r = httpx.get(
        f"https://www.youtube.com/watch?v={vid}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        follow_redirects=True,
        timeout=25,
    )
    pr = extract_player(r.text)
    if not pr:
        print(vid, "NO_PLAYER")
        continue
    tracks = (
        pr.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    print(vid, "tracks", len(tracks), "playability", pr.get("playabilityStatus", {}).get("status"))
    if tracks:
        url = tracks[0]["baseUrl"]
        if "fmt=" not in url:
            url += "&fmt=json3" if "?" in url else "?fmt=json3"
        r2 = httpx.get(url, timeout=20)
        print("  timedtext", r2.status_code, "bytes", len(r2.text))
