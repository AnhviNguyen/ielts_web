"""Centralized visibility check for user-facing content.

Handles legacy data where ``status`` may be an int (0/1),
a string ("published", "archived", "draft"), or absent entirely.
"""

from __future__ import annotations

from typing import Any


def is_public_content(item: dict[str, Any]) -> bool:
    """Return *True* if *item* should be visible to regular (non-admin) users.

    Hidden when any of:
    - ``is_public`` is explicitly ``False``
    - ``status`` is ``0``, ``"0"``, or ``False``
    - ``status`` (string) equals ``"archived"`` (case-insensitive)
    """
    if item.get("is_public") is False:
        return False
    status = item.get("status")
    if status in (0, "0", False):
        return False
    if isinstance(status, str) and status.lower() == "archived":
        return False
    return True
