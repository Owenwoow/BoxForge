"""BoxForge desktop launcher.

Packaged with PyInstaller (see ``packaging/boxforge.spec``) into a single
double-click executable. On launch it starts the Streamlit server locally in
headless mode and opens the default browser at the app -- no Python install,
no terminal, no ``pip`` required for the end user.

Run from source (for testing the exact frozen code path) with::

    python box_generator/desktop_app.py
"""
from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _base_dir() -> Path:
    """Directory that holds app.py / main.py / box_builder / .streamlit.

    When frozen by PyInstaller the bundled data files are unpacked into a
    temporary dir exposed as ``sys._MEIPASS``; from source it's just this
    file's own directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


PORT = int(os.environ.get("BOXFORGE_PORT", "8501"))
URL = f"http://localhost:{PORT}"


def _register_dll_dirs(base: Path) -> None:
    """Windows-only: put every bundled folder that holds DLLs on the loader's
    search path.

    PyInstaller lays some native extensions (e.g. casadi's `_casadi.pyd`) at
    the bundle root while their dependency DLLs (`libcasadi.dll` + ~90 more)
    land in a sibling `casadi/` folder. Since Python 3.8 an extension only
    auto-searches its *own* directory for DLLs, so the split breaks the load
    ("DLL load failed while importing _casadi"). Registering each DLL-bearing
    folder via os.add_dll_directory bridges that gap.
    """
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return
    add = getattr(os, "add_dll_directory", None)
    if add is None:
        return
    seen = set()
    for dll in base.rglob("*.dll"):
        d = dll.parent
        if d not in seen:
            seen.add(d)
            try:
                add(str(d))
            except OSError:
                pass


def _open_browser_when_ready() -> None:
    """Poll Streamlit's health endpoint, then open the browser once -- so the
    tab isn't opened before the server can actually answer it."""
    import urllib.request

    for _ in range(120):
        try:
            with urllib.request.urlopen(f"{URL}/_stcore/health", timeout=1) as resp:
                if resp.read() == b"ok":
                    break
        except Exception:
            pass
        time.sleep(0.5)
    webbrowser.open(URL)


def _selftest(base: Path) -> int:
    """Build the default config end-to-end and verify the solid is valid.

    Exercises the *entire* native stack (CadQuery -> OCP/OpenCASCADE -> casadi
    -> nlopt) inside the frozen binary, headlessly and deterministically -- no
    browser, no websocket. CI runs `BoxForge --selftest` on every platform so a
    missing native library fails the build instead of shipping a broken app.
    """
    from box_builder.validate import load_config
    from main import build_from_config

    cfg = load_config(str(base / "config.yaml"))
    solid = build_from_config(cfg)
    obj = solid.val()
    volume = obj.Volume()
    valid = obj.isValid()
    print(f"[selftest] volume={volume / 1000:.1f}cm^3 valid={valid}")
    if not valid or volume <= 0:
        print("[selftest] FAIL: invalid geometry", file=sys.stderr)
        return 1
    print("[selftest] PASS")
    return 0


def main() -> None:
    base = _base_dir()
    app_path = base / "app.py"

    # app.py does `from box_builder...` and `from main import ...`; both live
    # next to it. Make that dir the CWD (so the bundled .streamlit/config.toml
    # and config.yaml resolve relatively) and importable.
    os.chdir(base)
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    _register_dll_dirs(base)

    # Headless CI / packaging check: build a model and exit, skip the server.
    if "--selftest" in sys.argv or os.environ.get("BOXFORGE_SELFTEST") == "1":
        sys.exit(_selftest(base))

    from streamlit import config as st_config
    import streamlit.web.bootstrap as bootstrap

    # Pass options as flag_options -- the same channel `streamlit run` uses for
    # CLI flags, which is the *highest* precedence tier, so these win over the
    # bundled .streamlit/config.toml (that file targets the public Docker
    # deploy: it binds 0.0.0.0; a desktop app should stay on localhost).
    flag_options = {
        "server.headless": True,
        "server.port": PORT,
        "server.address": "localhost",
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
    }

    # Mirror streamlit.web.cli._main_run: register the script path, then load
    # config with our flag overrides *before* starting the server.
    main_script = os.path.abspath(str(app_path))
    st_config._main_script_path = main_script
    bootstrap.load_config_options(flag_options=flag_options)

    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    bootstrap.run(main_script, is_hello=False, args=[], flag_options=flag_options)


if __name__ == "__main__":
    main()
