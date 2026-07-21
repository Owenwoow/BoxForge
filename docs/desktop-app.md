# Desktop App (Prebuilt, No Python)

[English](desktop-app.md) · [简体中文](desktop-app.zh-CN.md) · [← README](../README.md)

The desktop app bundles Python, Streamlit and the whole CadQuery/OpenCASCADE stack into one self-contained folder. Download, unzip, run — it starts a local server and opens the web UI in your browser. No Python install, no `pip`.

## 1. Download

Get the archive for your platform from the [**latest release**](https://github.com/Owenwoow/BoxForge/releases/latest):

| Platform | File |
|---|---|
| Windows x64 | `BoxForge-windows-x64.zip` |
| Linux amd64 | `BoxForge-linux-amd64.tar.gz` |
| macOS (Apple Silicon) | `BoxForge-macos-arm64.tar.gz` |

> The download is large (~300–900 MB) because it contains a full CAD kernel.
>
> **Intel Macs** aren't shipped as a prebuilt app — run [from source](installation.md) or via [Docker](deployment.md) instead.

## 2. Unzip & run

**Windows**
1. Unzip `BoxForge-windows-x64.zip`.
2. Open the `BoxForge` folder and run `BoxForge.exe`.
3. First launch takes a while (it unpacks the CAD kernel); a browser tab opens at `http://localhost:8501` when ready.

```powershell
# Or from a terminal:
.\BoxForge\BoxForge.exe
```

**Linux**
```bash
tar -xzf BoxForge-linux-amd64.tar.gz
./BoxForge/BoxForge
```

**macOS**
```bash
tar -xzf BoxForge-macos-arm64.tar.gz
./BoxForge/BoxForge
```

## 3. OS security prompts

The binaries are **not code-signed**, so your OS may warn you the first time.

- **Windows** — "Windows protected your PC": click **More info → Run anyway**.
- **macOS** — "cannot be opened because the developer cannot be verified": right-click the binary → **Open** → **Open**, or allow it under **System Settings → Privacy & Security**. From a terminal you can also clear the quarantine flag:
  ```bash
  xattr -dr com.apple.quarantine BoxForge
  ```
- **Linux** — ensure it's executable: `chmod +x BoxForge/BoxForge`.

## 4. Options

- Pick a different port: set `BOXFORGE_PORT`, e.g. `BOXFORGE_PORT=8600 ./BoxForge/BoxForge`.
- Headless self-check (build a model and exit, no browser): `./BoxForge/BoxForge --selftest`.

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| Nothing happens for a minute on first run | Normal — the CAD kernel is being unpacked. Wait; the browser opens when the server is ready. |
| Browser didn't open | Manually visit `http://localhost:8501` (or your `BOXFORGE_PORT`). |
| Port already in use | Set `BOXFORGE_PORT` to a free port. |
| 3D preview is blank | The viewer loads Three.js from a CDN; if offline, the model still builds (stats show) — just download the STL. |

Want to build the desktop app yourself? See [CONTRIBUTING.md](../CONTRIBUTING.md#building-the-desktop-app-locally--本地打包桌面版).
