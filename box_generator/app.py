"""Stage 2: Streamlit web UI -- sliders + live 3D preview + STL download.

Run with: streamlit run app.py
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import streamlit as st
import yaml

from box_builder.export import export_stl
from box_builder.validate import ConfigError, validate_config
from box_builder.validate import _resolve_split_at as resolve_split_at
from main import build_from_config

st.set_page_config(page_title="BoxForge", layout="wide")

# Wider default sidebar so the slider+number-box pairs (added for direct
# numeric entry) have room to breathe instead of cramming the number box's
# stepper buttons against the slider's min/max labels. Users can still
# drag-resize it narrower/wider afterward.
#
# The `:has(div[data-testid="stSlider"])` rule vertically centers a
# slider+number-box row's two columns against each other, so the number box
# lines up with the slider's track/thumb instead of sitting up near its label.
st.markdown(
    """
    <style>
    /* Scoped to aria-expanded="true" only -- an unscoped width/min-width
    override here fights Streamlit's own collapse mechanism (it still knows
    the sidebar as 400px wide while collapsed, so the "expand" arrow control
    that should sit at the far left ends up positioned using that stale
    width instead, appearing stuck mid-page instead of at the edge). */
    section[data-testid="stSidebar"][aria-expanded="true"] {
        width: 400px !important;
        min-width: 320px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSlider"]) {
        align-items: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "lang" not in st.session_state:
    st.session_state["lang"] = "zh"


def T(key: str) -> str:
    return STRINGS[st.session_state["lang"]][key]


STRINGS = {
    "zh": {
        "page_title": "参数化收纳盒生成器",
        "page_caption": "拖动左侧参数 → 实时预览 → 下载 STL 用于 3D 打印",
        "sec_dimensions": "盒体尺寸",
        "sec_fillet": "圆角",
        "sec_partitions": "隔板",
        "sec_hollow": "镂空",
        "sec_export": "导出",
        "f_length": "长 (mm)",
        "f_width": "宽 (mm)",
        "f_height": "高 (mm)",
        "f_wall": "壁厚 (mm)",
        "f_corner_radius": "竖直四角圆角 (mm)",
        "f_edge_top": "顶沿圆角 (mm)",
        "f_edge_bottom": "底沿圆角 (mm)",
        "p_caption": "点按钮加隔板，方向/位置/厚度用下面的控件调；下方俯视图会实时更新。",
        "p_quick_start": "快速开始",
        "p_preset_placeholder": "-- 选一个预设 --",
        "p_whole_box": "整个盒子",
        "p_side_x0": "左侧", "p_side_x1": "右侧", "p_side_y0": "前侧", "p_side_y1": "后侧",
        "p_axis_x": "沿长度切 (分左右)", "p_axis_y": "沿宽度切 (分前后)",
        "p_node_title": "隔板 · {label}",
        "p_split_pos": "切割位置 ({label} 内的比例)",
        "p_thickness": "隔板厚度 (mm)",
        "p_full_height": "到顶",
        "p_custom_height": "隔板高度 (mm，从底部量起)",
        "p_delete": "🗑 删除此隔板（含内部子隔板）",
        "p_add": "+ 在「{label}」内添加隔板",
        "p_advanced": "高级：查看 / 粘贴 YAML",
        "p_paste_label": "粘贴 YAML 并应用",
        "p_apply": "应用粘贴的 YAML",
        "p_yaml_error": "YAML 解析失败: {err}",
        "p_diagram_caption": "俯视图 · 下方=正面(打印时面向你的一侧) · 红色=隔板",
        "h_hole_size": "孔大小 (mm)",
        "h_border": "边框宽度",
        "h_border_auto": "自动",
        "h_border_custom": "自定义",
        "h_border_value": "边框宽度 (mm)",
        "h_bottom": "底面镂空",
        "h_partitions": "隔板镂空",
        "e_tolerance": "STL 精度",
        "e_filename": "文件名",
        "m_size": "外部尺寸 (mm)",
        "m_volume": "体积 (cm^3)",
        "m_valid": "是否合法几何",
        "m_valid_ok": "OK",
        "m_valid_fail": "FAIL",
        "download_btn": "下载 STL",
        "config_error": "配置错误: {err}",
        "model_error": "建模失败: {err}",
        "preview_unavailable_note": "",
        "lang_toggle": "语言 / Language",
    },
    "en": {
        "page_title": "Parametric Storage Box Generator",
        "page_caption": "Drag the parameters on the left -> live preview -> download STL for 3D printing",
        "sec_dimensions": "Box Dimensions",
        "sec_fillet": "Fillets",
        "sec_partitions": "Partitions",
        "sec_hollow": "Pill Vents (45°, support-free)",
        "sec_export": "Export",
        "f_length": "Length (mm)",
        "f_width": "Width (mm)",
        "f_height": "Height (mm)",
        "f_wall": "Wall thickness (mm)",
        "f_corner_radius": "Corner radius (mm)",
        "f_edge_top": "Top rim fillet (mm)",
        "f_edge_bottom": "Bottom rim fillet (mm)",
        "p_caption": "Click to add a divider; tune direction/position/thickness below. The top-down diagram updates live.",
        "p_quick_start": "Quick start",
        "p_preset_placeholder": "-- pick a preset --",
        "p_whole_box": "Whole box",
        "p_side_x0": "Left", "p_side_x1": "Right", "p_side_y0": "Front", "p_side_y1": "Back",
        "p_axis_x": "Cut along length (left/right)", "p_axis_y": "Cut along width (front/back)",
        "p_node_title": "Divider · {label}",
        "p_split_pos": "Cut position (% within {label})",
        "p_thickness": "Divider thickness (mm)",
        "p_full_height": "Full height",
        "p_custom_height": "Divider height (mm, from the floor)",
        "p_delete": "🗑 Delete this divider (and its sub-dividers)",
        "p_add": "+ Add a divider in \"{label}\"",
        "p_advanced": "Advanced: view / paste YAML",
        "p_paste_label": "Paste YAML and apply",
        "p_apply": "Apply pasted YAML",
        "p_yaml_error": "Failed to parse YAML: {err}",
        "p_diagram_caption": "Top view · bottom = front (facing you when printing) · red = dividers",
        "h_hole_size": "Hole size (mm)",
        "h_border": "Border width",
        "h_border_auto": "auto",
        "h_border_custom": "custom",
        "h_border_value": "Border width (mm)",
        "h_bottom": "Vent the bottom",
        "h_partitions": "Vent the dividers",
        "e_tolerance": "STL tolerance",
        "e_filename": "Filename",
        "m_size": "Outer size (mm)",
        "m_volume": "Volume (cm^3)",
        "m_valid": "Valid geometry",
        "m_valid_ok": "OK",
        "m_valid_fail": "FAIL",
        "download_btn": "Download STL",
        "config_error": "Config error: {err}",
        "model_error": "Modeling failed: {err}",
        "preview_unavailable_note": "",
        "lang_toggle": "Language / 语言",
    },
}


def _split_node(axis: str, at: float, thickness: float) -> dict:
    # Matches the schema validate.py expects: split params nested under
    # "split", siblings with "children" -- NOT flattened onto the node.
    return {"split": {"axis": axis, "at": at, "thickness": thickness, "height": None}, "children": [None, None]}


PRESET_BUILDERS = {
    "none": None,
    "half_cols": lambda t: _split_node("x", 0.5, t),
    "half_rows": lambda t: _split_node("y", 0.5, t),
    "cross": lambda t: {**_split_node("x", 0.5, t), "children": [_split_node("y", 0.5, t), _split_node("y", 0.5, t)]},
}

PRESET_LABELS = {
    "zh": {"none": "清空 (无隔板)", "half_cols": "对半分 (两列)", "half_rows": "对半分 (两行)", "cross": "十字分四格"},
    "en": {"none": "Clear (no dividers)", "half_cols": "Split in half (2 columns)",
           "half_rows": "Split in half (2 rows)", "cross": "Cross (4 cells)"},
}


# On a public deployment these caches are shared process-wide across every
# visitor, so they must stay bounded or they become a slow memory/disk leak:
# every distinct parameter combination anyone tries would otherwise be kept
# forever. max_entries caps how many distinct models we retain; ttl expires
# idle ones. MAX_PREVIEW_FILES bounds the matching STL files on disk.
_SOLID_CACHE_MAX = 32
_PREVIEW_TTL_SECONDS = 1800
MAX_PREVIEW_FILES = 40


@st.cache_resource(show_spinner=False)
def _get_tmp_dir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="boxforge_"))
    return d


