# Contributing to BoxForge

Thanks for your interest in improving BoxForge! This guide covers the dev setup, branch model, CI/CD and conventions. / 感谢参与！本文说明开发环境、分支模型、CI/CD 与约定。

## Branch model / 分支模型

- **`main`** — what's live. Every merge into `main` is deployed to GitHub Pages automatically, so it must always be shippable. Protected: a PR can only merge once CI passes. / 线上版本；每次合入都会自动部署，受保护，CI 通过才能合并。
- **`dev`** — day-to-day development; also holds dev-only material (design notes, editor/AI tooling) that doesn't belong in the release tree. / 日常开发分支，同时存放开发期材料。
- **`legacy`** — frozen snapshot of the previous Python/CadQuery/Streamlit version. Read-only. / 旧版 Python 实现的冻结快照，只读保留。

Work on `dev` (or a feature branch off `dev`) and open PRs into `dev`; promote to `main` with a PR when ready. / 在 `dev` 上开发并向 `dev` 提 PR，成熟后再向 `main` 提 PR。

## Dev setup / 开发环境

Node.js 22+ is required. / 需要 Node.js 22 或更新版本。

```bash
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge
git checkout dev
npm install
npm run dev            # http://localhost:5173
```

## Before you push / 提交前自检

Run the same checks CI runs: / 运行与 CI 相同的检查：

```bash
npm run typecheck      # TypeScript
npm test               # unit tests: validation + real OpenCASCADE geometry
npm run build          # production build
npx playwright install chromium   # once
npm run e2e            # production build in a real browser
```

> Can't download Playwright's browser? Reuse an installed Chrome: `PW_CHANNEL=chrome npm run e2e`. / 下载不了 Playwright 自带浏览器时，可用本机 Chrome：`PW_CHANNEL=chrome npm run e2e`。

When changing geometry (`src/core/geometry/`), keep the reference-volume tests in `build.test.ts` passing — they pin the output to the original CadQuery implementation. If a change is meant to alter the geometry, update the reference numbers in the same commit and say why. / 修改建模代码时，`build.test.ts` 里的基准体积测试必须保持通过；若有意改变几何结果，请在同一次提交中更新基准值并说明原因。

## CI/CD / 持续集成与部署

Everything runs on GitHub — nothing is built, deployed or hosted by hand. / 构建、测试、部署、托管全部在 GitHub 上完成。

| Trigger / 触发 | Workflow | What runs / 执行内容 |
|---|---|---|
| PR into `dev` / `main`, push to `dev` | [`ci-cd.yml`](.github/workflows/ci-cd.yml) | typecheck → unit tests → build → Chromium E2E |
| push to `main` (i.e. a merged PR) | [`ci-cd.yml`](.github/workflows/ci-cd.yml) | the same, then **deploy to GitHub Pages** |
| push tag `vX.Y.Z` | [`release.yml`](.github/workflows/release.yml) | tests + build, then a GitHub Release with `boxforge-site-vX.Y.Z.zip` |

- Live site / 线上地址: <https://owenwoow.github.io/BoxForge/>
- The `Test & build` check is required before merging into `main`. / 合入 `main` 前必须通过 `Test & build` 检查。
- Dependabot opens weekly PRs into `dev` for npm packages and GitHub Actions. / Dependabot 每周向 `dev` 提依赖更新 PR。

### Cutting a release / 发版步骤

1. Merge `dev` into `main` via PR and wait for the deploy to finish. / 通过 PR 把 `dev` 合入 `main`，等部署完成。
2. Move the `[Unreleased]` notes in `CHANGELOG.md` under a new version heading, and bump `version` in `package.json`. / 把 `CHANGELOG.md` 中 `[Unreleased]` 的内容移到新版本号下，并更新 `package.json` 的 `version`。
3. Tag and push — Actions publishes the Release. / 打标签并推送，Actions 自动发布 Release：

```bash
git tag v0.3.0
git push origin v0.3.0
```

A tag with a suffix such as `v0.3.0-rc.1` is published as a pre-release. / 带后缀的标签（如 `v0.3.0-rc.1`）发布为预发布版。

## Commit convention / 提交规范

Use a type prefix and a concise description:

- `feat:` a new feature
- `fix:` a bug fix
- `refactor:` code change that neither fixes a bug nor adds a feature
- `docs:` documentation only
- `test:` tests only
- `chore:` / `ci:` build, tooling, CI

Keep one logical change per commit; don't bundle unrelated changes. / 每次提交只做一件事，不要把不相关的改动堆在一起。

## Reporting issues / 反馈问题

Open an [issue](https://github.com/Owenwoow/BoxForge/issues) with steps to reproduce, your browser and OS, and the config YAML (Export & config → Download config YAML) or a share link. / 提 issue 时请附复现步骤、浏览器与系统，以及配置 YAML 或分享链接。
