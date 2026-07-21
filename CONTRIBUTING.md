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

python -m venv .venv          # Python 3.10–3.13 (not 3.14)
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS / Linux:       source .venv/bin/activate
pip install -r requirements.txt
```

Run the app while developing:

```bash
streamlit run box_generator/app.py                 # web UI
python box_generator/main.py box_generator/config.yaml   # CLI
```

## Before you push / 提交前自检

Run the same checks CI runs:

```bash
python -m compileall box_generator                 # syntax
python box_generator/desktop_app.py --selftest     # full CadQuery build
```

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
