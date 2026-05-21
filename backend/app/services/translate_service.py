"""
Lightweight translation via Google Translate public endpoint (no API key).
"""

from __future__ import annotations

import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)


async def translate_text(
    text: str,
    from_lang: str = "en",
    to_lang: str = "vi",
) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    params = {
        "client": "gtx",
        "sl": from_lang or "auto",
        "tl": to_lang or "vi",
        "dt": "t",
        "q": text,
    }
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(params)

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    if not data or not isinstance(data[0], list):
        return ""

    parts = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
    result = "".join(parts).strip()
    logger.debug("Translated %d chars %s→%s", len(text), from_lang, to_lang)
    return result
