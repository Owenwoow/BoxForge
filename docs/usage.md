# Usage — Parameter Reference

[English](usage.md) · [简体中文](usage.zh-CN.md) · [← README](../README.md)

This guide covers every parameter: what it does, its limits, and how errors are handled. Use it online at <https://owenwoow.github.io/BoxForge/> — nothing to install.

## 1. The YAML config

The **Export & config** group can **download** the current design as YAML and **import** a YAML file to restore one; the Dividers group's advanced option shows/accepts just the divider-tree YAML. Full field reference:

```yaml
box:
  size: [120, 80, 40]          # [length, width, height] mm — length/width must be <= 250 (over = hard error, not shrunk)
  wall: 2                      # outer wall thickness mm
  corner_radius: 8             # vertical corner fillet radius mm, 0 = square
  edge_fillet:
    top: 1                     # top-rim fillet mm (rounds BOTH inner + outer lip), max ~ wall/2
    bottom: 1                  # bottom-rim fillet mm, 0 = square

partitions:                    # recursive BSP divider tree; whole thing can be null (no dividers)
  split:
    axis: x                    # cut direction: x or y
    at: 0.5                    # cut position: a 0–1 fraction, or an absolute size like "30mm"
    thickness: 1.5             # this divider's thickness mm
    height: null               # null = full height; a number = shorter divider (e.g. 20 = only 20mm tall)
  children:
    - split: {axis: y, at: "30mm", thickness: 1.5, height: null}
      children: [null, null]   # split the left region again; neither result splits further
    - null                     # the right region isn't split

hollow:
  hole_size: 8                 # pill-vent width mm — the only vent parameter you tune
  angle: 45                    # fixed at 45; any other value is forced back to 45 (key to support-free printing)
  border: auto                 # auto solid frame; or a number to set border width mm
  faces:
    bottom: true               # vent the floor?
    partitions: true           # vent the dividers? (single switch, all dividers together)

export:
  format: stl
  tolerance: 0.1               # STL mesh detail — smaller = finer = bigger file = slower export
  filename: box_output.stl
```

### 1.1 Limits & auto-correction

| Field | Hard limit (errors out) | Soft limit (auto-clamped + warning) |
|---|---|---|
| `box.size[0]` length | `> 250mm` errors | — |
| `box.size[1]` width | `> 250mm` errors | — |
| `box.size[2]` height | `> z_max` (default 250mm) errors | — |
| `box.wall` | `<= 0` errors; too thick (`wall*2 >= min(L,W)`) errors | — |
| `box.corner_radius` | `< 0` errors | clamped to `min(L,W)/2 * 0.9` |
| `edge_fillet.top` | `< 0` errors | clamped to `wall/2 * 0.9` (**half the wall**, see §4.1) |
| `edge_fillet.bottom` | `< 0` errors | clamped to `min(H, min(L,W)/2) * 0.8` |
| `hollow.hole_size` | `<= 0` errors | — |
| `hollow.angle` | — | forced back to 45 with a warning |
| `hollow.border` | `< 0` errors | `auto` → `max(wall, hole_size*0.5)` |
| `export.tolerance` | `<= 0` errors | — |

A hard limit shows a red error box at the top of the page and disables **Download STL** until the parameters are valid again. A soft limit still builds the model and lists what was **auto-corrected** in a yellow bar.

## 2. Partition tree syntax

`partitions` is either `null` (no dividers) or a `{split, children}` node:

