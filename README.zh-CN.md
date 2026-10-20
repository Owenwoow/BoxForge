<div align="center">

# 🗃️ BoxForge

**参数化 3D 收纳盒生成器 —— 圆角、递归隔板、45° 免支撑药丸镂空，一键导出可打印 STL。**

[![Open in GitHub Codespaces](https://img.shields.io/badge/Open%20in-Codespaces-2ea44f?logo=github)](https://codespaces.new/Owenwoow/BoxForge?quickstart=1)
[![CI](https://github.com/Owenwoow/BoxForge/actions/workflows/ci.yml/badge.svg)](https://github.com/Owenwoow/BoxForge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11–3.14](https://img.shields.io/badge/python-3.11--3.14-blue.svg)](https://www.python.org/)

<img src="docs/images/hero_render.png" alt="BoxForge 示例盒子" width="640">

[English](README.md) · **简体中文**

</div>

---

## 目录

- [这是什么？](#这是什么)
- [功能特性](#功能特性)
- [界面截图](#界面截图)
- [快速开始](#快速开始)
  - [方式一 —— 在 GitHub Codespaces 在线使用](#方式一--在-github-codespaces-在线使用)
  - [方式二 —— 从源码运行](#方式二--从源码运行)
- [文档](#文档)
- [项目结构](#项目结构)
- [参与贡献](#参与贡献)
- [开源协议](#开源协议)

## 这是什么？

BoxForge 把几个参数变成一个定制收纳盒，并导出**可 3D 打印的 STL**。填好尺寸、把四角磨圆、在任意位置加隔板、在底面和隔板上打免支撑透气孔，然后下载打印即可。

它提供两种形态，共用同一套建模引擎：

| 方式 | 适合场景 | 入口 |
|---|---|---|
| **网页界面**（Streamlit） | 手动调参 + 实时 3D 预览 | `streamlit run box_generator/app.py` |
| **命令行** | 写脚本、批量生成、自动化 | `python box_generator/main.py config.yaml` |

几何建模基于 [CadQuery](https://github.com/CadQuery/cadquery) —— 真正的 OpenCASCADE B-rep CAD 内核，**不是** mesh 网格库 —— 所以圆角、抽壳、布尔运算都稳健可靠。

> 收纳盒设计为**顶面开口无盖**。长宽硬性上限 **250 mm**，适配 256×256 打印板。

## 功能特性

- **自定义尺寸** —— 长 / 宽 / 高 / 壁厚全部参数化。
- **两类独立圆角** —— 竖直四角圆角（手机壳那种）*和* 顶/底水平棱圆角（不割手）。顶沿会**同时**倒内外两条棱。
- **递归隔板（BSP 树）** —— 沿 X 或 Y 切分任意区域，切完的每个子区域还能独立继续细分。对半分、十字四格等预设一键生成。
- **45° 免支撑药丸镂空** —— 底面和/或隔板上的交错胶囊孔，自动排布并保留一圈实心边框。45° 角能自架桥，无需支撑即可打印。外墙永不镂空。
- **实时 3D 预览** —— 网页界面把模型放在模拟的 256×256 打印板上（仿 Bambu Studio），可在浏览器里旋转缩放。
- **中英双语 + 明暗主题** —— 中文 / English、亮色 / 暗色都能随时切换。
- **输入加固** —— 几何上限自动钳制、文件名净化、隔板树深度/数量有上限，可安全地部署到公网。

## 界面截图

> 📌 **在这里放你自己的界面截图。** 运行网页界面，对整窗截图，保存到下面的路径，然后取消对应行的注释即可。

<!-- ![网页界面总览](docs/images/ui_overview.png) -->
`docs/images/ui_overview.png` *(待补 —— 建议约 1200px 宽)*

## 快速开始

### 方式一 —— 在 GitHub Codespaces 在线使用

什么都不用装，在浏览器里用 GitHub 的云端机器运行：

1. 打开 **<https://codespaces.new/Owenwoow/BoxForge?quickstart=1>**（需登录 GitHub），点 **Create codespace**。
2. 等首次初始化（安装 CadQuery，约 2 分钟），网页界面会自动启动并在预览标签页打开。
3. 想在完整浏览器标签页打开或分享给别人：打开 **Ports（端口）** 面板，找到 `8501` 端口，打开它的转发地址（`https://<codespace名>-8501.app.github.dev`）。默认只有你自己能访问；右键 → **Port Visibility → Public** 后别人也能打开。

> Codespace 是临时云端机器：闲置约 30 分钟会自动停止（可在 <https://github.com/codespaces> 重新打开），会消耗你账号每月的免费 Codespaces 时长，用完可在那里删除。

### 方式二 —— 从源码运行

```bash
# 需要 Python 3.11–3.14
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge

python -m venv .venv
# Windows PowerShell：  .venv\Scripts\Activate.ps1
# macOS / Linux：       source .venv/bin/activate
pip install -r requirements.txt

# 网页界面  ->  http://localhost:8501
streamlit run box_generator/app.py

# …或走命令行
python box_generator/main.py box_generator/config.yaml   # 生成 box_output.stl
```

完整步骤见 [安装教程](docs/installation.zh-CN.md)。

## 文档

| 指南 | English | 简体中文 |
|---|---|---|
| 安装与从源码运行 | [installation.md](docs/installation.md) | [installation.zh-CN.md](docs/installation.zh-CN.md) |
| 参数与使用手册 | [usage.md](docs/usage.md) | [usage.zh-CN.md](docs/usage.zh-CN.md) |

## 项目结构

```
BoxForge/
├── box_generator/
│   ├── config.yaml            # 命令行用的样例配置
│   ├── main.py                # 命令行入口
│   ├── app.py                 # Streamlit 网页界面入口
│   ├── .streamlit/            # Streamlit 配置（公网部署加固）
│   └── box_builder/
│       ├── validate.py         # YAML 校验 + 安全钳制
│       ├── body.py             # 盒体：圆角 + 抽壳
│       ├── partitions.py       # 递归 BSP 隔板
│       ├── hollow.py           # 45° 药丸镂空阵列
│       └── export.py           # STL 导出
├── tests/                     # pytest 测试（校验、建模、网页界面）
├── docs/                      # 教程（English + 简体中文）
├── .devcontainer/             # GitHub Codespaces 配置（自动启动网页界面）
└── .github/workflows/         # CI（lint + 测试）与打标签发版
```

## 参与贡献

欢迎贡献！开发环境、分支模型（`dev` 用于开发，`main` 只放正式版本）、提交规范请见 [CONTRIBUTING.md](CONTRIBUTING.md)。Bug 和需求请提 [issue](https://github.com/Owenwoow/BoxForge/issues)。

## 开源协议

基于 [MIT 协议](LICENSE) 发布。
