# Contributing to BoxForge

Thanks for your interest in improving BoxForge! This guide covers the dev setup, branch model, and conventions. / 感谢参与！本文说明开发环境、分支模型与约定。

## Branch model / 分支模型

- **`main`** — release branch. Only finished, working code and user-facing docs. Every commit should be shippable. Release tags (`vX.Y.Z`) are cut from here.
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
```

## CI/CD / 持续集成与发布

Everything runs on GitHub — nothing is built or deployed by hand. / 一切都在 GitHub 上完成，不需要手动构建或部署。

| Trigger / 触发 | What runs / 执行内容 |
|---|---|
| PR into `dev` / `main`, push to `dev` / `main` | [`ci.yml`](.github/workflows/ci.yml): ruff + pytest on Python 3.11 / 3.13 / 3.14 — must pass before a PR can merge into `main` / 合入 `main` 前必须通过 |
| push tag `vX.Y.Z` | [`release.yml`](.github/workflows/release.yml): GitHub Release with generated notes / 自动生成说明并发布 Release |

The web UI runs in [GitHub Codespaces](https://codespaces.new/Owenwoow/BoxForge?quickstart=1), configured by [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json). Dependabot opens weekly PRs into `dev` for Action and dev-container updates. / 网页界面在 GitHub Codespaces 中运行；Dependabot 每周向 `dev` 提更新 PR。

### Cutting a release / 发版步骤

1. Merge `dev` into `main` and wait for CI to go green. / 把 `dev` 合入 `main`，等 CI 通过。
2. Move the `[Unreleased]` notes in `CHANGELOG.md` under a new version heading. / 在 `CHANGELOG.md` 里把 `[Unreleased]` 的内容移到新版本号下。
3. Tag and push — Actions publishes the Release. / 打标签并推送，Actions 自动发布 Release：

```bash
git tag v0.2.0
git push origin v0.2.0
```

A tag with a suffix such as `v0.2.0-rc.1` is published as a pre-release. / 带后缀的标签（如 `v0.2.0-rc.1`）发布为预发布版。

## Commit convention / 提交规范

Use a type prefix and a concise description:

- `feat:` a new feature
- `fix:` a bug fix
- `refactor:` code change that neither fixes a bug nor adds a feature
- `docs:` documentation only
- `chore:` build/tooling/CI

Keep one logical change per commit; don't bundle unrelated changes. / 每次提交只做一件事，不要把不相关的改动堆在一起。

## Reporting issues / 反馈问题

Open an [issue](https://github.com/Owenwoow/BoxForge/issues) with steps to reproduce, your OS, Python version, and the relevant config/YAML.
