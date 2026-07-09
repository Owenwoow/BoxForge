<div align="center">

# 🗃️ BoxForge

**Parametric 3D storage-box generator — rounded corners, recursive dividers, support-free 45° pill vents, straight to printable STL.**

**参数化 3D 收纳盒生成器 —— 圆角、递归隔板、45° 免支撑药丸镂空，一键导出可打印 STL。**

<img src="docs/images/hero_render.png" alt="BoxForge sample box" width="640">

English | [中文](#-中文说明)

</div>

---

## ✨ What is this?

BoxForge turns a handful of parameters into a custom storage box and exports a **3D-printable STL**. Fill in the size, round the corners, drop in dividers wherever you want, punch support-free vent holes into the floor and dividers — then download and print.

It ships in two forms that share the exact same modeling engine:

| Mode | Best for | Entry point |
|---|---|---|
| **Command line** | scripting, batch generation, automation | `box_generator/main.py` + `config.yaml` |
| **Web UI** (Streamlit) | tweaking by hand with a live 3D preview | `streamlit run box_generator/app.py` |

The geometry is built with [CadQuery](https://github.com/CadQuery/cadquery) (a real OpenCASCADE B-rep CAD kernel — **not** a mesh library), so fillets, shelling and boolean cuts are solid and reliable.

## 🎯 Features

- **Custom dimensions** — length / width / height / wall thickness, all parametric. Length & width are hard-capped at **250 mm** to fit a 256×256 print bed.
- **Two independent fillet types** — rounded vertical corners (phone-case style) *and* rounded top/bottom horizontal rims (won't cut your hand). The top rim rounds **both** the inner and outer lip.
- **Recursive dividers (BSP tree)** — split any region along X or Y, then recursively split any sub-region independently. Presets for halves and a 2×2 cross are one click away.
- **45° support-free pill vents** — fixed-length staggered capsule holes on the floor and/or dividers, auto-spaced with a solid border frame. The 45° angle self-bridges so it prints without supports. Outer walls are never vented.
- **Live 3D preview** — the web UI shows the model on a simulated 256×256 print bed (Bambu-Studio style), rotate/zoom in-browser.
- **Bilingual UI** — switch between 中文 / English on the fly.

## 📸 Screenshots

> 📌 **Add your own UI screenshots here.** Run `streamlit run box_generator/app.py`, take a full-window screenshot, save it as the path below, and uncomment the line. (Two placeholder paths are already referenced so the layout is ready.)

**Web UI overview** — left sidebar = parameters, right = live 3D preview + download button.

<!-- Save your screenshot to docs/images/ui_overview.png, then uncomment: -->
<!-- ![Web UI overview](docs/images/ui_overview.png) -->
`docs/images/ui_overview.png` *(to add — 建议约 1200px 宽)*

**Divider editor** — click-to-build partitions with a live top-down diagram.

<!-- Save your screenshot to docs/images/ui_partitions.png, then uncomment: -->
<!-- ![Partition builder](docs/images/ui_partitions.png) -->
`docs/images/ui_partitions.png` *(to add)*

## 🚀 Quick start

```bash
# 1. Create and activate a virtual environment (Python 3.10–3.13)
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):        .venv\Scripts\activate.bat
# macOS / Linux:        source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3a. Web UI  ->  open http://localhost:8501
cd box_generator
streamlit run app.py

# 3b. …or the command line
python main.py config.yaml   # writes box_output.stl
```

> ⚠️ Use **Python 3.10–3.13**. CadQuery has no prebuilt wheel for 3.14 yet, so it won't install there.

## 🐳 Deploy on a public VPS (Docker, one command)

For hosting the web UI for others to use, ship it with Docker instead of a bare `streamlit run`:

```bash
# From the repo root:
docker compose up -d --build
# -> web UI on http://<server-ip>:8501
```

Then put a TLS-terminating reverse proxy (Nginx / Caddy / Traefik) in front of port `8501`.

The image is hardened for public exposure:

- **Runs as a non-root user**, telemetry off, dev toolbar and error stack traces hidden.
- **Hard CPU/RAM/PID ceiling** (`docker-compose.yml`) so one heavy CadQuery build can't take the host down — model building is deliberately expensive.
- **Bounded caches & disk** — generated STL previews live in a size-capped `tmpfs`, and old previews/models are pruned automatically.
- **Abuse guards in validation** — the partition tree (which can be pasted as raw YAML) is capped in depth and node count, and export filenames are sanitized against path traversal.

See the full guide for reverse-proxy configs and tuning: [docs/DEPLOYMENT_AND_USAGE.md](docs/DEPLOYMENT_AND_USAGE.md)

📖 **Full step-by-step deployment & usage guide:** [docs/DEPLOYMENT_AND_USAGE.md](docs/DEPLOYMENT_AND_USAGE.md)

## 📁 Project structure

```
BoxForge/
├── requirements.txt
├── box_generator/
│   ├── config.yaml            # sample config for the CLI
│   ├── main.py                # CLI entry point
│   ├── app.py                 # Streamlit web UI entry point
│   └── box_builder/
│       ├── validate.py         # YAML validation + safe clamping
│       ├── body.py             # box body: fillets + shell
│       ├── partitions.py       # recursive BSP dividers
│       ├── hollow.py           # 45° pill-vent arrays
│       └── export.py           # STL export
└── docs/                       # this guide + the design/spec docs
```

---

<div align="center">

## 📖 中文说明

English | [中文](#-中文说明)

</div>

## ✨ 这是什么？

BoxForge 把几个参数变成一个定制收纳盒，并导出**可 3D 打印的 STL**。填好尺寸、把四角磨圆、在任意位置加隔板、在底面和隔板上打免支撑的透气孔，然后下载打印即可。

它提供两种形态，共用同一套建模引擎：

| 方式 | 适合场景 | 入口 |
|---|---|---|
| **命令行** | 写脚本、批量生成、自动化 | `box_generator/main.py` + `config.yaml` |
| **网页界面**（Streamlit） | 手动调参 + 实时 3D 预览 | `streamlit run box_generator/app.py` |

几何建模基于 [CadQuery](https://github.com/CadQuery/cadquery)（真正的 OpenCASCADE B-rep CAD 内核，**不是** mesh 网格库），所以圆角、抽壳、布尔运算都稳健可靠。

## 🎯 功能特性

- **自定义尺寸** —— 长 / 宽 / 高 / 壁厚全部参数化。长宽硬性上限 **250 mm**，适配 256×256 打印板。
- **两类独立圆角** —— 竖直四角圆角（手机壳那种）*和* 顶/底水平棱圆角（不割手）。顶沿会**同时**倒内外两条棱。
- **递归隔板（BSP 树）** —— 沿 X 或 Y 切分任意区域，切完的每个子区域还能独立继续细分。对半分、十字四格等预设一键生成。
- **45° 免支撑药丸镂空** —— 底面和/或隔板上的固定长度交错胶囊孔，自动排布并保留一圈实心边框。45° 角能自架桥，无需支撑即可打印。外墙永不镂空。
- **实时 3D 预览** —— 网页界面把模型放在模拟的 256×256 打印板上（仿 Bambu Studio 效果），可在浏览器里旋转缩放。
- **中英双语界面** —— 可随时切换中文 / English。

## 📸 界面截图

> 📌 **在这里放你自己的界面截图。** 运行 `streamlit run box_generator/app.py`，对整窗截图，保存到下面的路径，然后取消对应行的注释即可。（占位路径已经写好，版式现成的。）

**网页界面总览** —— 左侧栏是参数，右侧是实时 3D 预览 + 下载按钮。

<!-- 把截图存到 docs/images/ui_overview.png，然后取消下一行注释： -->
<!-- ![网页界面总览](docs/images/ui_overview.png) -->
`docs/images/ui_overview.png` *(待补 —— 建议约 1200px 宽)*

**隔板编辑器** —— 点击式加隔板，配实时俯视图。

<!-- 把截图存到 docs/images/ui_partitions.png，然后取消下一行注释： -->
<!-- ![隔板编辑器](docs/images/ui_partitions.png) -->
`docs/images/ui_partitions.png` *(待补)*

## 🚀 快速开始

```bash
# 1. 创建并激活虚拟环境（Python 3.10–3.13）
python -m venv .venv
# Windows（PowerShell）：
.venv\Scripts\Activate.ps1
# Windows（cmd）：       .venv\Scripts\activate.bat
# macOS / Linux：        source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3a. 网页界面  ->  浏览器打开 http://localhost:8501
cd box_generator
streamlit run app.py

# 3b. …或走命令行
python main.py config.yaml   # 生成 box_output.stl
```

> ⚠️ 请使用 **Python 3.10–3.13**。CadQuery 目前没有 3.14 的预编译包，在 3.14 上装不上。

📖 **完整的分步部署与使用教程：** [docs/DEPLOYMENT_AND_USAGE.md](docs/DEPLOYMENT_AND_USAGE.md)

## 📁 项目结构

```
BoxForge/
├── requirements.txt
├── box_generator/
│   ├── config.yaml            # 命令行用的样例配置
│   ├── main.py                # 命令行入口
│   ├── app.py                 # Streamlit 网页界面入口
│   └── box_builder/
│       ├── validate.py         # YAML 校验 + 安全钳制
│       ├── body.py             # 盒体：圆角 + 抽壳
│       ├── partitions.py       # 递归 BSP 隔板
│       ├── hollow.py           # 45° 药丸镂空阵列
│       └── export.py           # STL 导出
└── docs/                       # 本教程 + 设计/执行方案文档
```

## 📄 License

_No license chosen yet — add a `LICENSE` file (e.g. MIT) if you want others to reuse this._
_尚未选择开源协议——如需他人复用，请自行添加 `LICENSE` 文件（例如 MIT）。_
