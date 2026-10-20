/**
 * Click-and-fill divider tree editor (replaces hand-written YAML), with a
 * live top-view diagram. A `path` is the list of 0/1 child indices from the
 * root; it addresses a node and keys its React subtree.
 */
import * as yaml from "js-yaml";
import { useState } from "react";
import { PRESETS, resolveSplitAt, splitNode, type PresetId, type RawPartitionNode } from "../core/config";
import { Checkbox, NumberSlider, Segmented } from "./controls";
import type { T } from "./i18n";

type Tree = RawPartitionNode | null;
type Path = number[];

function nodeAt(root: Tree, path: Path): Tree {
  let node = root;
  for (const i of path) node = node?.children?.[i] ?? null;
  return node;
}

/** Immutable update of the node at `path`. */
function setAt(root: Tree, path: Path, value: Tree): Tree {
  if (path.length === 0) return value;
  const node = root!;
  const children = [...(node.children ?? [null, null])] as [Tree, Tree];
  children[path[0]] = setAt(children[path[0]], path.slice(1), value);
  return { ...node, children };
}

function regionLabel(root: Tree, path: Path, t: T): string {
  if (path.length === 0) return t("p_whole_box");
  const parts: string[] = [];
  let node = root;
  for (const i of path) {
    const axis = node!.split.axis;
    parts.push(t(`p_side_${axis}${i}` as "p_side_x0"));
    node = node!.children?.[i] ?? null;
  }
  return parts.join(" › ");
}

/** Fraction (0..1) for the slider, whatever form `at` was given in. */
function atFraction(at: unknown): number {
  return typeof at === "number" && at >= 0 && at <= 1 ? at : 0.5;
}

// ---- Top-view diagram --------------------------------------------------------

type Rect = [number, number, number, number]; // x0, x1, y0, y1

function collect(node: Tree, r: Rect, walls: Rect[], leaves: Rect[]) {
  const [x0, x1, y0, y1] = r;
  if (!node) {
    leaves.push(r);
    return;
  }
  const { axis, thickness = 2 } = node.split;
  let cut: number;
  try {
    cut = resolveSplitAt(node.split.at ?? 0.5, axis === "x" ? x1 - x0 : y1 - y0);
  } catch {
    cut = (axis === "x" ? x1 - x0 : y1 - y0) / 2;
  }
  const kids = node.children ?? [null, null];
  if (axis === "x") {
    const a = x0 + cut - thickness / 2;
    const b = x0 + cut + thickness / 2;
    walls.push([a, b, y0, y1]);
    collect(kids[0], [x0, a, y0, y1], walls, leaves);
    collect(kids[1], [b, x1, y0, y1], walls, leaves);
  } else {
    const a = y0 + cut - thickness / 2;
    const b = y0 + cut + thickness / 2;
    walls.push([x0, x1, a, b]);
    collect(kids[0], [x0, x1, y0, a], walls, leaves);
    collect(kids[1], [x0, x1, b, y1], walls, leaves);
  }
}

function Diagram({ tree, innerL, innerW, t }: { tree: Tree; innerL: number; innerW: number; t: T }) {
  const walls: Rect[] = [];
  const leaves: Rect[] = [];
  collect(tree, [0, innerL, 0, innerW], walls, leaves);
  const scale = innerL > 0 && innerW > 0 ? Math.min(320 / innerL, 200 / innerW) : 1;
  const vw = innerL * scale;
  const vh = innerW * scale;
  const pad = 10;
  // Flip Y: the front (y=0) renders at the bottom, like the 3D view.
  const box = ([x0, x1, y0, y1]: Rect) => ({
    x: x0 * scale + pad,
    y: vh - y1 * scale + pad,
    width: Math.max((x1 - x0) * scale, 1.5),
    height: Math.max((y1 - y0) * scale, 1.5),
  });
  return (
    <figure className="diagram">
      <svg viewBox={`0 0 ${vw + pad * 2} ${vh + pad * 2}`} role="img" aria-label={t("p_diagram_caption")}>
        <rect {...box([0, innerL, 0, innerW])} rx={3} className="d-box" />
        {leaves.map((r, i) => {
          const b = box(r);
          return (
            <g key={`l${i}`}>
              <rect {...b} className="d-cell" />
              {b.width > 34 && b.height > 16 && (
                <text x={b.x + b.width / 2} y={b.y + b.height / 2} className="d-dim">
                  {`${(r[1] - r[0]).toFixed(0)}×${(r[3] - r[2]).toFixed(0)}`}
                </text>
              )}
            </g>
          );
        })}
        {walls.map((r, i) => (
          <rect key={`w${i}`} {...box(r)} className="d-wall" />
        ))}
      </svg>
      <figcaption>{t("p_diagram_caption")}</figcaption>
    </figure>
  );
}

