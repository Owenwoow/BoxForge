# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **GitHub Codespaces**: one-click online run
  (<https://codespaces.new/Owenwoow/BoxForge?quickstart=1>); the dev container
  installs everything and starts the web UI automatically.
- **Test suite** (`pytest`): config validation and abuse guards, real CadQuery
  modeling, CLI export, and a headless Streamlit run of the web UI.
- Dependabot updates for GitHub Actions and the dev container.

### Changed

- CI runs lint (ruff) + tests on Python 3.11, 3.13 and 3.14, and must pass
  before a PR can merge into `main`. Tag pushes publish a GitHub Release.
- Supported Python is now **3.11–3.14** (current CadQuery dropped 3.10 and
  added 3.14).

### Removed

- Desktop app (PyInstaller builds) — use Codespaces or run from source.
- Docker image, `docker-compose.yml` and the self-hosted deployment guide.

## [0.1.0] - 2026-07-22

First public release.

### Added

- Parametric box modeling core (CadQuery): custom size, vertical corner
  fillets, top/bottom rim fillets, shelling to an open-topped box.
- Recursive BSP divider tree with per-region independent splitting.
- 45° support-free pill vents on the floor and dividers, with auto spacing and
  a solid border frame.
- Command-line entry point (`main.py` + `config.yaml`) and STL export.
- Streamlit web UI with live in-browser 3D preview on a simulated 256×256 bed,
  click-to-build divider editor, bilingual (中文 / English) interface, and a
  light / dark theme toggle.
- **Desktop app**: PyInstaller-packaged launcher (`desktop_app.py`) that runs
  the web UI locally with no Python install, plus a `--selftest` mode.
- **GitHub Actions**: CI on every push, and a release workflow that builds and
  smoke-tests desktop apps for Windows x64, Linux amd64, and macOS
  (Apple Silicon), attaching them to the GitHub Release.
- **Docker** one-command public deployment (`docker compose up -d --build`)
  with a hardened, non-root image and resource ceilings.
- Public-deploy safety: geometry-limit clamping, filename sanitization, and
  depth/size caps on the partition tree.
- Bilingual documentation (English + 简体中文) and open-source scaffolding
  (MIT license, contributing guide, issue/PR templates).

[Unreleased]: https://github.com/Owenwoow/BoxForge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Owenwoow/BoxForge/releases/tag/v0.1.0
