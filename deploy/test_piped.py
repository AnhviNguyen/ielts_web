#!/usr/bin/env python3
import json
import urllib.request

vid = "dQw4w9WgXcQ"
url = f"https://pipedapi.kavin.rocks/streams/{vid}"
with urllib.request.urlopen(url, timeout=20) as r:
    d = json.load(r)
subs = d.get("subtitles") or []
print("subs", len(subs))
for s in subs[:8]:
    print(s.get("code"), (s.get("url") or "")[:100])
