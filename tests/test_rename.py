"""Reform Cut used to be Reform Cut: old settings and the old database file carry on working."""
import os, subprocess, sys, tempfile
from pathlib import Path

data = Path(tempfile.mkdtemp(prefix="rc-rename-"))
for end in ("", "-wal", "-shm"):
    (data / f"peakcut.db{end}").write_bytes(b"x")
env = {k: v for k, v in os.environ.items() if not k.startswith(("PEAKCUT_", "REFORMCUT_"))}
env.update(PEAKCUT_DATA=str(data), PEAKCUT_PORT="8123", REFORMCUT_AI_PROVIDER="new", PEAKCUT_AI_PROVIDER="old", DATABASE_URL="")
code = "from studio import config as c; print(c.PORT, c.DATA_DIR, c.env('REFORMCUT_AI_PROVIDER'))"
out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
fails = []
def check(name, got, want):
    ok = got == want
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   got {got!r}"))
    ok or fails.append(name)
port, folder, provider = (out.stdout.split() + ["", "", ""])[:3]
check("an old PEAKCUT_ setting still works", (port, folder), ("8123", str(data)))
check("the new name wins when both are set", provider, "new")
check("the old database file is renamed, journals too", sorted(p.name for p in data.iterdir() if "db" in p.name),
      ["reformcut.db", "reformcut.db-shm", "reformcut.db-wal"])
print(out.stderr[-500:] if fails else "")
sys.exit(1 if fails else 0)
