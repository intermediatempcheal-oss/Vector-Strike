import shutil
import socket
import subprocess

print("psql:", shutil.which("psql") or "not found")
print("postgres:", shutil.which("postgres") or "not found")
print("pg_isready:", shutil.which("pg_isready") or "not found")

s = socket.socket()
s.settimeout(1)
try:
    s.connect(("127.0.0.1", 5432))
    print("port 5432: OPEN")
except OSError:
    print("port 5432: closed")
finally:
    s.close()

out = subprocess.run(["sc", "query", "postgresql-x64-17"], capture_output=True, text=True)
print("sc query:", out.returncode, (out.stdout + out.stderr).strip()[:200])