// ---- Node editor -------------------------------------------------------------

function NodeEditor({
  root,
  path,
  defaultThickness,
  boxHeight,
  onChange,
  t,
}: {
  root: Tree;
  path: Path;
  defaultThickness: number;
  boxHeight: number;
  onChange: (tree: Tree) => void;
  t: T;
}) {
  const node = nodeAt(root, path);
  const label = regionLabel(root, path, t);
  const set = (value: Tree) => onChange(setAt(root, path, value));

  if (!node) {
    return (
      <button type="button" className="btn btn-ghost add" onClick={() => set(splitNode("x", 0.5, defaultThickness))}>
        {t("p_add", { label })}
      </button>
    );
  }

  const split = node.split;
  const update = (patch: Partial<RawPartitionNode["split"]>) => set({ ...node, split: { ...split, ...patch } });
  const height = split.height ?? null;

  return (
    <>
      <div className="node">
        <div className="node-title">{t("p_node_title", { label })}</div>
        <Segmented
          label={t("p_node_title", { label })}
          value={split.axis}
          options={[
            { value: "x", label: t("p_axis_x") },
            { value: "y", label: t("p_axis_y") },
          ]}
          onChange={(axis) => update({ axis })}
        />
        <NumberSlider
          label={t("p_split_pos", { label })}
          value={Math.round(atFraction(split.at) * 100)}
          min={1}
          max={99}
          step={1}
          onChange={(pct) => update({ at: pct / 100 })}
        />
        <NumberSlider
          label={t("p_thickness")}
          value={split.thickness ?? defaultThickness}
          min={0.5}
          max={10}
          step={0.1}
          onChange={(thickness) => update({ thickness })}
        />
        <Checkbox
          label={t("p_full_height")}
          checked={height === null}
          onChange={(full) => update({ height: full ? null : Math.min(20, boxHeight) })}
        />
        {height !== null && (
          <NumberSlider
            label={t("p_custom_height")}
            value={height}
            min={1}
            max={Math.max(boxHeight, 1)}
            step={1}
            onChange={(h) => update({ height: h })}
          />
        )}
        <button type="button" className="btn btn-danger" onClick={() => set(null)}>
          {t("p_delete")}
        </button>
      </div>
      {[0, 1].map((i) => (
        <NodeEditor
          key={i}
          root={root}
          path={[...path, i]}
          defaultThickness={defaultThickness}
          boxHeight={boxHeight}
          onChange={onChange}
          t={t}
        />
      ))}
    </>
  );
}

export function PartitionEditor({
  tree,
  onChange,
  length,
  width,
  height,
  wall,
  t,
}: {
  tree: Tree;
  onChange: (tree: Tree) => void;
  length: number;
  width: number;
  height: number;
  wall: number;
  t: T;
}) {
  const [showYaml, setShowYaml] = useState(false);
  const [pasted, setPasted] = useState("");
  const [yamlError, setYamlError] = useState<string | null>(null);

  const applyYaml = () => {
    try {
      onChange(pasted.trim() ? ((yaml.load(pasted) as Tree) ?? null) : null);
      setYamlError(null);
    } catch (e) {
      setYamlError(t("p_yaml_error", { err: e instanceof Error ? e.message : String(e) }));
    }
  };

  return (
    <div className="partitions">
      <p className="hint">{t("p_caption")}</p>
      <label className="field">
        <span>{t("p_quick_start")}</span>
        <select
          value=""
          onChange={(e) => {
            const id = e.target.value as PresetId;
            if (id) onChange(PRESETS[id](wall));
          }}
        >
          <option value="">{t("p_preset_placeholder")}</option>
          {(Object.keys(PRESETS) as PresetId[]).map((id) => (
            <option key={id} value={id}>
              {t(`preset_${id}`)}
            </option>
          ))}
        </select>
      </label>

      <Diagram tree={tree} innerL={length - 2 * wall} innerW={width - 2 * wall} t={t} />

      <NodeEditor root={tree} path={[]} defaultThickness={wall} boxHeight={height - wall} onChange={onChange} t={t} />

      <Checkbox label={t("p_advanced")} checked={showYaml} onChange={setShowYaml} />
      {showYaml && (
        <div className="node">
          <pre className="code">{tree ? yaml.dump(tree, { flowLevel: 3 }) : "null\n"}</pre>
          <textarea rows={5} value={pasted} onChange={(e) => setPasted(e.target.value)} spellCheck={false} />
          <button type="button" className="btn" onClick={applyYaml}>
            {t("p_apply")}
          </button>
          {yamlError && <p className="error">{yamlError}</p>}
        </div>
      )}
    </div>
  );
}
