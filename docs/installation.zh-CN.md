# 安装与从源码运行

[English](installation.md) · [简体中文](installation.zh-CN.md) · [← README](../README.zh-CN.md)

本教程带你从一台干净的电脑一路走到可打印的 STL，重点讲如何创建 Python 虚拟环境。不需要任何 Python 工具链基础。

> 不想折腾环境？直接用 [桌面版](desktop-app.zh-CN.md)，无需 Python。

## 1. 环境要求

| 工具 | 版本 / 说明 |
|---|---|
| **Python** | **3.11 – 3.14**（CI 中全部测试过）。更老的 Python 装不上当前版本的 CadQuery。 |
| **git** | 任意较新版本 |
| 操作系统 | Windows / macOS / Linux 都可以 |

查看你装了哪些 Python 版本：

```bash
py -0p            # Windows
python3 --version # macOS / Linux
```

## 2. 获取代码

```bash
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge
```

## 3. 创建虚拟环境

**虚拟环境**（venv）是一个隔离的、项目本地的 Python，能把 CadQuery 庞大的二进制依赖跟系统 Python 隔离开。只建一次：

```bash
# 如果默认解释器不是 3.11–3.14，就指定一个：
py -3.13 -m venv .venv     # Windows 示例
python3 -m venv .venv      # macOS / Linux
```

## 4. 激活虚拟环境

**每次新开终端**做这个项目时都要先激活：

| Shell | 命令 |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd.exe | `.venv\Scripts\activate.bat` |
| macOS / Linux（bash/zsh） | `source .venv/bin/activate` |

激活后提示符前会出现 `(.venv)`。退出用 `deactivate`。

> **PowerShell 报"禁止运行脚本"？** 执行一次 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，再激活。
>
> **不想激活？** 用完整路径调用，例如 `.venv\Scripts\streamlit.exe run box_generator\app.py`。

## 5. 安装依赖库

在 venv 已激活的状态下：

```bash
pip install -r requirements.txt
```

会安装 **cadquery**（CAD 内核，连带装 OpenCASCADE + VTK 二进制，体积**很大、几百 MB**，耐心等）、**pyyaml**、**streamlit**。

> **`pip install cadquery` 失败或卡住？** 先确认 Python 是 3.11–3.14。退路用 conda：`conda install -c conda-forge -c cadquery cadquery`。

## 6. 验证安装

```bash
python -c "import cadquery as cq; print(cq.Workplane('XY').box(10,10,10).val().Volume())"
```

打印出 `999.99…` → CadQuery 正常。

## 7. 运行

### 网页界面（推荐）

```bash
streamlit run box_generator/app.py
```

打开打印出的地址（默认 **http://localhost:8501**）。左侧拖滑块，右侧看 3D 预览，满意了点 **下载 STL**。

- 换端口：`--server.port 8600`。局域网访问：`--server.address 0.0.0.0`。
- 按 `Ctrl+C` 停止。

### 命令行

```bash
cd box_generator
python main.py config.yaml     # 或直接 python main.py（默认读 config.yaml）
```

成功会打印 `Exported box_output.stl`。改 `config.yaml` 重新跑。也可指定别的文件：`python main.py my_box.yaml`。

逐字段的完整参数说明（隔板树语法、取值上限、打印建议）见 [使用手册](usage.zh-CN.md)。

## 8. 日常流程

```bash
cd BoxForge
.venv\Scripts\Activate.ps1        # （或你所用 shell 的激活命令）
streamlit run box_generator/app.py
```

不用重建 venv、不用重装包，激活后直接运行。

## 9. 故障排查

| 现象 | 解决 |
|---|---|
| `'streamlit' 不是内部或外部命令` | venv 没激活。先激活，或用完整路径 `.venv\Scripts\streamlit.exe`。 |
| `pip install cadquery` 装不上 | 确认 Python 是 3.11–3.14；否则用 conda 退路（第 5 步）。 |
| PowerShell 拦截 `Activate.ps1` | 执行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，再激活。 |
| 命令行报 `box length/width must be <= 250.0mm` | 尺寸超过打印板限制，硬性拒绝、不会自动缩小。改小 `size`。 |
| 网页预览区空白 | 3D 预览从 CDN 加载 Three.js；无法访问时模型仍会生成（下方有统计信息）——直接下载 STL 用切片软件预览即可。 |
