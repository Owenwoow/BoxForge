# Contributing to BoxForge

Thanks for your interest in improving BoxForge! This guide covers the dev setup, branch model, and conventions. / 感谢参与！本文说明开发环境、分支模型与约定。

## Branch model / 分支模型

- **`main`** — release branch. Only finished, working code and user-facing docs. Every commit should be shippable. Release tags (`vX.Y.Z`) are cut from here and trigger the desktop-app builds.
- **`dev`** — development branch. Where day-to-day work happens; also holds dev-only material (design/spec docs, AI/editor tooling) that doesn't belong in a clean release tree.

Work on `dev` (or a feature branch off `dev`), then open a PR into `dev`. Changes are promoted to `main` when they're release-ready.

> **`main`** = 只放正式、可用的代码和面向用户的文档；发布 tag 从这里打。**`dev`** = 日常开发分支，同时存放开发期材料（设计/执行方案、编辑器工具等）。请在 `dev` 上开发并向 `dev` 提 PR，成熟后再合入 `main`。

## Dev setup / 开发环境

```bash
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge
git checkout dev

python -m venv .venv          # Python 3.11–3.14
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS / Linux:       source .venv/bin/activate
pip install -r requirements-dev.txt   # runtime deps + pytest + ruff
```

Run the app while developing:

```bash
streamlit run box_generator/app.py                 # web UI
python box_generator/main.py box_generator/config.yaml   # CLI
```

## Before you push / 提交前自检

Run the same checks CI runs:

```bash
ruff check .                                       # lint
pytest                                             # validation, modeling, web UI tests
pytest -m "not slow"                               # just the fast validation tests
python box_generator/desktop_app.py --selftest     # desktop launcher self-test
```

## CI/CD / 持续集成与发布

Everything is built, tested and published by GitHub Actions — nothing is built by hand. / 构建、测试、发布全部由 GitHub Actions 完成，不需要手动构建。

| Trigger / 触发 | What runs / 执行内容 | Output / 产物 |
|---|---|---|
| PR into `dev` / `main` | lint + tests (Python 3.11 / 3.13 / 3.14) + Docker build & smoke test | — |
| push to `dev` | same, then publish image | `ghcr.io/owenwoow/boxforge:dev` |
| push to `main` | same, then publish image | `ghcr.io/owenwoow/boxforge:edge` |
| push tag `vX.Y.Z` | same + desktop builds (Windows / Linux / macOS) | image `:X.Y.Z` `:X.Y` `:latest` + GitHub Release |

Workflows: [`ci.yml`](.github/workflows/ci.yml) (tests + Docker image) and [`build-desktop.yml`](.github/workflows/build-desktop.yml) (desktop apps + Release). Dependabot opens weekly PRs into `dev` for Action and base-image updates.

### Cutting a release / 发版步骤

1. Merge `dev` into `main` and wait for CI to go green. / 把 `dev` 合入 `main`，等 CI 通过。
2. Move the `[Unreleased]` notes in `CHANGELOG.md` under a new version heading. / 在 `CHANGELOG.md` 里把 `[Unreleased]` 的内容移到新版本号下。
3. Tag and push — Actions does the rest. / 打标签并推送，其余交给 Actions：

```bash
git tag v0.2.0
git push origin v0.2.0
```

A tag with a suffix such as `v0.2.0-rc.1` is published as a pre-release and does not move `:latest`. / 带后缀的标签（如 `v0.2.0-rc.1`）发布为预发布版，不会更新 `:latest`。

## Commit convention / 提交规范

Use a type prefix and a concise description:

- `feat:` a new feature
- `fix:` a bug fix
- `refactor:` code change that neither fixes a bug nor adds a feature
- `docs:` documentation only
- `chore:` build/tooling/CI

Keep one logical change per commit; don't bundle unrelated changes. / 每次提交只做一件事，不要把不相关的改动堆在一起。

## Building the desktop app locally / 本地打包桌面版

```bash
pip install pyinstaller
pyinstaller packaging/boxforge.spec --noconfirm
python packaging/smoke_test.py dist/BoxForge/BoxForge   # (BoxForge.exe on Windows)
```

## Reporting issues / 反馈问题

Open an [issue](https://github.com/Owenwoow/BoxForge/issues) with steps to reproduce, your OS, Python version, and the relevant config/YAML.