- `split.axis` — `x` (cut along length → left/right) or `y` (cut along width → front/back)
- `split.at` — a `0`–`1` fraction (**proportional**, `0.5` = center), or a string like `"30mm"` (**absolute**, measured from that region's own start edge)
- `split.thickness` — this divider's thickness mm
- `split.height` — `null` = up to the rim; a number = shorter (measured up from the inner floor)
- `children` — a fixed length-2 array `[follow-up for region 1, follow-up for region 2]`; each is `null` (no more splitting) or another `{split, children}` node

**Key idea**: after a cut produces two sub-regions, they're independent — either can keep subdividing, or one can stop. That's why both a full grid and "split just one half" are possible.

**Example 1 — cross into 4 cells**

```yaml
partitions:
  split: {axis: x, at: 0.5, thickness: 1.5, height: null}
  children:
    - split: {axis: y, at: 0.5, thickness: 1.5, height: null}
      children: [null, null]
    - split: {axis: y, at: 0.5, thickness: 1.5, height: null}
      children: [null, null]
```

**Example 2 — one short divider in the left half only**

```yaml
partitions:
  split: {axis: x, at: 0.5, thickness: 1.5, height: null}
  children:
    - split: {axis: y, at: 0.4, thickness: 1.5, height: 15}   # only 15mm tall
      children: [null, null]
    - null
```

**Known trade-off**: cross grids from recursive bisection don't guarantee a perfectly aligned center junction (each side is split independently). This is the cost of "any region subdivides independently"; for a perfectly aligned grid, hand-compute matching `at` values on both sides.

## 3. Vent (`hollow`) details

- **Only `hole_size` is exposed** — spacing and the length/width ratio (pill length = width × 2.5) are computed for you.
- **Don't change `angle`** — 45° lets each hole's top self-bridge into an arch so it prints without supports. Other values are forced back to 45.
- **Outer walls are never vented** — `hollow.faces` only controls `bottom` and `partitions`; there is no outer-wall option, by design.
- **`border`** — the hole array is trimmed near region edges, leaving a solid border frame; in `auto` mode its width is `max(wall, hole_size/2)`.

## 4. FAQ

### 4.1 A larger top-rim fillet fails to build

The top rim rounds **both** the outer and inner lip. The two fillets eat into the wall from each side; as the radius approaches `wall/2`, their arcs meet inside the thin wall — OCCT can't build that self-intersecting geometry (`BRep_API: command not done`). The safe cap is `wall/2 * 0.9`; when hand-writing YAML, keep `edge_fillet.top` under half the wall.

### 4.2 Changing `hollow.angle` did nothing

45° is locked (key to support-free printing). Any other value is forced back with a warning — not a bug.

### 4.3 Divider error: `does not fit within span`

Some `split.at` + `thickness/2` exceeds its region. Check the region's actual available width (what's left after the parent cut) and move `at` toward the center.

### 4.4 Slow first load / blank 3D preview

The modeling kernel (OpenCASCADE compiled to WebAssembly) is a ~7 MB download the first time, then cached by the browser. If it stays on "Loading the CAD kernel" or reports a kernel error, use a recent Chrome / Edge / Firefox / Safari. A blank preview with normal stats usually means WebGL (hardware acceleration) is disabled — the model itself is fine, just download the STL.

## 5. Web UI control map

| Group | Control | Field | Note |
|---|---|---|---|
| Dimensions | length/width/height/wall | `box.size`, `box.wall` | length/width sliders cap at 250mm |
| Fillets | corner radius | `box.corner_radius` | cap tracks length/width |
| Fillets | top rim | `edge_fillet.top` | cap tracks wall (`wall/2`) |
| Fillets | bottom rim | `edge_fillet.bottom` | cap tracks height/width |
| Partitions | presets / add buttons / YAML | `partitions` | click-to-build, or write YAML directly |
| Vents | hole size / border / bottom / dividers | `hollow.*` | "custom" border reveals a slider |
| Export & config | STL tolerance / filename / download·import YAML / copy share link | `export.*` | the share link encodes the whole config in the URL, so whoever opens it gets the same design |

Main area: **3D preview** (drag to rotate, scroll to zoom; rebuilds on any change), **stats** (outer size / volume / valid geometry — `OK` = safe to export, `FAIL` = current params produced invalid geometry, adjust them), and the **Download STL** button.

## 6. Print tips

- The box is **open-topped (no lid)** by design — print it opening-up, no supports needed.
- The 45° floor/divider vents are support-free — no extra supports for those holes.
- If your slicer still flags a spot for support, check whether an extreme `corner_radius`/`edge_fillet` created an unintended overhang, rather than force-printing with auto-support off.
