import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = Path(os.environ.get("VECTOR_STRIKE_LOG_DIR", Path.cwd() / ".runtime_logs"))
TMP.mkdir(parents=True, exist_ok=True)

flags = (
    subprocess.CREATE_NEW_PROCESS_GROUP
    | subprocess.DETACHED_PROCESS
    | subprocess.CREATE_NO_WINDOW
)

venv_python = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
py = str(venv_python if venv_python.exists() else Path(os.environ.get("PYTHON", shutil.which("python") or "python")))
node = os.environ.get("NODE", shutil.which("node") or "node")

jobs = (
    ("django", [py, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
     ROOT / "backend", "django.log"),
    ("vite", [node, str(ROOT / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"), "--port", "5173", "--host", "127.0.0.1"],
     ROOT / "frontend", "vite.log"),
)

for name, args, cwd, log in jobs:
    fh = open(TMP / log, "w", encoding="utf-8")
    subprocess.Popen(
        args,
        cwd=cwd,
        stdout=fh,
        stderr=subprocess.STDOUT,
        creationflags=flags,
        close_fds=True,
    )
    print(f"{name} spawned")

import time
time.sleep(10)
import socket


def up(port):
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        return "UP"
    except OSError:
        return "DOWN"
    finally:
        s.close()


print("django", up(8000))
print("vite", up(5173))