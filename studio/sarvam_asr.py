"""Hinglish speech to text through Sarvam AI (saaras), for creators set to the "hinglish" language.

The local model (transcribe.py) only knows English. Sarvam hears Hindi, Hinglish and Indian English and, in
"translit" mode, writes everything in Roman letters ("bhai ye kya ho gaya"), which is what the captions need.
Sarvam gives the time of each phrase, not of each word, so the words of a phrase are spread evenly across it."""
import io
import time
import wave

import numpy as np

from . import config

URL = "https://api.sarvam.ai/speech-to-text"
MODEL = config.env("REFORMCUT_SARVAM_MODEL", "saaras:v4")
SR = 16000


def ready() -> bool:
    return bool(config.sarvam_key())


def spread(text: str, start: float, end: float) -> list:
    """The words of one phrase, each given an equal share of [start, end]."""
    words = text.split()
    if not words or end <= start:
        return []
    step = (end - start) / len(words)
    return [{"w": w, "s": round(start + i * step, 2), "e": round(start + (i + 1) * step - 0.02, 2)}
            for i, w in enumerate(words)]


def _phrases(answer: dict, length: float) -> list:
    """(text, start, end) for each phrase in one Sarvam answer; the whole piece when no timestamps came back."""
    ts = answer.get("timestamps") or {}
    texts, starts, ends = ts.get("words") or [], ts.get("start_time_seconds") or [], ts.get("end_time_seconds") or []
    if texts and len(texts) == len(starts) == len(ends):
        return [(str(t), float(s), float(e)) for t, s, e in zip(texts, starts, ends)]
    text = str(answer.get("transcript") or "").strip()
    return [(text, 0.0, length)] if text else []


def _wav(seg: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(seg.astype(np.int16).tobytes())
    return buf.getvalue()


def _ask(seg: np.ndarray) -> dict:
    """One piece (at most 30 s) to Sarvam. Rate limits and overloads are tried again with a growing wait."""
    import httpx
    key = config.sarvam_key()
    if not key:
        raise RuntimeError("Hinglish needs a Sarvam key: set SARVAM_API_KEY in .env.")
    data = {"model": MODEL, "mode": "translit", "language_code": "hi-IN", "with_timestamps": "true"}
    for attempt in range(4):
        r = httpx.post(URL, headers={"api-subscription-key": key}, data=data,
                       files={"file": ("piece.wav", _wav(seg), "audio/wav")}, timeout=60)
        if r.status_code in (429, 503) and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    return {}


def transcribe(audio: np.ndarray, on_progress=None) -> list:
    """Same shape as transcribe.transcribe: [{'w', 's', 'e'}, ...] for the whole audio (16 kHz, int16)."""
    from .transcribe import _chunks
    pieces = list(_chunks(audio))
    words = []
    for i, (a, b) in enumerate(pieces):
        seg = audio[a:b]
        x = seg.astype(np.float32) / 32768.0
        if len(seg) >= 4800 and float(np.sqrt((x ** 2).mean())) >= 0.003:   # silence costs money and adds made-up words
            off = a / SR
            for text, s, e in _phrases(_ask(seg), (b - a) / SR):
                words += spread(text, off + s, off + e)
        if on_progress:
            on_progress((i + 1) / len(pieces))
    return words
