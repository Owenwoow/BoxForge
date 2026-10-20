# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- UI screenshots and a self-hosting guide (own GitHub Pages fork, or the
  release zip on any static host) in the README.

### Changed

- `@types/node` 24 → 26.
- Dependabot ignores TypeScript major upgrades (stay on 5.x until 7.x settles).

## [0.2.0] - 2026-10-20

Rebuilt as a static web app that runs entirely in the browser and is built,
tested and hosted on GitHub. The previous Python version is preserved on the
`legacy` branch.

### Added

- **Online at <https://owenwoow.github.io/BoxForge/>**: GitHub Pages hosting,
  deployed automatically by GitHub Actions on every merge into `main`.
- **In-browser CAD kernel**: OpenCASCADE compiled to WebAssembly (via
  replicad), running in a Web Worker so the page stays responsive.
- **Config YAML import/export** (same schema as the old CLI `config.yaml`) and
  **share links** that encode the whole design in the URL.
- Auto-corrected parameters are listed on the page instead of only logged.
- Test suite: config validation, real OpenCASCADE geometry pinned to volumes
  from the original CadQuery implementation, and Playwright end-to-end tests of
  the production build in Chromium.
- `release.yml`: version tags publish a Release with the built site as a zip.

### Changed

- Rewritten in TypeScript (React + Vite + Three.js); the modeling pipeline,
  validation rules, limits and presets are ported 1:1 from the Python version.
- CI/CD (`ci-cd.yml`): typecheck → unit tests → build → E2E on every PR and
  push; `main` additionally deploys to GitHub Pages.

### Removed

- Python implementation (CadQuery modeling core, Streamlit web UI, CLI),
  Codespaces dev container and Python tooling — see the `legacy` branch.

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

[Unreleased]: https://github.com/Owenwoow/BoxForge/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Owenwoow/BoxForge/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Owenwoow/BoxForge/releases/tag/v0.1.0
