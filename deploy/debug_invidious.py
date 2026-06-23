import json
import httpx

vid = "5MuIMqhT8DM"
instances = [
    "https://inv.tux.pizza",
    "https://invidious.fdn.fr",
    "https://yt.artemislena.eu",
    "https://invidious.privacyredirect.com",
]

for base in instances:
    url = f"{base}/api/v1/captions/{vid}?lang=en"
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        print(base.split("//")[1].split("/")[0], r.status_code, r.text[:120].replace("\n", " "))
    except Exception as e:
        print(base, "ERR", e)
