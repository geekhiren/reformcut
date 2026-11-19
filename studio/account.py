"""Deleting things for good: one clip, a creator with everything under it, or a whole account.

Nothing here can be undone, so every caller asks the person first. Work in progress is never pulled out from under
itself: a video still being made, or a stream still being recorded, has to finish or be stopped first."""
import shutil
import time
import zipfile
from pathlib import Path

from . import auth, cloud, config, creators, ctx, db, jobs, live, usage


class Busy(Exception):
    """Something is still being worked on."""


def _busy(job) -> bool:
    return job["status"] in ("queued", "running", "live") or job["id"] in live.SESSIONS


# ---------------------------------------------------------------- clips and videos
def delete_clip(jid: str, cid: str) -> bool:
    """Remove one clip and its files. The video and its other clips stay."""
    job = jobs.get(jid)
    if not job:
        return False
    clip = next((c for c in job["clips"] if c["id"] == cid), None)
    if not clip:
        return False
    if clip.get("status") in ("queued", "rendering"):
        raise Busy("This clip is still being made. Wait for it to finish first.")
    job["clips"] = [c for c in job["clips"] if c["id"] != cid]
    jobs.save(job)
    d = Path(job["dir"])
    for name in (clip.get("file"), clip.get("cover")):
        if name:
            (d / "clips" / Path(str(name)).name).unlink(missing_ok=True)
            cloud.remove(d / "clips" / Path(str(name)).name)
    for stem in {cid, Path(str(clip.get("file") or cid)).stem}:     # the captions and the notes kept beside the clip
        for ext in ("ass", "json"):
            (d / "clips" / f"{stem}.{ext}").unlink(missing_ok=True)
    src = clip.get("src")
    if src:                                        # the piece of video fetched or recorded just for this clip
        p = Path(src)
        try:
            mine = p.resolve().parent in ((d / "clips").resolve(), d.resolve()) and p.name.startswith(f"{cid}.src")
        except OSError:
            mine = False
        if mine:                                   # never the whole video's own file
            p.unlink(missing_ok=True)
    ctx.bump()
    return True


def delete_many(job_ids: list, clip_ids: list) -> dict:
    """Delete several videos and clips in one go. What is still being worked on is left alone and counted."""
    out = {"videos": 0, "clips": 0, "skipped": 0}
    whole = set()
    for jid in dict.fromkeys(job_ids):
        job = jobs.get(jid)
        if not job:
            continue
        if _busy(job):
            out["skipped"] += 1
            continue
        if jobs.delete(jid):
            whole.add(jid)
            out["videos"] += 1
    for jid, cid in dict.fromkeys(clip_ids):
        if jid in whole:
            continue
        try:
            out["clips"] += bool(delete_clip(jid, cid))
        except Busy:
            out["skipped"] += 1
    return out


def zip_clips(clip_ids: list, limit_gb: float = 4.0) -> Path:
    """One .zip of finished clips, for downloading many at once. Clips are already compressed, so they are only
    stored, not squeezed again: making the file is as fast as copying."""
    files, texts, total, seen, fetched = [], [], 0, set(), []     # fetched: pulled down from online storage just for this zip
    for jid, cid in dict.fromkeys(clip_ids):
        job = jobs.get(jid)
        clip = next((c for c in (job or {}).get("clips", []) if c["id"] == cid and c.get("status") == "done"), None)
        if not clip or not clip.get("file"):
            continue
        f = Path(job["dir"]) / "clips" / Path(str(clip["file"])).name
        if cloud.fetch(f):
            fetched.append(f)
        if not f.is_file():
            continue
        total += f.stat().st_size
        if total > limit_gb * 1e9:
            raise ValueError(f"That is more than {limit_gb:g} GB of clips. Download them in smaller groups.")
        # numbered the way the app shows them (Clip 1, Clip 2...), so a file and its text below are easy to match
        title = "".join(ch if ch.isalnum() or ch in " -_" else "" for ch in (clip.get("title") or clip.get("hook") or cid))[:60].strip() or cid
        base = f"Clip {job['clips'].index(clip) + 1:02d} - {title}"
        name, n = f"{base}.mp4", 2
        while name.lower() in seen:
            name, n = f"{base} ({n}).mp4", n + 1
        seen.add(name.lower())
        files.append((f, name))
        texts.append(post_text(name, job, clip))
    if not files:
        raise ValueError("None of those clips are ready to download.")
    tmp = config.user_dir(ctx.uid()) / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("clips-*.zip"):                       # leftovers from downloads that were abandoned
        if time.time() - old.stat().st_mtime > 3600:
            old.unlink(missing_ok=True)
    out = tmp / f"clips-{int(time.time() * 1000)}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for f, name in files:
            z.write(f, name)
        # everything needed to post the clips by hand, one block per clip, in the same order as the files
        z.writestr("post-text.txt", "\n\n".join(texts).replace("\n", "\r\n").encode("utf-8-sig"))
    for f in fetched:
        f.unlink(missing_ok=True)
    return out


