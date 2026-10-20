# 项目说明

**BoxForge — 参数化 3D 收纳盒生成器（浏览器端静态网页）**

用户在网页里填参数（尺寸、圆角、递归隔板布局、镂空开关）→ 浏览器里用 OpenCASCADE（WebAssembly）建模 → 实时 3D 预览 → 下载 STL 供 3D 打印。打印板 256×256，故长宽硬性上限 250mm。收纳盒顶面开口无盖。

线上地址：https://owenwoow.github.io/BoxForge/ （GitHub Pages，由 GitHub Actions 部署）

## 架构原则
- **一切在 GitHub 上完成**：GitHub Actions 测试 + 构建，GitHub Pages 托管纯静态文件。不引入任何服务器、后端或第三方托管。
- **建模在访客浏览器里做**：replicad + replicad-opencascadejs（OCCT 的 WASM 构建），跑在 Web Worker 里。
- 旧版 Python/CadQuery/Streamlit 实现在 `legacy` 分支，只读；旧 dev 在 `legacy-dev` 分支。

## 技术栈
- TypeScript + React 19 + Vite 8；3D 预览 Three.js（打包进站点，不走 CDN）
- 测试：Vitest（Node 里跑真实 OCCT 建模）+ Playwright（Chromium 端到端）
- Node.js ≥ 22

## 目录结构
```
src/
├── core/                  # 纯 TS，无 DOM，Node 可测
│   ├── config.ts           # 配置结构（与旧 CLI 的 YAML 同构，snake_case）、校验、钳制、预设
│   └── geometry/
│       ├── oc.ts           # OCCT 初始化
│       ├── body.ts         # 盒体：圆角 + 抽壳（自定义 shellInward）
│       ├── partitions.ts   # 递归 BSP 隔板
│       ├── hollow.ts       # 45° 药丸镂空
│       └── build.ts        # 组装、统计、预览网格、STL
├── worker/                # Web Worker：持有 OCCT 和当前模型
└── ui/                    # React 界面、Three.js 预览、中英文案、分享链接
e2e/                       # Playwright 测试
.github/workflows/         # ci-cd.yml（测试 + 部署 Pages）、release.yml（标签发版）
```

## 关键约束
- **建模顺序**（改 body.ts 时务必遵守）：竖直角圆角在抽壳前做；顶口内外两条沿棱的圆角必须在抽壳**之后**做。棱边一律按方向/位置筛选，禁止按索引硬编码。
- **抽壳必须用 `shellInward`**：replicad 自带 `shell()` 传 Intersection=false，底沿圆角小于壁厚时会失败；`shellInward` 按 CadQuery 的参数（Intersection=true）直接调 OCCT。
- **基准体积测试**（`build.test.ts`）锁定了与旧版 CadQuery 一致的结果；有意改变几何时，同一次提交里更新基准值并说明原因。
- 站点用相对路径（`vite.config.ts` 的 `base: "./"`），同一份构建可部署在 Pages 子路径或任意静态主机。

## 常用命令
```
npm run dev        # 开发服务器
npm test           # 单元测试
npm run build      # 构建到 dist/
PW_CHANNEL=chrome npm run e2e   # 本机网络下载不了 Playwright 浏览器时用本机 Chrome
```

## Git 提交规范
每完成一次需求相关的改动，必须执行一次 git commit。
提交信息格式：feat: <中文介绍更新点>
（如果是修复bug用 fix:，重构用 refactor:等）
禁止把多个不相关需求的改动堆在一次提交里。
在 dev 上开发，向 dev 提 PR；成熟后向 main 提 PR，CI（Test & build）通过才能合并，合并即上线。
