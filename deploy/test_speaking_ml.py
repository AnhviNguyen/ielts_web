import asyncio
import numpy as np
from ml.model_registry import get_whisper_model, pron_model_available, preload_all

print("pron available", pron_model_available())
try:
    print("loading faster-whisper...")
    m = get_whisper_model()
    print("whisper OK", type(m))
except Exception as e:
    print("whisper FAIL", type(e).__name__, str(e)[:300])

from app.services.speaking_audio_utils import run_whisper, run_pronunciation, load_audio_16k
import tempfile, os

# minimal silent wav
import wave
path = tempfile.mktemp(suffix=".wav")
with wave.open(path, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(b"\x00\x00" * 16000)

try:
    audio = load_audio_16k(path)
    print("audio rms", float(np.sqrt(np.mean(audio**2))))
    print("pron", run_pronunciation(audio))
    print("whisper", run_whisper(path))
except Exception as e:
    print("pipeline FAIL", type(e).__name__, str(e)[:300])
finally:
    os.unlink(path)
