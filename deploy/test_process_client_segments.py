import asyncio
from app.db.database import AsyncSessionLocal
from app.repositories.shadowing_repository import ShadowingRepository
from app.services.shadowing_service import ShadowingService
from app.services.youtube_transcript_service import get_innertube_caption_url, parse_timedtext_content
import httpx

vid = "5MuIMqhT8DM"
url = f"https://www.youtube.com/watch?v={vid}"

# Simulate client_segments from browser (use pre-signed URL from local if innertube fails on VM)
try:
    cap_url, lang = get_innertube_caption_url(vid, ["en"])
    print("innertube ok", lang)
except Exception as e:
    print("innertube fail", e)
    cap_url = open("/app/caption_url.txt", encoding="utf-8").read().strip()
    lang = "en"
    print("using fallback signed url")

raw = httpx.get(cap_url, timeout=20).text
client_segments = parse_timedtext_content(raw)
print("client_segments", len(client_segments))


async def main():
    async with AsyncSessionLocal() as db:
        svc = ShadowingService(ShadowingRepository(db))
        data = await svc.process_url(
            url,
            level="Intermediate",
            translate=False,
            client_segments=client_segments[:50],
            client_language=lang,
            force_refresh=True,
        )
        await db.commit()
        print("process_ok", data["video_id"], data["transcript_source"], len(data["segments"]))


asyncio.run(main())
