# 桌面版（预编译，无需 Python）

[English](desktop-app.md) · [简体中文](desktop-app.zh-CN.md) · [← README](../README.zh-CN.md)

桌面版把 Python、Streamlit 以及整套 CadQuery/OpenCASCADE 打包进一个自包含的文件夹。下载、解压、运行——它会启动本地服务并在浏览器打开网页界面。不需要装 Python，不需要 `pip`。

## 1. 下载

从 [**最新 Release**](https://github.com/Owenwoow/BoxForge/releases/latest) 下载对应平台的压缩包：

| 平台 | 文件 |
|---|---|
| Windows x64 | `BoxForge-windows-x64.zip` |
| Linux amd64 | `BoxForge-linux-amd64.tar.gz` |
| macOS（Apple 芯片） | `BoxForge-macos-arm64.tar.gz` |
| macOS（Intel） | `BoxForge-macos-x64.tar.gz` |

> 因为内含完整 CAD 内核，下载体积较大（约 300–900 MB）。

## 2. 解压并运行

**Windows**
1. 解压 `BoxForge-windows-x64.zip`。
2. 进入 `BoxForge` 文件夹，运行 `BoxForge.exe`。
3. 首次启动较慢（要解包 CAD 内核）；就绪后会自动打开浏览器到 `http://localhost:8501`。

```powershell
# 也可从终端运行：
.\BoxForge\BoxForge.exe
```

**Linux**
```bash
tar -xzf BoxForge-linux-amd64.tar.gz
./BoxForge/BoxForge
```

**macOS**
```bash
tar -xzf BoxForge-macos-arm64.tar.gz   # Intel 用 -x64
./BoxForge/BoxForge
```

## 3. 系统安全提示

这些可执行文件**未做代码签名**，首次运行系统可能会拦截。

- **Windows** —— 弹出"Windows 已保护你的电脑"：点 **更多信息 → 仍要运行**。
- **macOS** —— 提示"无法验证开发者"：右键点可执行文件 → **打开** → **打开**，或在 **系统设置 → 隐私与安全性** 里允许。也可在终端清除隔离标记：
  ```bash
  xattr -dr com.apple.quarantine BoxForge
  ```
- **Linux** —— 确保有执行权限：`chmod +x BoxForge/BoxForge`。

## 4. 选项

- 换端口：设置 `BOXFORGE_PORT`，例如 `BOXFORGE_PORT=8600 ./BoxForge/BoxForge`。
- 无界面自检（建一个模型就退出，不开浏览器）：`./BoxForge/BoxForge --selftest`。

## 5. 故障排查

| 现象 | 解决 |
|---|---|
| 首次运行一分钟没反应 | 正常——正在解包 CAD 内核。稍等，服务就绪后浏览器会自动打开。 |
| 浏览器没自动打开 | 手动访问 `http://localhost:8501`（或你设的 `BOXFORGE_PORT`）。 |
| 端口被占用 | 把 `BOXFORGE_PORT` 设成一个空闲端口。 |
| 3D 预览空白 | 预览从 CDN 加载 Three.js；离线时模型仍会生成（有统计信息）——直接下载 STL 即可。 |

想自己打包桌面版？见 [CONTRIBUTING.md](../CONTRIBUTING.md#building-the-desktop-app-locally--本地打包桌面版)。
