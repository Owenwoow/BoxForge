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
from main import build_from_config

st.set_page_config(page_title="参数化收纳盒生成器", layout="wide")

DEFAULT_PARTITIONS_YAML = """split:
  axis: x
  at: 0.5
  thickness: 1.5
  height: null
children:
  - split: {axis: y, at: "30mm", thickness: 1.5, height: null}
    children: [null, null]
  - null
"""


@st.cache_resource(show_spinner=False)
def _get_tmp_dir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="boxforge_"))
    return d


@st.cache_resource(show_spinner="正在建模 (CadQuery)...")
def _build_solid_cached(cfg_json: str):
    cfg = json.loads(cfg_json)
    solid = build_from_config(cfg)
    return solid


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

    col1, col2 = st.sidebar.columns([3, 2])
    with col1:
        st.slider(label, min_v, max_v, default, step, key=slider_key, on_change=_from_slider)
    with col2:
        # Distinct accessible name from the slider (else they'd share one
        # aria-label, which is both an a11y issue and breaks label-based
        # element lookup for the two controls).
        st.number_input(
            f"{label} 数值", min_v, max_v, default, step, key=number_key, on_change=_from_number,
            label_visibility="collapsed",
        )
    return st.session_state[slider_key]


def sidebar_inputs() -> dict:
    st.sidebar.header("盒体尺寸")
    length = _synced_number_slider("长 length (mm)", 20.0, 250.0, 120.0, 1.0, "length")
    width = _synced_number_slider("宽 width (mm)", 20.0, 250.0, 80.0, 1.0, "width")
    height = _synced_number_slider("高 height (mm)", 10.0, 200.0, 40.0, 1.0, "height")
    wall = _synced_number_slider("壁厚 wall (mm)", 0.8, 6.0, 2.0, 0.1, "wall")

    st.sidebar.header("圆角")
    corner_radius = st.sidebar.slider(
        "竖直四角圆角 corner_radius (mm)", 0.0, min(length, width) / 2, 8.0, 0.5
    )
    edge_top = st.sidebar.slider("顶沿圆角 edge_fillet.top (mm)", 0.0, wall / 2, wall / 4, 0.05)
    edge_bottom = st.sidebar.slider(
        "底沿圆角 edge_fillet.bottom (mm)", 0.0, min(height, min(length, width) / 2), 1.0, 0.1
    )

    st.sidebar.header("隔板 (递归二分树 YAML)")
    st.sidebar.caption("axis: x/y, at: 比例(0~1)或\"30mm\", children 留空数组表示不再分")
    enable_partitions = st.sidebar.checkbox("启用隔板", value=True)
    partitions_yaml = st.sidebar.text_area(
        "partitions", DEFAULT_PARTITIONS_YAML, height=200, disabled=not enable_partitions
    )

    st.sidebar.header("药丸镂空 (45°, 免支撑)")
    hole_size = st.sidebar.slider("孔大小 hole_size (mm)", 3.0, 20.0, 8.0, 0.5)
    border_mode = st.sidebar.selectbox("边框宽度 border", ["auto", "自定义"])
    border_value = "auto"
    if border_mode == "自定义":
        border_value = st.sidebar.slider("边框宽度 (mm)", 0.0, 20.0, 3.0, 0.5)
    hollow_bottom = st.sidebar.checkbox("底面镂空", value=True)
    hollow_partitions = st.sidebar.checkbox("隔板镂空", value=True)

    st.sidebar.header("导出")
    tolerance = st.sidebar.select_slider("STL 精度 tolerance", [0.5, 0.2, 0.1, 0.05, 0.02], value=0.1)
    filename = st.sidebar.text_input("文件名", "box_output.stl")

    raw = {
        "box": {
            "size": [length, width, height],
            "wall": wall,
            "corner_radius": corner_radius,
            "edge_fillet": {"top": edge_top, "bottom": edge_bottom},
        },
        "partitions": None,
        "hollow": {
            "hole_size": hole_size,
            "angle": 45,
            "border": border_value,
            "faces": {"bottom": hollow_bottom, "partitions": hollow_partitions},
        },
        "export": {"format": "stl", "tolerance": tolerance, "filename": filename},
    }

    if enable_partitions:
        try:
            raw["partitions"] = yaml.safe_load(partitions_yaml)
        except yaml.YAMLError as e:
            st.sidebar.error(f"partitions YAML 解析失败: {e}")
            raw["partitions"] = None

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

    stl_bytes = stl_path.read_bytes()
    b64 = base64.b64encode(stl_bytes).decode("ascii")
    st.components.v1.html(_stl_viewer_html(b64), height=530)

    bb = solid.val().BoundingBox()
    c1, c2, c3 = st.columns(3)
    c1.metric("外部尺寸 (mm)", f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
    c2.metric("体积 (cm^3)", f"{solid.val().Volume() / 1000:.1f}")
    c3.metric("是否合法几何", "OK" if solid.val().isValid() else "FAIL")

    return stl_path


def main():
    st.title("参数化收纳盒生成器")
    st.caption("拖动左侧参数 -> 实时预览 -> 下载 STL 用于 3D 打印")

    raw_cfg = sidebar_inputs()

    try:
        cfg = validate_config(raw_cfg)
    except ConfigError as e:
        st.error(f"配置错误: {e}")
        return

    cfg_hash = _config_hash(cfg)
    tmp_dir = _get_tmp_dir()

    try:
        solid = _build_solid_cached(json.dumps(cfg, sort_keys=True))
    except Exception as e:
        st.error(f"建模失败: {e}")
        return

    stl_path = render_preview(solid, tmp_dir, cfg_hash)

    st.download_button(
        "下载 STL",
        data=stl_path.read_bytes(),
        file_name=cfg["export"]["filename"],
        mime="model/stl",
        type="primary",
    )


if __name__ == "__main__":
    main()
