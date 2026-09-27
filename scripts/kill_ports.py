import re
import subprocess

out = subprocess.run(
    ["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True
).stdout
pids = set()
for line in out.splitlines():
    m = re.search(r"127\.0\.0\.1:(8000|5173)\s+\S+\s+LISTENING\s+(\d+)", line)
    if m:
        pids.add(int(m.group(2)))
import os

for pid in sorted(pids):
    try:
        os.kill(pid, 9)
        print("killed", pid)
    except OSError:
        print("not there", pid)
print("done" if pids else "nothing listening")