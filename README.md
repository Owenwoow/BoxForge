<div align="center">

# 🗃️ BoxForge

**Parametric 3D storage-box generator — rounded corners, recursive dividers, support-free 45° pill vents, straight to a printable STL.**

[![CI](https://github.com/Owenwoow/BoxForge/actions/workflows/ci.yml/badge.svg)](https://github.com/Owenwoow/BoxForge/actions/workflows/ci.yml)
[![Build desktop apps](https://github.com/Owenwoow/BoxForge/actions/workflows/build-desktop.yml/badge.svg)](https://github.com/Owenwoow/BoxForge/actions/workflows/build-desktop.yml)
[![Latest release](https://img.shields.io/github/v/release/Owenwoow/BoxForge?include_prereleases&sort=semver)](https://github.com/Owenwoow/BoxForge/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://www.python.org/)

<img src="docs/images/hero_render.png" alt="BoxForge sample box" width="640">

**English** · [简体中文](README.zh-CN.md)

</div>

---

## Table of contents

- [What is this?](#what-is-this)
- [Features](#features)
- [Screenshots](#screenshots)
- [Get started](#get-started)
  - [Option 1 — Desktop app (no Python)](#option-1--desktop-app-no-python)
  - [Option 2 — Run from source](#option-2--run-from-source)
  - [Option 3 — Docker (public deploy)](#option-3--docker-public-deploy)
- [Documentation](#documentation)
- [Project structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## What is this?

BoxForge turns a handful of parameters into a custom storage box and exports a **3D-printable STL**. Fill in the size, round the corners, drop in dividers wherever you want, punch support-free vent holes into the floor and dividers — then download and print.

It ships in two forms that share the exact same modeling engine:

| Mode | Best for | Entry point |
|---|---|---|
| **Web UI** (Streamlit) | tweaking by hand with a live 3D preview | `streamlit run box_generator/app.py` |
| **Command line** | scripting, batch generation, automation | `python box_generator/main.py config.yaml` |

The geometry is built with [CadQuery](https://github.com/CadQuery/cadquery) — a real OpenCASCADE B-rep CAD kernel, **not** a mesh library — so fillets, shelling and boolean cuts are solid and reliable.

> Storage boxes are **open-topped (no lid)** by design. Length and width are hard-capped at **250 mm** to fit a 256×256 print bed.

## Features

- **Custom dimensions** — length / width / height / wall thickness, all parametric.
- **Two independent fillet types** — rounded vertical corners (phone-case style) *and* rounded top/bottom horizontal rims (won't cut your hand). The top rim rounds **both** the inner and outer lip.
- **Recursive dividers (BSP tree)** — split any region along X or Y, then recursively split any sub-region independently. One-click presets for halves and a 2×2 cross.
- **45° support-free pill vents** — staggered capsule holes on the floor and/or dividers, auto-spaced with a solid border frame. The 45° angle self-bridges so it prints without supports. Outer walls are never vented.
- **Live 3D preview** — the web UI shows the model on a simulated 256×256 print bed (Bambu-Studio style); rotate/zoom in-browser.
- **Bilingual UI + light/dark theme** — switch 中文 / English and light / dark on the fly.
- **Input hardening** — geometry limits are auto-clamped, filenames sanitized, and the partition tree is depth/size-capped, so it's safe to expose publicly.

## Screenshots

> 📌 **Add your own UI screenshots here.** Run the web UI, take a full-window screenshot, save it to the path below, and uncomment the line.

<!-- ![Web UI overview](docs/images/ui_overview.png) -->
`docs/images/ui_overview.png` *(to add — ~1200px wide recommended)*

## Get started

### Option 1 — Desktop app (no Python)

The easiest way for non-developers. Download the prebuilt app for your OS from the [**latest release**](https://github.com/Owenwoow/BoxForge/releases/latest), unzip, and run `BoxForge` — it starts a local server and opens the web UI in your browser automatically. No Python, no `pip`.

| Platform | Download |
|---|---|
| Windows x64 | `BoxForge-windows-x64.zip` |
| Linux amd64 | `BoxForge-linux-amd64.tar.gz` |
| macOS (Apple Silicon) | `BoxForge-macos-arm64.tar.gz` |

> Intel Macs: run [from source](#option-2--run-from-source) or via [Docker](#option-3--docker-public-deploy).

See the [Desktop app guide](docs/desktop-app.md) for run instructions and OS security prompts.

### Option 2 — Run from source

```bash
# Python 3.10–3.13 required (not 3.14 — CadQuery has no wheel for it yet)
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge

python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS / Linux:       source .venv/bin/activate
pip install -r requirements.txt

# Web UI  ->  http://localhost:8501
streamlit run box_generator/app.py

# …or the command line
python box_generator/main.py box_generator/config.yaml   # writes box_output.stl
```

Full walkthrough: [Installation guide](docs/installation.md).

### Option 3 — Docker (public deploy)

To host the web UI for others on a server:

```bash
docker compose up -d --build
# -> web UI on http://<server-ip>:8501
```

The image is hardened for public exposure (non-root, resource ceilings, bounded caches, input abuse guards). Put a TLS-terminating reverse proxy in front of port `8501`. Full guide: [Deployment guide](docs/deployment.md).

## Documentation

| Guide | English | 简体中文 |
|---|---|---|
| Install & run from source | [installation.md](docs/installation.md) | [installation.zh-CN.md](docs/installation.zh-CN.md) |
| Desktop app (prebuilt) | [desktop-app.md](docs/desktop-app.md) | [desktop-app.zh-CN.md](docs/desktop-app.zh-CN.md) |
| Parameters & usage reference | [usage.md](docs/usage.md) | [usage.zh-CN.md](docs/usage.zh-CN.md) |
| Public deployment (Docker) | [deployment.md](docs/deployment.md) | [deployment.zh-CN.md](docs/deployment.zh-CN.md) |

## Project structure

```
BoxForge/
├── box_generator/
│   ├── config.yaml            # sample config for the CLI
│   ├── main.py                # CLI entry point
│   ├── app.py                 # Streamlit web UI entry point
│   ├── desktop_app.py         # desktop launcher (packaged by PyInstaller)
│   ├── .streamlit/            # Streamlit config (public-deploy hardening)
│   └── box_builder/
│       ├── validate.py         # YAML validation + safe clamping
│       ├── body.py             # box body: fillets + shell
│       ├── partitions.py       # recursive BSP dividers
│       ├── hollow.py           # 45° pill-vent arrays
│       └── export.py           # STL export
├── packaging/                 # PyInstaller spec + smoke test
├── docs/                      # guides (EN + 简体中文)
├── Dockerfile · docker-compose.yml
└── .github/workflows/         # CI + desktop-app release builds
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup, branch model (`dev` for work, `main` for releases), and commit conventions. Open an [issue](https://github.com/Owenwoow/BoxForge/issues) for bugs and feature requests.

## License

Released under the [MIT License](LICENSE).
