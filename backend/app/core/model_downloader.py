"""
Central model resolver — download from HuggingFace Hub or use local files.

Priority:
1. If a valid local file exists → use it (dev mode / pre-downloaded).
2. Otherwise → download from the HF Model Repository via ``hf_hub_download``.

``hf_hub_download`` handles caching automatically: the file is downloaded once
and stored in ``~/.cache/huggingface/hub/``.  Subsequent calls return the
cached path immediately without any network request.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Minimum file size to accept a local file as "real" (not a Git LFS pointer).
_MIN_VALID_BYTES = 1024


def _is_valid_local_file(path: Path) -> bool:
    """Return True when *path* exists, is big enough, and is NOT a Git LFS pointer."""
    if not path.is_file():
        return False
    if path.stat().st_size < _MIN_VALID_BYTES:
        return False
    try:
        head = path.read_bytes()[:32]
    except OSError:
        return False
    # Git LFS pointer files start with "version https://git-lfs"
    return not head.startswith(b"version https://git-lfs")


def resolve_model(
    filename: str,
    local_path: str | None = None,
) -> str:
    """
    Resolve a model file path.

    Parameters
    ----------
    filename:
        Name of the file in the HF Model Repository (e.g. ``pron_scorer_best.pt``).
    local_path:
        Optional local filesystem path to check first.  When running locally
        with the model file already present, this avoids any HF Hub call.

    Returns
    -------
    str
        Absolute path to the model file (either local or HF-cached).

    Raises
    ------
    FileNotFoundError
        When the model cannot be found locally and HF Hub download fails.
    """
    # 1. Try local path first (backward-compatible for dev mode)
    if local_path:
        local = Path(local_path)
        if _is_valid_local_file(local):
            logger.debug("Using local model: %s", local)
            return str(local)

    # 2. Download from HuggingFace Hub
    try:
        from app.core.config import settings
        repo_id = settings.HF_MODEL_REPO_ID
    except Exception:
        repo_id = os.environ.get("HF_MODEL_REPO_ID", "phuc7/linguaielts-models")
    logger.info(
        "Downloading model '%s' from HF repo '%s' …",
        filename,
        repo_id,
    )

    try:
        from huggingface_hub import hf_hub_download

        cached_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
        )
        logger.info("Model '%s' ready at: %s", filename, cached_path)
        return cached_path
    except Exception as exc:
        raise FileNotFoundError(
            f"Model '{filename}' not found locally"
            f"{f' ({local_path})' if local_path else ''}"
            f" and HF Hub download failed: {exc}"
        ) from exc
