"""Hinglish creators are heard by Sarvam AI: words come back in Roman letters, spread over each phrase, on the
stream's own clock. Sarvam is replaced by a stand-in, so nothing leaves this machine."""
import os, sys, tempfile
os.environ["REFORMCUT_DATA"] = tempfile.mkdtemp(prefix="pc-sarvam-"); os.environ["DATABASE_URL"] = ""
os.environ["SARVAM_API_KEY"] = "test-key-123"
sys.path.insert(0, ".")
import numpy as np
from studio import creators, ctx, sarvam_asr, transcribe
fails = []
def check(n, ok, x=""):
    print(("PASS " if ok else "FAIL ") + n + (f"  {x}" if x and not ok else "")); ok or fails.append(n)
def text(words):
    return " ".join(w["w"] for w in words)

# ---- spreading one phrase over its time
w = sarvam_asr.spread("bhai ye kya hua", 10.0, 12.0)
check("each word of a phrase gets an equal share", [x["s"] for x in w] == [10.0, 10.5, 11.0, 11.5], str(w))
check("...and ends before the next word starts", all(a["e"] < b["s"] for a, b in zip(w, w[1:])), str(w))
check("an empty phrase gives no words", sarvam_asr.spread("  ", 0, 5) == [])

# ---- answers with and without phrase times
ans = {"transcript": "arre bhai clip it", "timestamps": {"words": ["arre bhai", "clip it"],
       "start_time_seconds": [0.0, 1.5], "end_time_seconds": [1.2, 2.5]}}
check("phrase times are used when Sarvam sends them", sarvam_asr._phrases(ans, 5.0) == [("arre bhai", 0.0, 1.2), ("clip it", 1.5, 2.5)])
check("without them the whole piece is one phrase", sarvam_asr._phrases({"transcript": "kya scene hai"}, 5.0) == [("kya scene hai", 0.0, 5.0)])

# ---- the whole path: loud audio goes to Sarvam, silence does not, times sit on the stream's clock
calls = []
def fake_ask(seg):
    calls.append(len(seg))
    return {"transcript": "bhai ye kya ho gaya", "timestamps": None}
sarvam_asr._ask = fake_ask
sr = 16000
loud = (np.sin(np.arange(sr * 4) / 3) * 8000).astype(np.int16)
quiet = np.zeros(sr * 4, dtype=np.int16)
out = transcribe.transcribe(np.concatenate([loud]), lang="hinglish")
check("Hinglish goes to Sarvam and comes back in Roman letters", text(out) == "bhai ye kya ho gaya", text(out))
check("...timed inside the audio", out[0]["s"] == 0.0 and out[-1]["e"] <= 4.0, str(out))
calls.clear()
check("silence is never sent (it costs money)", transcribe.transcribe(quiet, lang="hinglish") == [] and not calls)

# ---- the creator setting
with ctx.as_user("u_test"):
    c = creators.create({"name": "Carry", "channels": {"youtube": "https://www.youtube.com/@CarryisLive"}})
    check("a new creator is English by default", c["language"] == "en")
    check("Hinglish can be chosen", creators.update(c["id"], {"language": "hinglish"})["language"] == "hinglish")
    check("anything else falls back to English", creators.update(c["id"], {"language": "klingon"})["language"] == "en")

# ---- a plain video (no creator) can be Hinglish too
from studio import jobs
check("a video's language can be Hinglish", jobs.clean_options({"language": "hinglish"})["language"] == "hinglish")
check("...anything else is English", jobs.clean_options({"language": "xx"})["language"] == "en")
check("videos are English unless chosen", jobs.DEFAULTS["language"] == "en")

print("ALL PASSED" if not fails else f"{len(fails)} failed")
import shutil; shutil.rmtree(os.environ["REFORMCUT_DATA"], ignore_errors=True)
sys.exit(1 if fails else 0)