def post_text(name: str, job: dict, clip: dict) -> str:
    """One clip's post text, ready to copy into YouTube, Instagram or TikTok by hand."""
    line = "=" * 70
    parts = [line, name, line,
             "TITLE:\n" + (clip.get("title") or clip.get("hook") or ""),
             "YOUTUBE DESCRIPTION:\n" + (clip.get("description") or ""),
             "INSTAGRAM / TIKTOK CAPTION:\n" + (clip.get("caption") or "(none: use the title and YouTube description)"),
             "HASHTAGS:\n" + " ".join("#" + h for h in clip.get("hashtags") or []),
             "YOUTUBE TAGS:\n" + ", ".join(clip.get("tags") or [])]
    from . import posting      # here, not at the top: posting imports jobs, which this module also imports
    credit = posting.credit_line(creators.get(job.get("creator")) or dict(creators.DEFAULTS), job.get("uploader", ""))
    if credit:
        parts.append("CREDIT (add to every post):\n" + credit)
    return "\n".join(parts[:3]) + "\n" + "\n\n".join(parts[3:])


# ---------------------------------------------------------------- creators
def delete_creator(cid: str) -> dict:
    """Remove a creator, their settings and folder, and every video and clip filed under them."""
    c = creators.get(cid)
    if not c:
        return {"ok": False}
    if live.active_for(cid):
        raise Busy("This creator is being recorded. Stop the recording first.")
    mine = [j for j in jobs.list_jobs() if j.get("creator") == cid]
    if any(_busy(j) for j in mine):
        raise Busy("One of this creator's videos is still being made. Wait for it to finish first.")
    for j in mine:
        jobs.delete(j["id"])
    with creators._lock:
        creators._mine().pop(cid, None)
    cloud.remove_prefix(creators.root(cid))
    shutil.rmtree(creators.root(cid), ignore_errors=True)
    ctx.bump()
    return {"ok": True, "videos": len(mine)}


# ---------------------------------------------------------------- the whole account
def delete_account(uid: str) -> dict:
    """Remove an account and everything it owns: recordings, videos, clips, creators, connected accounts and
    history. Sign-in is removed too."""
    u = auth.get_user(uid)
    if not u:
        return {"ok": False}
    if u.is_admin:
        raise Busy("Admin accounts can't be deleted. Make it a normal account first.")
    with ctx.as_user(uid):
        for s in list(live.SESSIONS.values()):
            if s.job.get("user") == uid and not s.finished:
                raise Busy("A stream is still being recorded. Stop the recording first.")
        mine = jobs.list_jobs()
        if any(_busy(j) for j in mine):
            raise Busy("A video is still being made. Wait for it to finish, then delete the account.")
        for j in mine:
            jobs.delete(j["id"])
    with db.engine.begin() as c:
        for t in reversed(db.meta.sorted_tables):
            if t.name != "users" and "user_id" in t.c:
                c.execute(t.delete().where(t.c.user_id == uid))
        c.execute(db.users.delete().where(db.users.c.id == uid))
    auth.forget(uid)
    creators._mem.pop(uid, None)
    try:
        from . import accounts
        accounts._settings_mem.pop(uid, None)
    except Exception:  # noqa: BLE001
        pass
    from . import posting
    posting.forget(uid)                            # scheduled posts must not outlive the account that owns them
    usage.forget(uid)
    cloud.remove_prefix(config.user_dir(uid))
    shutil.rmtree(config.user_dir(uid), ignore_errors=True)
    return {"ok": True}
