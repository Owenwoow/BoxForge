# Installation & Running from Source

[English](installation.md) · [简体中文](installation.zh-CN.md) · [← README](../README.md)

This guide takes you from a clean machine to a printable STL, with an emphasis on setting up a Python virtual environment. No prior Python-tooling experience assumed.

> Prefer no setup at all? Grab the [desktop app](desktop-app.md) instead — no Python required.

## 1. Prerequisites

| Tool | Version / note |
|---|---|
| **Python** | **3.11 – 3.14** (all tested in CI). Older Pythons can't install current CadQuery. |
| **git** | any recent version |
| OS | Windows / macOS / Linux all work |

Check which Python versions you have:

```bash
py -0p            # Windows
python3 --version # macOS / Linux
```

## 2. Get the code

```bash
git clone https://github.com/Owenwoow/BoxForge.git
cd BoxForge
```

## 3. Create a virtual environment

A **virtual environment** (venv) is an isolated, project-local Python. It keeps CadQuery's large binary dependencies out of your system Python. Create it once:

```bash
# Force a specific interpreter if your default isn't 3.11–3.14:
py -3.13 -m venv .venv     # Windows example
python3 -m venv .venv      # macOS / Linux
```

## 4. Activate it

Do this **every time you open a new terminal** for this project:

| Shell | Command |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd.exe | `.venv\Scripts\activate.bat` |
| macOS / Linux (bash/zsh) | `source .venv/bin/activate` |

After activating, your prompt shows `(.venv)`. Leave it later with `deactivate`.

> **PowerShell "running scripts is disabled"?** Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again.
>
> **Prefer not to activate?** Call the venv's tools by full path, e.g. `.venv\Scripts\streamlit.exe run box_generator\app.py`.

## 5. Install the libraries

With the venv activated:

```bash
pip install -r requirements.txt
```

This installs **cadquery** (the CAD kernel — pulls in OpenCASCADE + VTK binaries, so it's a **large, several-hundred-MB** download; be patient), **pyyaml**, and **streamlit**.

> **`pip install cadquery` fails or hangs?** Confirm Python is 3.11–3.14. Fallback via conda: `conda install -c conda-forge -c cadquery cadquery`.

## 6. Verify

```bash
python -c "import cadquery as cq; print(cq.Workplane('XY').box(10,10,10).val().Volume())"
```

Prints `999.99…` → CadQuery works.

## 7. Run it

### Web UI (recommended)

```bash
streamlit run box_generator/app.py
```

Open the printed URL (default **http://localhost:8501**). Drag sliders on the left, watch the 3D preview on the right, click **Download STL**.

- To change port: `--server.port 8600`. To reach it from your LAN: `--server.address 0.0.0.0`.
- Stop with `Ctrl+C`.

### Command line

```bash
cd box_generator
python main.py config.yaml     # or: python main.py  (defaults to config.yaml)
```

On success it prints `Exported box_output.stl`. Edit `config.yaml` and re-run. Point it at any file: `python main.py my_box.yaml`.

For the full parameter reference (every YAML field, limits, the partition-tree syntax, print tips), see the [Usage guide](usage.md).

## 8. Everyday workflow

```bash
cd BoxForge
.venv\Scripts\Activate.ps1        # (or your shell's activate command)
streamlit run box_generator/app.py
```

You don't recreate the venv or reinstall — just activate and run.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `'streamlit' is not recognized` | The venv isn't activated. Activate it, or use the full path `.venv\Scripts\streamlit.exe`. |
| `pip install cadquery` won't install | Ensure Python 3.11–3.14; else use the conda fallback (step 5). |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| CLI: `box length/width must be <= 250.0mm` | The design is bigger than the print bed allows — a hard reject, not auto-shrunk. Reduce `size`. |
| Web preview area is blank | The 3D viewer loads Three.js from a CDN; if that's unreachable the model still generates (stats show below) — just download the STL and preview in your slicer. |
