"""Post-build smoke test for the frozen BoxForge desktop app.

Two checks, run in CI on every platform right after packaging so a broken
binary fails the build instead of shipping:

  1. `<exe> --selftest` -- builds the default model end-to-end, exercising the
     whole native stack (CadQuery / OCP / casadi / nlopt) headlessly. This is
     the check that catches a missing native library.
  2. Launch `<exe>` normally and wait for Streamlit's health endpoint, proving
     the desktop app actually starts its server.

Usage:
    python packaging/smoke_test.py <path-to-executable>
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORT = 8599
BASE = f"http://localhost:{PORT}"


def _selftest(exe: Path) -> bool:
    print(f"[smoke] {exe.name} --selftest (CadQuery build)")
    proc = subprocess.run(
        [str(exe), "--selftest"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    print(proc.stdout[-2000:])
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
        print("[smoke] FAIL: --selftest returned", proc.returncode, file=sys.stderr)
        return False
    return True


def _server_boots(exe: Path) -> bool:
    print(f"[smoke] {exe.name} (Streamlit server boot)")
    proc = subprocess.Popen(
        [str(exe)],
        env={**os.environ, "BOXFORGE_PORT": str(PORT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 180
        while time.time() < deadline:
            if proc.poll() is not None:
                print("[smoke] FAIL: process exited before serving", file=sys.stderr)
                return False
            try:
                with urllib.request.urlopen(f"{BASE}/_stcore/health", timeout=2) as r:
                    if r.read() == b"ok":
                        print("[smoke] server is up")
                        return True
            except Exception:
                pass
            time.sleep(2)
        print("[smoke] FAIL: health check timed out", file=sys.stderr)
        return False
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: smoke_test.py <executable>", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1])
    if not exe.exists():
        print(f"executable not found: {exe}", file=sys.stderr)
        return 2

    if not _selftest(exe):
        return 1
    if not _server_boots(exe):
        return 1
    print("[smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
