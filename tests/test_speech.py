"""Speech models for other spoken languages (Arabic first): downloading one only when asked, removing it, choosing
the language for a video or a creator, Arabic words, and the second machine never using the wrong language's model.
Runs against the code directly, with its own empty data folder; nothing is downloaded."""
import io
import os
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

os.environ["PEAKCUT_DATA"] = tempfile.mkdtemp(prefix="pc-speech-")
os.environ.pop("PEAKCUT_MODELS", None)          # models are made and removed: only ever inside this test's folder
os.environ.update(DATABASE_URL="", PEAKCUT_ACCOUNTS="0", PEAKCUT_FETCH_MODEL="0", PEAKCUT_AI_KEY="", PEAKCUT_AI_KEY_FILE="",
                  PEAKCUT_PUBLIC_URL="http://127.0.0.1:8765")
sys.path.insert(0, ".")
from fastapi.testclient import TestClient  # noqa: E402

from studio import brain, config, creators, db, fetch_model, jobs, live, server, transcribe  # noqa: E402

db.init()
fails = []
BASE = "http://127.0.0.1:8765"
ORIGIN = {"Origin": BASE}
c = TestClient(server.app, base_url=BASE, follow_redirects=False)


def check(name, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   got {ascii(got)}"))
    ok or fails.append(name)


assert str(config.MODELS_DIR).startswith(os.environ["PEAKCUT_DATA"]), "the test must only touch its own folder"
downloads = []


def fake_download(url, dest, hook=None):
    """A tiny stand-in for the real archive: the right folder name, the four files."""
    downloads.append(url)
    lang = next(k for k, m in fetch_model.MODELS.items() if m[2] == url)
    name = fetch_model.MODELS[lang][1]
    src = Path(tempfile.mkdtemp(prefix="pc-tar-")) / name
    src.mkdir()
    for n in ("tokens.txt", "encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx"):
        (src / n).write_bytes(b"model")
    with tarfile.open(dest, "w:bz2") as t:
        t.add(src, arcname=name)
    if hook:
        hook(1, 100, 100)


class _Reply(io.BytesIO):
    headers = {}
    def __enter__(self): return self
    def __exit__(self, *a): pass


def fake_open(url, timeout=None):
    """The download now reads the archive itself (so it can give up on a stalled connection): hand it the bytes."""
    dest = Path(tempfile.mkdtemp(prefix="pc-dl-")) / "m.tar.bz2"
    fake_download(url, dest)
    return _Reply(dest.read_bytes())


fetch_model.urllib.request.urlopen = fake_open

# ---- the list of models
check("English and Arabic are known", sorted(fetch_model.MODELS), ["ar", "en"])
check("Arabic is downloaded from its own address, not English's", fetch_model.MODELS["ar"][2] != fetch_model.MODELS["en"][2], True)
check("each language has its own folder", fetch_model.folder("ar") != fetch_model.folder("en"), True)
check("nothing is here to begin with", (fetch_model.status("en"), fetch_model.status("ar")), ("missing", "missing"))

# ---- Arabic is never downloaded unless someone asks
try:
    fetch_model.ensure("ar", start=False)
    said = ""
except RuntimeError as e:
    said = str(e)
check("a video needing Arabic says what to do instead of downloading", ("Speech models" in said, downloads), (True, []))
try:
    transcribe._new("ar")
    said = ""
except RuntimeError as e:
    said = str(e)
check("...and so does loading the model for transcribing", ("Speech models" in said, downloads), (True, []))

# ---- the routes: list, download, remove
r = c.get("/api/speech").json()["models"]
check("the page lists both languages with their size", [(m["lang"], m["state"], m["size_mb"] > 0) for m in r],
      [("en", "missing", True), ("ar", "missing", True)])
check("an unknown language is refused", c.post("/api/speech/xx", headers=ORIGIN).status_code, 400)
check("another website cannot start a download", c.post("/api/speech/ar", headers={"Origin": "https://evil.example"}).status_code, 403)
check("...and nothing was downloaded", downloads, [])
check("the owner can start the Arabic download", c.post("/api/speech/ar", headers=ORIGIN).status_code, 200)
for _ in range(100):
    if fetch_model.status("ar") == "ready":
        break
    time.sleep(0.05)
check("Arabic arrives whole, in its own folder", (fetch_model.ready("ar"), sorted(p.name for p in fetch_model.folder("ar").iterdir())),
      (True, ["decoder.int8.onnx", "encoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]))
check("English was not touched", fetch_model.ready("en"), False)
check("nothing is left over from the download", sorted(p.name for p in config.MODELS_DIR.iterdir()), [fetch_model.MODELS["ar"][1]])
check("the status tells every page Arabic is ready", c.get("/api/status").json()["speech"]["ar"]["state"], "ready")
check("asking again downloads nothing more", (c.post("/api/speech/ar", headers=ORIGIN).status_code, len(downloads)), (200, 1))
check("English can't be removed", c.delete("/api/speech/en", headers=ORIGIN).status_code, 400)

transcribe._pool("ar").made += 1                  # pretend a video is transcribing in Arabic right now
check("a model in use is not removed", (c.delete("/api/speech/ar", headers=ORIGIN).status_code, fetch_model.ready("ar")), (409, True))
transcribe._pool("ar").made -= 1
check("Arabic can be removed when nothing uses it", (c.delete("/api/speech/ar", headers=ORIGIN).status_code, fetch_model.folder("ar").exists()), (200, False))

# ---- choosing the language
check("a video can be marked as Arabic", jobs.clean_options({"lang": "ar"}), {"lang": "ar"})
check("an unknown language becomes English", jobs.clean_options({"lang": "xx"}), {"lang": "en"})
check("videos are English unless chosen", jobs.DEFAULTS["lang"], "en")
check("a creator can speak Arabic", creators._clean({"lang": "ar"}), {"lang": "ar"})
check("...but not a made-up language", creators._clean({"lang": "<b>"}), {"lang": "en"})
r = c.post("/api/creators", json={"name": "Arabic speaker"}, headers=ORIGIN)
cid = r.json()["id"]
c.put(f"/api/creators/{cid}", json={"lang": "ar"}, headers=ORIGIN)
from studio import auth, ctx  # noqa: E402
with ctx.as_user(auth.local_user().id):
    cr = creators.get(cid)
    check("the creator's language is kept", cr.get("lang"), "ar")
    try:
        live.start_session(cr, "https://www.twitch.tv/someone")
        said = ""
    except ValueError as e:
        said = str(e)
    check("recording an Arabic creator without the model says what to do", "Speech models" in said, True)

# ---- Arabic words
tokens = ["▁ال", "ك", "ت", "ا", "بُ", "▁جـ", "ميل", "،", "▁ok"]
words = transcribe._words(tokens, [0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 1.0], 0, 32000)
check("Arabic pieces join into words, vowel marks and the stretching line removed, punctuation kept",
      [w["w"] for w in words], ["الكتاب", "جميل،", "ok"])
check("live word matching works in Arabic letters", (live._plain("الكتابُ"), live._plain("Clip-That!")), ("الكتاب", "clipthat"))

from studio import roman  # noqa: E402
check("Arabic without the AI is spelled in Roman letters the caption font can draw, hamza and commas too",
      roman.to_roman("قابلت نوران أنا، إن شاء الله؟"), lambda t: not roman.OTHER_SCRIPT.search(t) and "," in t and "?" in t)

# ---- the AI is told about English words in Arabic letters, only when the transcript is in Arabic letters
arabic = "[1] " + "مرحبا بكم في الحلقة الجديدة سبسكرايب " * 3
check("an Arabic transcript gets the note", brain.ARABIC_NOTE in brain._rules(15, 60, arabic), True)
check("an English one does not", brain.ARABIC_NOTE in brain._rules(15, 60, "[1] hello and welcome back " * 5), False)

# ---- the second machine: never the wrong language's model
class Reply:
    def __init__(self, code, body):
        self.status_code, self.body = code, body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self.body


import httpx  # noqa: E402
real_post = httpx.post
piece = [transcribe.np.zeros(16000, dtype="float32")]
old = {"pieces": [{"tokens": ["▁hi"], "timestamps": [0.0]}]}
httpx.post = lambda *a, **k: Reply(200, old)               # an older machine: answers in English, says no language
try:
    transcribe._decode_remote(piece, "ar")
    got = "used"
except transcribe.RemoteLacks:
    got = "refused"
check("an older machine's English answer is not used for Arabic", got, "refused")
check("...but still used for English", transcribe._decode_remote(piece, "en"), [(["▁hi"], [0.0])])
httpx.post = lambda *a, **k: Reply(409, {})
try:
    transcribe._decode_remote(piece, "ar")
    got = "used"
except transcribe.RemoteLacks:
    got = "refused"
check("a machine without the Arabic model says so", got, "refused")
httpx.post = lambda *a, **k: Reply(200, dict(old, lang="ar"))
check("a machine with the Arabic model is used", transcribe._decode_remote(piece, "ar"), [(["▁hi"], [0.0])])
httpx.post = real_post

print("ALL PASSED" if not fails else f"{len(fails)} failed")
shutil.rmtree(os.environ["PEAKCUT_DATA"], ignore_errors=True)
sys.exit(1 if fails else 0)
