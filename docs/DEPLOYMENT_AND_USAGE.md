# BoxForge — Deployment & Usage Guide / 部署与使用教程

English | [中文](#中文教程)

This guide walks you from a clean machine all the way to a printable STL, with an emphasis on **setting up a Python virtual environment and installing the libraries into it**. No prior Python-tooling experience assumed.

For the full parameter reference (every YAML field, limits, partition-tree syntax, print tips), see the deeper manual: [参数化收纳盒生成器_使用手册.md](参数化收纳盒生成器_使用手册.md).

---

## 1. Prerequisites

| Tool | Version / note |
|---|---|
| **Python** | **3.10 – 3.13**. ⚠️ Not 3.14 — CadQuery has no prebuilt wheel for it yet and the install will fail. |
| **git** | any recent version (to clone the repo) |
| OS | Windows / macOS / Linux all work |

Check which Python versions you have:

```bash
# Windows
py -0p
# macOS / Linux
python3 --version
```

If your default `python` is 3.14 (or 2.x), note the path to a 3.10–3.13 interpreter — you'll point `venv` at it explicitly in the next step.

---

## 2. Get the code

```bash
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge
```

---

## 3. Create a virtual environment

A **virtual environment** (venv) is an isolated, project-local Python with its own set of installed packages. It keeps CadQuery and its large binary dependencies out of your system Python and away from other projects. We create it once, in a `.venv` folder at the repo root.

```bash
# Use a specific interpreter if your default isn't 3.10–3.13.
# Windows example, forcing Python 3.13:
py -3.13 -m venv .venv
#   or simply:  python -m venv .venv   (if your default python is already 3.10–3.13)

# macOS / Linux:
python3 -m venv .venv
```

This creates a `.venv/` directory. You only do this **once** per clone.

---

## 4. Activate the virtual environment

Activating makes `python` and `pip` in your terminal point at the venv's copies instead of the system ones. You do this **every time you open a new terminal** to work on the project.

| Shell | Command |
|---|---|
| **Windows PowerShell** | `.venv\Scripts\Activate.ps1` |
| **Windows cmd.exe** | `.venv\Scripts\activate.bat` |
| **macOS / Linux (bash/zsh)** | `source .venv/bin/activate` |

After activating, your prompt is prefixed with `(.venv)`.

> **PowerShell "running scripts is disabled" error?** Run this once for your user, then activate again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

> **Prefer not to activate?** You can always call the venv's tools by full path instead, e.g.
> `.venv\Scripts\python.exe box_generator\main.py` or `.venv\Scripts\streamlit.exe run box_generator\app.py`.

To leave the venv later: `deactivate`.

---

## 5. Install the libraries into the venv

With the venv **activated**:

```bash
pip install -r requirements.txt
```

This installs:

- **cadquery** — the CAD kernel that does all the modeling (fillets, shell, boolean cuts, STL export). It pulls in OpenCASCADE + VTK binaries, so this download is **large (several hundred MB)** and can take a few minutes. That's normal — don't cancel it.
- **pyyaml** — reads the YAML config.
- **streamlit** — the web UI. (The 3D preview uses Three.js loaded from a CDN, so there's no extra heavy Python 3D dependency.)

> **`pip install cadquery` fails or hangs?**
> - Double-check your Python is 3.10–3.13 (`python --version`).
> - As a fallback, install via conda: `conda install -c conda-forge -c cadquery cadquery`.

---

## 6. Verify the install

```bash
python -c "import cadquery as cq; print(cq.Workplane('XY').box(10,10,10).val().Volume())"
```

Prints something like `999.99…` → CadQuery is working.

---

## 7. Run it

### Option A — Web UI (recommended for exploring)

```bash
cd box_generator
streamlit run app.py
```

Streamlit prints a local URL (default **http://localhost:8501**) — open it in your browser. Drag the sliders on the left, watch the 3D preview on the right, click **Download STL** when happy.

- The server is local-only by default (only your machine's browser can reach it).
- To pick a different port: `streamlit run app.py --server.port 8600`.
- To let other devices on your LAN reach it: `streamlit run app.py --server.address 0.0.0.0` (then browse to your machine's IP).

Stop the server with `Ctrl+C`.

### Option B — Command line

```bash
cd box_generator
python main.py config.yaml     # or just: python main.py  (defaults to config.yaml)
```

On success it prints `Exported box_output.stl`. Edit `config.yaml`, re-run, get a new model. You can point it at any config file: `python main.py my_box.yaml`.

---

## 8. Editing the config (CLI mode)

`box_generator/config.yaml` is the only thing you edit for CLI use. Minimal example:

```yaml
box:
  size: [120, 80, 40]     # [length, width, height] mm — length/width must be ≤ 250
  wall: 2                 # wall thickness mm
  corner_radius: 5        # vertical corner fillet mm (0 = square)
  edge_fillet:
    top: 1                # top rim fillet mm (≤ wall/2)
    bottom: 1             # bottom rim fillet mm

partitions: null          # null = no dividers (see the manual for the tree syntax)

hollow:
  hole_size: 8            # pill vent width mm
  angle: 45               # fixed at 45, don't change
  border: auto            # auto solid frame (or a number for a fixed border mm)
  faces:
    bottom: true          # vent the floor?
    partitions: true      # vent the dividers?

export:
  format: stl
  tolerance: 0.1          # arc detail — smaller = smoother = bigger file
  filename: box_output.stl
```

Full field-by-field reference (partition tree, limits, auto-clamping behavior, print advice): [参数化收纳盒生成器_使用手册.md](参数化收纳盒生成器_使用手册.md).

---

## 9. Everyday workflow after first setup

```bash
cd BoxForge
.venv\Scripts\Activate.ps1        # (or your shell's activate command)
cd box_generator
streamlit run app.py              # …or: python main.py config.yaml
```

That's it — you don't recreate the venv or reinstall packages; just activate and run.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `'streamlit' is not recognized` | The venv isn't activated (streamlit lives inside `.venv`). Activate it, or call `.venv\Scripts\streamlit.exe run app.py` by full path. |
| `pip install cadquery` won't install | Ensure Python 3.10–3.13; else use the conda fallback (step 5). |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| CLI: `box length/width must be <= 250.0mm` | The design is bigger than the print bed allows — this is a hard reject, not auto-shrunk. Reduce `size`. |
| Web preview area is blank | The 3D viewer loads Three.js from `cdn.jsdelivr.net`; if that's unreachable the model still generates (stats show below) — just download the STL and preview in your slicer. |
| Slicer says a hollow face needs supports | Check you didn't set `corner_radius`/`edge_fillet` to extreme values creating unintended overhangs; the 45° pill vents themselves are support-free by design. |

---
---

# 中文教程

[English](#boxforge--deployment--usage-guide--部署与使用教程) | 中文

本教程带你从一台干净的电脑一路走到可打印的 STL，**重点讲如何创建 Python 虚拟环境并把依赖库装进去**。不需要任何 Python 工具链基础。

完整的参数说明（每个 YAML 字段、取值上限、隔板树语法、打印建议）见更详细的手册：[参数化收纳盒生成器_使用手册.md](参数化收纳盒生成器_使用手册.md)。

---

## 1. 环境要求

| 工具 | 版本 / 说明 |
|---|---|
| **Python** | **3.10 – 3.13**。⚠️ 不要用 3.14 —— CadQuery 还没有对应的预编译包，会装不上。 |
| **git** | 任意较新版本（用来克隆仓库） |
| 操作系统 | Windows / macOS / Linux 都可以 |

查看你装了哪些 Python 版本：

```bash
# Windows
py -0p
# macOS / Linux
python3 --version
```

如果默认的 `python` 是 3.14（或 2.x），记下某个 3.10–3.13 解释器的位置——下一步创建 venv 时要显式指定它。

---

## 2. 获取代码

```bash
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge
```

---

## 3. 创建虚拟环境

**虚拟环境**（venv）是一个隔离的、项目本地的 Python，有自己独立的一套已安装的包。它能把 CadQuery 及其庞大的二进制依赖跟你的系统 Python、以及其他项目隔离开。我们只在仓库根目录建一次，放在 `.venv` 文件夹里。

```bash
# 如果默认解释器不是 3.10–3.13，就指定一个。
# Windows 示例，强制用 Python 3.13：
py -3.13 -m venv .venv
#   或者直接：  python -m venv .venv  （如果你的默认 python 已经是 3.10–3.13）

# macOS / Linux：
python3 -m venv .venv
```

这会生成一个 `.venv/` 目录。每次克隆**只需做一次**。

---

## 4. 激活虚拟环境

激活之后，终端里的 `python` 和 `pip` 就指向 venv 里的那份，而不是系统的。**每次新开终端**来做这个项目时都要先激活。

| Shell | 命令 |
|---|---|
| **Windows PowerShell** | `.venv\Scripts\Activate.ps1` |
| **Windows cmd.exe** | `.venv\Scripts\activate.bat` |
| **macOS / Linux（bash/zsh）** | `source .venv/bin/activate` |

激活后，命令行提示符前会出现 `(.venv)`。

> **PowerShell 报“禁止运行脚本”？** 给当前用户执行一次下面的命令，然后重新激活：
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

> **不想激活？** 也可以始终用完整路径调用 venv 里的工具，例如
> `.venv\Scripts\python.exe box_generator\main.py` 或 `.venv\Scripts\streamlit.exe run box_generator\app.py`。

之后要退出 venv：输入 `deactivate`。

---

## 5. 把依赖库装进 venv

在 venv **已激活**的状态下：

```bash
pip install -r requirements.txt
```

会安装：

- **cadquery** —— 负责所有建模的 CAD 内核（圆角、抽壳、布尔切除、STL 导出）。它会连带装 OpenCASCADE + VTK 二进制，所以这个下载**体积很大（几百 MB）**、可能要等几分钟。这是正常的，别中途取消。
- **pyyaml** —— 读取 YAML 配置。
- **streamlit** —— 网页界面。（3D 预览用的是从 CDN 加载的 Three.js，所以不需要额外的重量级 Python 3D 依赖。）

> **`pip install cadquery` 失败或卡住？**
> - 先确认 Python 是 3.10–3.13（`python --version`）。
> - 退路是用 conda 安装：`conda install -c conda-forge -c cadquery cadquery`。

---

## 6. 验证安装

```bash
python -c "import cadquery as cq; print(cq.Workplane('XY').box(10,10,10).val().Volume())"
```

打印出 `999.99…` 之类的数字 → CadQuery 正常工作。

---

## 7. 运行

### 方式 A —— 网页界面（推荐，适合探索）

```bash
cd box_generator
streamlit run app.py
```

Streamlit 会打印一个本地地址（默认 **http://localhost:8501**）——在浏览器打开即可。拖左侧滑块，看右侧 3D 预览，满意了点 **下载 STL**。

- 默认只有本机能访问。
- 换端口：`streamlit run app.py --server.port 8600`。
- 让局域网内其他设备访问：`streamlit run app.py --server.address 0.0.0.0`（然后用本机 IP 访问）。

按 `Ctrl+C` 停止服务。

### 方式 B —— 命令行

```bash
cd box_generator
python main.py config.yaml     # 或直接：python main.py（默认读 config.yaml）
```

成功会打印 `Exported box_output.stl`。改 `config.yaml`，重新跑，得到新模型。也可以指定别的配置文件：`python main.py my_box.yaml`。

---

## 8. 编辑配置（命令行模式）

命令行使用时你唯一要改的就是 `box_generator/config.yaml`。最小示例：

```yaml
box:
  size: [120, 80, 40]     # [长, 宽, 高] mm —— 长/宽必须 ≤ 250
  wall: 2                 # 壁厚 mm
  corner_radius: 5        # 竖直四角圆角 mm（0 = 直角）
  edge_fillet:
    top: 1                # 顶沿圆角 mm（≤ 壁厚/2）
    bottom: 1             # 底沿圆角 mm

partitions: null          # null = 无隔板（隔板树语法见手册）

hollow:
  hole_size: 8            # 药丸孔宽度 mm
  angle: 45               # 固定 45，别改
  border: auto            # 自动留实边框（或填数字指定边框宽 mm）
  faces:
    bottom: true          # 底面镂空？
    partitions: true      # 隔板镂空？

export:
  format: stl
  tolerance: 0.1          # 弧面精度——越小越平滑、文件越大
  filename: box_output.stl
```

逐字段的完整说明（隔板树、上限、自动钳制行为、打印建议）见：[参数化收纳盒生成器_使用手册.md](参数化收纳盒生成器_使用手册.md)。

---

## 9. 首次配置完成后的日常流程

```bash
cd BoxForge
.venv\Scripts\Activate.ps1        # （或你所用 shell 的激活命令）
cd box_generator
streamlit run app.py              # …或：python main.py config.yaml
```

就这么简单——不用重建 venv、不用重装包，激活后直接运行即可。

---

## 10. 故障排查

| 现象 | 解决 |
|---|---|
| `'streamlit' 不是内部或外部命令` | venv 没激活（streamlit 只装在 `.venv` 里）。先激活，或用完整路径 `.venv\Scripts\streamlit.exe run app.py`。 |
| `pip install cadquery` 装不上 | 确认 Python 是 3.10–3.13；否则用 conda 退路（第 5 步）。 |
| PowerShell 拦截 `Activate.ps1` | 执行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，再激活。 |
| 命令行报 `box length/width must be <= 250.0mm` | 设计超过打印板允许尺寸——这是硬性拒绝，不会自动缩小。改小 `size`。 |
| 网页预览区空白 | 3D 预览从 `cdn.jsdelivr.net` 加载 Three.js；无法访问时模型仍会生成（下方有统计信息）——直接下载 STL 用切片软件预览即可。 |
| 切片软件提示某镂空面需要支撑 | 检查是不是把 `corner_radius`/`edge_fillet` 设成了极端值导致意外悬空；45° 药丸孔本身是免支撑设计。 |
