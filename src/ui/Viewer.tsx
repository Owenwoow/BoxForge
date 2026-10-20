import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { PreviewMesh } from "../core/geometry/build";

const BED = 256; // Bambu print bed, matches the 250 mm footprint limit + margin

const PALETTE = {
  light: { bg: 0xe9eaec, bed: 0x303234, gridMajor: 0x5a5d60, gridMinor: 0x45484b, edge: 0x6d7073 },
  dark: { bg: 0x1c1e24, bed: 0x24262c, gridMajor: 0x3a3d44, gridMinor: 0x2c2e34, edge: 0x4a4d54 },
};

interface Scene {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  bed: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshStandardMaterial>;
  grid: THREE.GridHelper;
  outline: THREE.LineSegments<THREE.EdgesGeometry, THREE.LineBasicMaterial>;
  model: THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>;
  framed: boolean;
}

function makeGrid(theme: "light" | "dark") {
  const p = PALETTE[theme];
  const grid = new THREE.GridHelper(BED, Math.round(BED / 10), p.gridMajor, p.gridMinor);
  grid.rotation.x = Math.PI / 2; // GridHelper is XZ; the bed is XY (Z up)
  grid.position.z = -0.1;
  return grid;
}

export function Viewer({ mesh, theme, busy }: { mesh: PreviewMesh | null; theme: "light" | "dark"; busy: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const ctx = useRef<Scene | null>(null);

  // One-time scene setup.
  useEffect(() => {
    const el = host.current!;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 8000);
    camera.up.set(0, 0, 1); // Z-up like CadQuery / slicers

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    el.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.65));
    const key = new THREE.DirectionalLight(0xffffff, 0.85);
    key.position.set(-0.4, -0.8, 1.2);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 0.35);
    fill.position.set(0.8, 0.6, 0.5);
    scene.add(fill);

    const bed = new THREE.Mesh(
      new THREE.PlaneGeometry(BED, BED),
      new THREE.MeshStandardMaterial({ roughness: 0.95, metalness: 0 }),
    );
    bed.position.z = -0.15; // just below Z=0 so the floor rests cleanly on it
    scene.add(bed);

    const outline = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.PlaneGeometry(BED, BED)),
      new THREE.LineBasicMaterial(),
    );
    outline.position.z = -0.05;
    scene.add(outline);

    const model = new THREE.Mesh(
      new THREE.BufferGeometry(),
      new THREE.MeshStandardMaterial({ color: 0xd9b382, metalness: 0.1, roughness: 0.65 }),
    );
    scene.add(model);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    const grid = makeGrid("light");
    scene.add(grid);

    ctx.current = { renderer, scene, camera, controls, bed, grid, outline, model, framed: false };

    const resize = () => {
      const w = el.clientWidth || 600;
      const h = el.clientHeight || 400;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false); // CSS sizes the canvas; avoids a resize feedback loop
    };
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    resize();

    let raf = 0;
    const loop = () => {
      raf = requestAnimationFrame(loop);
      controls.update();
      renderer.render(scene, camera);
    };
    loop();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      controls.dispose();
      model.geometry.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
      ctx.current = null;
    };
  }, []);

  // Theme colors.
  useEffect(() => {
    const c = ctx.current!;
    const p = PALETTE[theme];
    c.scene.background = new THREE.Color(p.bg);
    c.bed.material.color.setHex(p.bed);
    c.outline.material.color.setHex(p.edge);
    c.scene.remove(c.grid);
    c.grid.dispose();
    c.grid = makeGrid(theme);
    c.scene.add(c.grid);
  }, [theme]);

  // New model geometry; frame the camera only on the very first model so the
  // user's own view survives parameter tweaks.
  useEffect(() => {
    const c = ctx.current!;
    if (!mesh) return;
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(mesh.vertices, 3));
    geom.setAttribute("normal", new THREE.BufferAttribute(mesh.normals, 3));
    geom.setIndex(new THREE.BufferAttribute(mesh.triangles, 1));
    geom.computeBoundingBox();
    const bb = geom.boundingBox!;
    // Rest the box on the bed: center on X/Y, drop its floor onto Z=0.
    geom.translate(-(bb.min.x + bb.max.x) / 2, -(bb.min.y + bb.max.y) / 2, -bb.min.z);
    c.model.geometry.dispose();
    c.model.geometry = geom;

    if (!c.framed) {
      c.framed = true;
      // Front (-Y) toward the viewer, looking down ~45°, whole bed in view.
      const height = bb.max.z - bb.min.z;
      const dist = (BED * 0.62) / Math.tan(((45 / 2) * Math.PI) / 180);
      const target = new THREE.Vector3(0, 0, height / 2);
      c.camera.position.copy(new THREE.Vector3(-0.3, -0.86, 0.86).normalize().multiplyScalar(dist).add(target));
      c.controls.target.copy(target);
      c.controls.update();
    }
  }, [mesh]);

  return <div ref={host} className={`viewer${busy ? " busy" : ""}`} data-testid="viewer" />;
}