@st.cache_resource(show_spinner="正在建模 (CadQuery)...", max_entries=_SOLID_CACHE_MAX, ttl=_PREVIEW_TTL_SECONDS)
def _build_solid_cached(cfg_json: str):
    cfg = json.loads(cfg_json)
    solid = build_from_config(cfg)
    return solid


def _prune_preview_dir(tmp_dir: Path, keep: int = MAX_PREVIEW_FILES) -> None:
    """Keep only the newest `keep` preview STLs so the shared temp dir can't
    grow without bound as visitors explore different parameter sets."""
    try:
        files = sorted(tmp_dir.glob("preview_*.stl"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return
    for stale in files[keep:]:
        try:
            stale.unlink()
        except OSError:
            pass


def _config_hash(cfg: dict) -> str:
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:10]


def _synced_number_slider(label: str, min_v: float, max_v: float, default: float, step: float, key: str) -> float:
    """Slider + number box bound to the same value, so users can either drag
    or type an exact number. Both widgets keep their own session_state entry;
    each on_change writes into the *other* widget's entry so they stay in
    sync across reruns (Streamlit doesn't sync two independently-keyed
    widgets automatically)."""
    slider_key, number_key = f"{key}_slider", f"{key}_number"

    def _from_slider():
        st.session_state[number_key] = st.session_state[slider_key]

    def _from_number():
        st.session_state[slider_key] = st.session_state[number_key]

    col1, col2 = st.columns([5, 3])
    with col1:
        st.slider(label, min_v, max_v, default, step, key=slider_key, on_change=_from_slider)
    with col2:
        # Distinct accessible name from the slider (else they'd share one
        # aria-label, which is both an a11y issue and breaks label-based
        # element lookup for the two controls).
        st.number_input(
            f"{label}__num", min_v, max_v, default, step, key=number_key, on_change=_from_number,
            label_visibility="collapsed",
        )
    return st.session_state[slider_key]


# --- Partition tree builder: click-and-fill instead of hand-written YAML ---
#
# The tree is stored as one object in st.session_state["ptree"] (same shape
# validate.py expects: {split: {axis, at, thickness, height}, children:[a,b]}
# or None). A `path` is a tuple of 0/1 child indices from the root, used both
# to address a node and as a stable widget-key suffix (e.g. "p_0_1_axis").

def _axis_labels() -> dict:
    return {"x": T("p_axis_x"), "y": T("p_axis_y")}


def _side_labels() -> dict:
    return {
        ("x", 0): T("p_side_x0"), ("x", 1): T("p_side_x1"),
        ("y", 0): T("p_side_y0"), ("y", 1): T("p_side_y1"),
    }


def _node_at_path(root, path):
    node = root
    for idx in path:
        node = node["children"][idx]
    return node


def _set_node_at_path(path, value):
    if not path:
        st.session_state["ptree"] = value
        return
    node = st.session_state["ptree"]
    for idx in path[:-1]:
        node = node["children"][idx]
    node["children"][path[-1]] = value


def _bump_partition_generation():
    """Every structural tree edit (preset picked, YAML pasted, node added or
    deleted) bumps this counter. All per-node widget keys bake the current
    generation in, so any edit renders a fresh set of widget keys.

    Just `del`-ing the old session_state entries isn't enough here: Streamlit
    can keep a widget's client-side (React) checked/selected state alive
    across a rerun even after its server-side session_state value was
    cleared, since the key *string* didn't change. Changing the key string
    itself forces a real unmount/remount, which sidesteps that staleness at
    the root instead of fighting it.
    """
    st.session_state["ptree_gen"] = st.session_state.get("ptree_gen", 0) + 1


def _region_label(path: tuple) -> str:
    if not path:
        return T("p_whole_box")
    side_labels = _side_labels()
    node = st.session_state["ptree"]
    parts = []
    for idx in path:
        parts.append(side_labels[(node["split"]["axis"], idx)])
        node = node["children"][idx]
    return " › ".join(parts)


def _collect_rects(node, x0, x1, y0, y1, walls, leaves):
    if node is None:
        leaves.append((x0, x1, y0, y1))
        return
    axis, thickness = node["split"]["axis"], node["split"]["thickness"]
    span = (x1 - x0) if axis == "x" else (y1 - y0)
    cut = resolve_split_at(node["split"]["at"], span)
    if axis == "x":
        a, b = x0 + cut - thickness / 2, x0 + cut + thickness / 2
        walls.append((a, b, y0, y1))
        _collect_rects(node["children"][0], x0, a, y0, y1, walls, leaves)
        _collect_rects(node["children"][1], b, x1, y0, y1, walls, leaves)
    else:
        a, b = y0 + cut - thickness / 2, y0 + cut + thickness / 2
        walls.append((x0, x1, a, b))
        _collect_rects(node["children"][0], x0, x1, y0, a, walls, leaves)
        _collect_rects(node["children"][1], x0, x1, b, y1, walls, leaves)


def _partition_diagram_svg(tree, inner_length: float, inner_width: float) -> str:
    walls, leaves = [], []
    _collect_rects(tree, 0.0, inner_length, 0.0, inner_width, walls, leaves)

    scale = min(320 / inner_length, 200 / inner_width) if inner_length and inner_width else 1
    vw, vh = inner_length * scale, inner_width * scale
    pad = 10

    def to_svg(x0, x1, y0, y1):
        # Flip Y: local y=0 (front / "idx0" side) renders at the BOTTOM of
        # the diagram, matching the 3D preview's front-facing convention.
        return (x0 * scale + pad, (vh - y1 * scale) + pad, (x1 - x0) * scale, (y1 - y0) * scale)

    parts = [
        '<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="#26292f" stroke="#565b64" stroke-width="1.5" rx="3"/>'.format(
            *to_svg(0, inner_length, 0, inner_width)
        )
    ]
    for x0, x1, y0, y1 in leaves:
        sx, sy, sw, sh = to_svg(x0, x1, y0, y1)
        parts.append(
            f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
            f'fill="#3a4048" stroke="#6b7078" stroke-width="1"/>'
        )
        if sw > 34 and sh > 16:
            dim = f"{x1 - x0:.0f}×{y1 - y0:.0f}"
            parts.append(
                f'<text x="{sx + sw / 2:.1f}" y="{sy + sh / 2:.1f}" fill="#c7cbd1" font-size="11" '
                f'text-anchor="middle" dominant-baseline="middle">{dim}</text>'
            )
    for x0, x1, y0, y1 in walls:
        sx, sy, sw, sh = to_svg(x0, x1, y0, y1)
        parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{max(sw,1.5):.1f}" height="{max(sh,1.5):.1f}" fill="#e0645f"/>')

    total_w, total_h = vw + pad * 2, vh + pad * 2 + 18
    parts.append(
        f'<text x="{total_w/2:.0f}" y="{total_h-4:.0f}" fill="#8a8f96" font-size="10" text-anchor="middle">'
        f"{T('p_diagram_caption')}</text>"
    )
    return (
        f'<svg viewBox="0 0 {total_w:.0f} {total_h:.0f}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:360px;height:auto;display:block;margin:6px auto;">{"".join(parts)}</svg>'
    )


def _render_partition_node(path: tuple, default_thickness: float):
    node = st.session_state["ptree"] if not path else _node_at_path(st.session_state["ptree"], path)
    gen = st.session_state.get("ptree_gen", 0)
    key = f"p{gen}_" + "_".join(map(str, path)) if path else f"p{gen}_root"
    label = _region_label(path)

    if node is None:
        if st.button(T("p_add").format(label=label), key=key + "_add", use_container_width=True):
            _set_node_at_path(path, _split_node("x", 0.5, default_thickness))
            _bump_partition_generation()
            st.rerun()
        return

    split = node["split"]
    axis_labels = _axis_labels()
    with st.container(border=True):
        st.markdown(f"**{T('p_node_title').format(label=label)}**")
        axis_choice = st.radio(
            "axis", list(axis_labels.values()),
            index=0 if split["axis"] == "x" else 1,
            key=key + "_axis", horizontal=True, label_visibility="collapsed",
        )
        split["axis"] = "x" if axis_choice == axis_labels["x"] else "y"

        at_frac = split["at"] if isinstance(split["at"], (int, float)) and 0 <= split["at"] <= 1 else 0.5
        pct = st.slider(T("p_split_pos").format(label=label), 0, 100, int(round(at_frac * 100)), key=key + "_at")
        split["at"] = pct / 100

        c1, c2 = st.columns(2)
        with c1:
            split["thickness"] = st.number_input(
                T("p_thickness"), 0.5, 10.0, float(split["thickness"]), 0.5, key=key + "_thick"
            )
        with c2:
            full_height = st.checkbox(T("p_full_height"), value=(split["height"] is None), key=key + "_fullh")
        if not full_height:
            split["height"] = st.number_input(
                T("p_custom_height"), 5.0, 300.0,
                float(split["height"]) if split["height"] else 20.0, 1.0, key=key + "_h",
            )
        else:
            split["height"] = None

        if st.button(T("p_delete"), key=key + "_del", use_container_width=True):
            _set_node_at_path(path, None)
            _bump_partition_generation()
            st.rerun()

    _render_partition_node(path + (0,), default_thickness)
    _render_partition_node(path + (1,), default_thickness)


def partition_builder_ui(length: float, width: float, wall: float):
    if "ptree" not in st.session_state:
        st.session_state["ptree"] = None

    st.caption(T("p_caption"))

    preset_ids = ["__placeholder__"] + list(PRESET_BUILDERS.keys())
    labels = PRESET_LABELS[st.session_state["lang"]]
    # Bake the language into the key: Streamlit/React can keep showing a
    # selectbox's previously-rendered option text after a rerun even when
    # format_func would now return something different for the same
    # underlying value (same staleness class as the partition-tree radio
    # fix above) -- changing the key forces a clean remount on language switch.
    preset_key = f"ptree_preset_{st.session_state['lang']}"

    def _preset_display(pid: str) -> str:
        return T("p_preset_placeholder") if pid == "__placeholder__" else labels[pid]

    def _apply_preset():
        choice = st.session_state[preset_key]
        if choice != "__placeholder__":
            builder = PRESET_BUILDERS[choice]
            st.session_state["ptree"] = builder(wall) if callable(builder) else builder
            _bump_partition_generation()
            # Resetting a widget's own key back to its placeholder is only
            # allowed from inside that widget's own callback (this runs
            # before the next rerun instantiates it), not as a plain
            # assignment after the widget has already been created.
            st.session_state[preset_key] = "__placeholder__"

    st.selectbox(
        T("p_quick_start"), preset_ids, format_func=_preset_display, key=preset_key, on_change=_apply_preset
    )

    inner_length, inner_width = length - 2 * wall, width - 2 * wall
    st.markdown(
        _partition_diagram_svg(st.session_state["ptree"], inner_length, inner_width),
        unsafe_allow_html=True,
    )

    _render_partition_node((), wall)

    # A plain st.expander here would be a *nested* expander (this whole
    # function already runs inside the "Partitions" expander), which
    # Streamlit forbids -- use a checkbox-gated container instead.
    if st.checkbox(T("p_advanced"), key="ptree_advanced_toggle"):
        with st.container(border=True):
            current_yaml = yaml.safe_dump(st.session_state["ptree"], allow_unicode=True, sort_keys=False) \
                if st.session_state["ptree"] else "null\n"
            st.code(current_yaml, language="yaml")
            pasted = st.text_area(T("p_paste_label"), "", key="ptree_paste", height=100)
            if st.button(T("p_apply"), key="ptree_paste_apply"):
                try:
                    st.session_state["ptree"] = yaml.safe_load(pasted) if pasted.strip() else None
                    _bump_partition_generation()
                    st.rerun()
                except yaml.YAMLError as e:
                    st.error(T("p_yaml_error").format(err=e))

    return st.session_state["ptree"]


def sidebar_inputs() -> dict:
    with st.sidebar:
        # Language itself is already resolved at the very top of main() (see
        # _resolve_language) so title/caption/etc. rendered *before*
        # sidebar_inputs() runs still pick up a same-run language switch.
        # This radio just displays/persists that choice.
        st.radio(
            T("lang_toggle"), ["中文", "English"],
            index=0 if st.session_state["lang"] == "zh" else 1,
            key="lang_radio", horizontal=True,
        )

        with st.expander(T("sec_dimensions"), expanded=True):
            length = _synced_number_slider(T("f_length"), 20.0, 250.0, 120.0, 1.0, "length")
            width = _synced_number_slider(T("f_width"), 20.0, 250.0, 80.0, 1.0, "width")
            height = _synced_number_slider(T("f_height"), 10.0, 200.0, 40.0, 1.0, "height")
            wall = _synced_number_slider(T("f_wall"), 0.8, 6.0, 2.0, 0.1, "wall")

        with st.expander(T("sec_fillet"), expanded=False):
            corner_radius = st.slider(T("f_corner_radius"), 0.0, min(length, width) / 2, 5.0, 0.5)
            edge_top = st.slider(T("f_edge_top"), 0.0, wall / 2, wall / 4, 0.05)
            edge_bottom = st.slider(T("f_edge_bottom"), 0.0, min(height, min(length, width) / 2), 1.0, 0.1)

        with st.expander(T("sec_partitions"), expanded=False):
            partitions_tree = partition_builder_ui(length, width, wall)

        with st.expander(T("sec_hollow"), expanded=False):
            hole_size = st.slider(T("h_hole_size"), 3.0, 20.0, 8.0, 0.5)
            border_mode = st.selectbox(T("h_border"), [T("h_border_auto"), T("h_border_custom")])
            border_value = "auto"
            if border_mode == T("h_border_custom"):
                border_value = st.slider(T("h_border_value"), 0.0, 20.0, 3.0, 0.5)
            hollow_bottom = st.checkbox(T("h_bottom"), value=False)
            hollow_partitions = st.checkbox(T("h_partitions"), value=False)

        with st.expander(T("sec_export"), expanded=False):
            tolerance = st.select_slider(T("e_tolerance"), [0.5, 0.2, 0.1, 0.05, 0.02], value=0.1)
            filename = st.text_input(T("e_filename"), "box_output.stl")

    raw = {
        "box": {
            "size": [length, width, height],
            "wall": wall,
            "corner_radius": corner_radius,
            "edge_fillet": {"top": edge_top, "bottom": edge_bottom},
        },
        "partitions": partitions_tree,
        "hollow": {
            "hole_size": hole_size,
            "angle": 45,
            "border": border_value,
            "faces": {"bottom": hollow_bottom, "partitions": hollow_partitions},
        },
        "export": {"format": "stl", "tolerance": tolerance, "filename": filename},
    }

    return raw


BED_SIZE = 256.0  # Bambu print bed 256x256, matches the length/width hard limit


def _stl_viewer_html(stl_b64: str) -> str:
    return f"""
<div id="viewer" style="width:100%;height:520px;background:#e9eaec;border-radius:8px;"></div>
<script type="importmap">
{{"imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
}}}}
</script>
<script type="module">
import * as THREE from "three";
import {{ OrbitControls }} from "three/addons/controls/OrbitControls.js";
import {{ STLLoader }} from "three/addons/loaders/STLLoader.js";

const BED = {BED_SIZE};

const container = document.getElementById("viewer");
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe9eaec);

function containerSize() {{
    return [container.clientWidth || window.innerWidth || 700, container.clientHeight || 520];
}}
const [initW, initH] = containerSize();

// Z-up, matching CadQuery / Bambu Studio (bed = XY plane, height along +Z).
const camera = new THREE.PerspectiveCamera(45, initW / initH, 0.1, 8000);
camera.up.set(0, 0, 1);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
// Render at the display's real pixel density (capped at 2x for perf), else
// the canvas renders at 1x and gets upscaled by the browser -> blurry on
// HiDPI / Retina / 2K / 4K screens.
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(initW, initH);
container.appendChild(renderer.domElement);

function resizeToContainer() {{
    const [w, h] = containerSize();
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h);
}}
window.addEventListener("resize", resizeToContainer);
setTimeout(resizeToContainer, 50);
setTimeout(resizeToContainer, 300);

scene.add(new THREE.AmbientLight(0xffffff, 0.65));
const key = new THREE.DirectionalLight(0xffffff, 0.85);
key.position.set(-0.4, -0.8, 1.2);
scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 0.35);
fill.position.set(0.8, 0.6, 0.5);
scene.add(fill);

// --- Print bed (256x256) to simulate the Bambu Studio import view ---
const bed = new THREE.Mesh(
    new THREE.PlaneGeometry(BED, BED),
    new THREE.MeshStandardMaterial({{ color: 0x303234, roughness: 0.95, metalness: 0.0 }})
);
bed.position.z = -0.15;  // just below Z=0 so the box floor rests cleanly on top
scene.add(bed);

// Grid on the XY plane (GridHelper is XZ by default -> rotate 90deg about X).
const divisions = Math.round(BED / 10);  // ~10mm cells
const grid = new THREE.GridHelper(BED, divisions, 0x5a5d60, 0x45484b);
grid.rotation.x = Math.PI / 2;
grid.position.z = -0.1;
scene.add(grid);

// Bed outline
const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(BED, BED)),
    new THREE.LineBasicMaterial({{ color: 0x6d7073 }})
);
edges.position.z = -0.05;
scene.add(edges);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

function b64ToArrayBuffer(b64) {{
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes.buffer;
}}

const loader = new STLLoader();
const geometry = loader.parse(b64ToArrayBuffer("{stl_b64}"));
geometry.computeVertexNormals();

// Rest the box on the bed: center it on X/Y, drop its floor onto Z=0.
geometry.computeBoundingBox();
const bb = geometry.boundingBox;
geometry.translate(
    -(bb.min.x + bb.max.x) / 2,
    -(bb.min.y + bb.max.y) / 2,
    -bb.min.z
);
geometry.computeBoundingBox();
const boxHeight = geometry.boundingBox.max.z;

const material = new THREE.MeshStandardMaterial({{ color: 0xd9b382, metalness: 0.1, roughness: 0.65 }});
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

// Default view: bottom down, front (-Y) toward viewer, looking down ~45 deg,
// framed so the whole 256x256 plate is visible (like a fresh Bambu import).
const fov = 45 * Math.PI / 180;
const dist = (BED * 0.62) / Math.tan(fov / 2);
const dir = new THREE.Vector3(-0.30, -0.86, 0.86).normalize();
const target = new THREE.Vector3(0, 0, boxHeight / 2);
camera.position.copy(dir.multiplyScalar(dist).add(target));
controls.target.copy(target);
controls.update();

function animate() {{
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}}
animate();
</script>
"""


def render_preview(solid, tmp_dir: Path, cfg_hash: str):
    import base64

    stl_path = tmp_dir / f"preview_{cfg_hash}.stl"
    if not stl_path.exists():
        # Fine tessellation for a smooth preview -- coarse tolerance makes
        # the rounded corners/fillets look faceted. Still fast enough here.
        export_stl(
            solid,
            {"filename": str(stl_path), "tolerance": 0.05, "angular_tolerance": 0.1},
        )
        _prune_preview_dir(tmp_dir)

    stl_bytes = stl_path.read_bytes()
    b64 = base64.b64encode(stl_bytes).decode("ascii")
    st.components.v1.html(_stl_viewer_html(b64), height=530)

    bb = solid.val().BoundingBox()
    c1, c2, c3 = st.columns(3)
    c1.metric(T("m_size"), f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
    c2.metric(T("m_volume"), f"{solid.val().Volume() / 1000:.1f}")
    c3.metric(T("m_valid"), T("m_valid_ok") if solid.val().isValid() else T("m_valid_fail"))

    return stl_path


def _resolve_language():
    """Read the language radio's *own* widget state (already updated by
    Streamlit before the script reruns) into st.session_state["lang"] before
    anything else renders, so a language switch takes effect on the very
    same rerun instead of lagging one rerun behind."""
    if "lang_radio" in st.session_state:
        st.session_state["lang"] = "zh" if st.session_state["lang_radio"] == "中文" else "en"
    elif "lang" not in st.session_state:
        st.session_state["lang"] = "zh"


def main():
    _resolve_language()
    st.title(T("page_title"))
    st.caption(T("page_caption"))

    raw_cfg = sidebar_inputs()

    try:
        cfg = validate_config(raw_cfg)
    except ConfigError as e:
        st.error(T("config_error").format(err=e))
        return

    cfg_hash = _config_hash(cfg)
    tmp_dir = _get_tmp_dir()

    try:
        solid = _build_solid_cached(json.dumps(cfg, sort_keys=True))
    except Exception as e:
        st.error(T("model_error").format(err=e))
        return

    stl_path = render_preview(solid, tmp_dir, cfg_hash)

    st.download_button(
        T("download_btn"),
        data=stl_path.read_bytes(),
        file_name=cfg["export"]["filename"],
        mime="model/stl",
        type="primary",
    )


if __name__ == "__main__":
    main()
