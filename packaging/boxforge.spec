# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the BoxForge desktop app.

Freezes box_generator/desktop_app.py (which boots Streamlit + opens a browser)
together with the whole CadQuery / OpenCASCADE (OCP) / VTK stack into a
self-contained folder. Build from the repo root:

    pip install -r requirements.txt pyinstaller
    pyinstaller packaging/boxforge.spec

Output: dist/BoxForge/  (onedir -- ship the whole folder, run BoxForge[.exe]).

onedir, not onefile: the bundle is 300 MB+ because OCP is a full compiled CAD
kernel. onefile would re-extract all of that to a temp dir on every launch
(slow) and is far more fragile with OCP's native libraries.
"""
import os

from PyInstaller.utils.hooks import collect_all, copy_metadata

# SPECPATH is injected by PyInstaller = the directory containing this spec.
REPO = os.path.dirname(os.path.abspath(SPECPATH))  # noqa: F821  (SPECPATH is a spec global)
APP = os.path.join(REPO, "box_generator")

datas: list = []
binaries: list = []
hiddenimports: list = []

# The heavy third-party stacks: pull in every submodule, data file and native
# library. VTK submodules are additionally covered by pyinstaller-hooks-contrib.
# casadi (CadQuery's assembly constraint solver) and nlopt are native
# extensions whose sibling DLLs PyInstaller's import analysis misses on its
# own -- collect_all grabs the .pyd *and* the loose DLLs it links against.
for pkg in ("streamlit", "cadquery", "OCP", "casadi", "nlopt"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Streamlit resolves its own version via importlib.metadata at runtime; without
# the dist-info copied in, it raises PackageNotFoundError on startup.
datas += copy_metadata("streamlit")

# The app's own source + config, placed at the bundle root so app.py's
# `from box_builder...` / `from main import ...` and the .streamlit/config.toml
# + config.yaml all resolve exactly as they do from source.
datas += [
    (os.path.join(APP, "app.py"), "."),
    (os.path.join(APP, "main.py"), "."),
    (os.path.join(APP, "config.yaml"), "."),
    (os.path.join(APP, "box_builder"), "box_builder"),
    (os.path.join(APP, ".streamlit"), ".streamlit"),
]

# app.py / main.py are loaded by Streamlit at runtime (not import-analyzed from
# the launcher), so their local package imports must be forced in.
hiddenimports += [
    "main",
    "box_builder",
    "box_builder.body",
    "box_builder.export",
    "box_builder.hollow",
    "box_builder.partitions",
    "box_builder.validate",
]

a = Analysis(
    [os.path.join(APP, "desktop_app.py")],
    pathex=[APP],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "tests"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BoxForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BoxForge",
)
