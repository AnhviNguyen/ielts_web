"""
ml/model_registry.py
─────────────────────
Singleton loaders for heavy ML models.
All configuration is hardcoded — zero network access required.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_MODEL_PT = Path(os.getenv("PRON_MODEL_PATH", "model/pron_scorer_best.pt"))
_MIN_PT_BYTES = 1024


def _local_pron_path() -> Path:
    """Resolve the local .pt path (may not exist on HF Spaces)."""
    return _MODEL_PT if _MODEL_PT.is_absolute() else Path(__file__).resolve().parents[1] / _MODEL_PT


def resolve_pron_model_path() -> Path:
    """Resolve pronunciation model: local file first, then HF Hub download."""
    from app.core.model_downloader import resolve_model
    local = _local_pron_path()
    return Path(resolve_model("pron_scorer_best.pt", str(local)))


def pron_model_available() -> bool:
    """True when the pronunciation model can be loaded (local or via HF Hub)."""
    try:
        path = resolve_pron_model_path()
        return path.is_file() and path.stat().st_size >= _MIN_PT_BYTES
    except FileNotFoundError:
        return False

# wav2vec2-base-960h config — hardcoded so no HuggingFace download is needed
_WAV2VEC2_CONFIG = {
    "model_type":                    "wav2vec2",
    "hidden_size":                   768,
    "num_hidden_layers":             12,
    "num_attention_heads":           12,
    "intermediate_size":             3072,
    "hidden_act":                    "gelu",
    "hidden_dropout":                0.1,
    "activation_dropout":            0.0,
    "attention_dropout":             0.1,
    "feat_proj_dropout":             0.1,
    "feat_extract_dropout":          0.0,
    "layerdrop":                     0.1,
    "initializer_range":             0.02,
    "layer_norm_eps":                1e-5,
    "feat_extract_norm":             "group",
    "feat_extract_activation":       "gelu",
    "conv_dim":                      [512, 512, 512, 512, 512, 512, 512],
    "conv_stride":                   [5, 2, 2, 2, 2, 2, 2],
    "conv_kernel":                   [10, 3, 3, 3, 3, 2, 2],
    "conv_bias":                     False,
    "num_conv_pos_embeddings":       128,
    "num_conv_pos_embedding_groups": 16,
    "do_stable_layer_norm":          False,
    "apply_spec_augment":            True,
    "mask_time_prob":                0.05,
    "mask_time_length":              10,
    "mask_feature_prob":             0.0,
    "mask_feature_length":           10,
    "num_feat_extract_layers":       7,
    "feat_proj_layer_norm":          False,
    "vocab_size":                    32,
    "pad_token_id":                  0,
    "bos_token_id":                  1,
    "eos_token_id":                  2,
}

# ── singletons ────────────────────────────────────────────────────────────────
_pron_model = None


def _normalize_audio(audio):
    """Zero-mean / unit-std normalisation (matches Wav2Vec2FeatureExtractor)."""
    import numpy as np
    audio = audio.astype("float32")
    return (audio - audio.mean()) / (audio.std() + 1e-7)


# ── Pronunciation model ───────────────────────────────────────────────────────

class _PronNet:
    """
    Wraps the wav2vec2 fine-tuned scorer.
    All heavy imports (torch, transformers) happen lazily inside methods so
    that the module can be imported even when PyTorch is not installed.
    """

    def __init__(self, unfreeze_last_n: int = 6, n_layers_avg: int = 4):
        import torch
        import torch.nn as nn
        from transformers import Wav2Vec2Config, Wav2Vec2Model

        self.n_layers_avg = n_layers_avg

        cfg = Wav2Vec2Config(**_WAV2VEC2_CONFIG)
        w2v = Wav2Vec2Model(cfg)   # random init — weights come from .pt

        # match training freeze policy (needed to get the same param shapes)
        for p in w2v.feature_extractor.parameters():
            p.requires_grad = False
        for p in w2v.encoder.parameters():
            p.requires_grad = False
        n_layers = len(w2v.encoder.layers)
        for i in range(n_layers - unfreeze_last_n, n_layers):
            for p in w2v.encoder.layers[i].parameters():
                p.requires_grad = True
        for p in w2v.feature_projection.parameters():
            p.requires_grad = True

        H = cfg.hidden_size
        layer_weights = nn.Parameter(torch.ones(n_layers_avg) / n_layers_avg)
        attn_pool     = nn.Linear(H, 1)
        trunk = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 256), nn.GELU(), nn.Dropout(0.15))

        def _head():
            return nn.Sequential(nn.Linear(256, 64), nn.GELU(), nn.Linear(64, 1), nn.Sigmoid())

        # Assemble as a single nn.Module so state_dict loading works
        class Net(nn.Module):
            pass

        net = Net()
        net.w2v           = w2v
        net.layer_weights = layer_weights
        net.attn_pool     = attn_pool
        net.trunk         = trunk
        net.h_acc         = _head()
        net.h_flu         = _head()
        net.h_pro         = _head()
        net.h_tot         = _head()

        self._net = net

    def load_weights(self, path: Path) -> None:
        import torch
        raw = torch.load(str(path), map_location="cpu", weights_only=False)
        if isinstance(raw, dict):
            state = raw.get("model_state_dict", raw)
        else:
            # someone saved the whole model object
            state = raw.state_dict() if hasattr(raw, "state_dict") else raw
        missing, unexpected = self._net.load_state_dict(state, strict=False)
        if missing:
            logger.warning("Missing state_dict keys (%d): %s …", len(missing), missing[:3])
        if unexpected:
            logger.warning("Unexpected state_dict keys (%d): %s …", len(unexpected), unexpected[:3])
        self._net.eval()
        logger.info("PronunciationScorer weights loaded from %s", path)

    def predict(self, audio_np) -> dict[str, float]:
        """audio_np: float32 numpy array at 16 kHz mono. Returns scores 0–10."""
        import torch

        audio_norm   = _normalize_audio(audio_np)
        input_values = torch.tensor(audio_norm).unsqueeze(0).float()

        with torch.no_grad():
            out = self._net.w2v(input_values, output_hidden_states=True)
            stacked = torch.stack(out.hidden_states[-self.n_layers_avg:], dim=0)
            weights = torch.softmax(self._net.layer_weights, dim=0).view(-1, 1, 1, 1)
            hidden  = (stacked * weights).sum(0)

            attn_w = torch.softmax(self._net.attn_pool(hidden), dim=1)
            pooled = (hidden * attn_w).sum(1)
            z      = self._net.trunk(pooled)

            acc = self._net.h_acc(z).squeeze(-1).item()
            flu = self._net.h_flu(z).squeeze(-1).item()
            pro = self._net.h_pro(z).squeeze(-1).item()
            tot = self._net.h_tot(z).squeeze(-1).item()

        return {
            "accuracy": round(acc * 10, 1),
            "fluency":  round(flu * 10, 1),
            "prosodic": round(pro * 10, 1),
            "total":    round(tot * 10, 1),
        }


# ── Public getters ────────────────────────────────────────────────────────────

def get_pron_model() -> _PronNet:
    global _pron_model
    if _pron_model is None:
        pt = resolve_pron_model_path()
        logger.info("Loading PronunciationScorer from %s …", pt)
        net = _PronNet(unfreeze_last_n=6, n_layers_avg=4)
        net.load_weights(pt)
        _pron_model = net
        logger.info("PronunciationScorer ready.")
    return _pron_model


def get_whisper_model():
    """Delegate to faster-whisper singleton (ml.whisper_asr)."""
    from ml.whisper_asr import get_whisper_model as _get

    return _get()


def preload_all():
    """Warm up models at FastAPI startup (called in background thread)."""
    if not pron_model_available():
        logger.info(
            "Pronunciation model not found or is a Git LFS pointer at %s — skipping preload.",
            resolve_pron_model_path(),
        )
    else:
        try:
            get_pron_model()
        except Exception as exc:
            logger.warning("Could not preload PronunciationScorer: %s", exc)
    try:
        get_whisper_model()
    except Exception as exc:
        logger.warning("Could not preload Whisper: %s", exc)
