import * as yaml from "js-yaml";
import { useEffect, useMemo, useRef, useState } from "react";
import { sanitizeFilename } from "../core/config";
import { Checkbox, NumberSlider, Section, Segmented } from "./controls";
import { translator, type Lang } from "./i18n";
import { PartitionEditor } from "./PartitionEditor";
import {
  DEFAULT_STATE,
  TOLERANCES,
  decodeShare,
  encodeShare,
  fromRawConfig,
  toRawConfig,
  type EditorState,
} from "./state";
import { useModel } from "./useModel";
import { Viewer } from "./Viewer";

const PROJECT_URL = "https://github.com/Owenwoow/BoxForge";

// Per-viewer conveniences only; the page works the same without storage.
const store = {
  get<T>(key: string, fallback: T): T {
    try {
      const v = localStorage.getItem(key);
      return v === null ? fallback : (JSON.parse(v) as T);
    } catch {
      return fallback;
    }
  },
  set(key: string, value: unknown) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* storage unavailable */
    }
  },
};

function initialState(): EditorState {
  return decodeShare(location.hash) ?? { ...DEFAULT_STATE, ...store.get<Partial<EditorState>>("bf.state", {}) };
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export function App() {
  const [lang, setLang] = useState<Lang>(() => store.get("bf.lang", navigator.language.startsWith("zh") ? "zh" : "en"));
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    store.get("bf.theme", matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"),
  );
  const [s, setS] = useState<EditorState>(initialState);
  const [exporting, setExporting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const t = useMemo(() => translator(lang), [lang]);

  const set = <K extends keyof EditorState>(key: K) => (value: EditorState[K]) => setS((prev) => ({ ...prev, [key]: value }));

  const raw = useMemo(() => toRawConfig(s), [s]);
  const model = useModel(raw);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    store.set("bf.theme", theme);
  }, [theme]);
  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.title = `BoxForge · ${t("title")}`;
    store.set("bf.lang", lang);
  }, [lang, t]);
  useEffect(() => store.set("bf.state", s), [s]);

  const flash = (msg: string) => {
    setNotice(msg);
    setTimeout(() => setNotice(null), 2500);
  };

  const onDownload = async () => {
    setExporting(true);
    try {
      download(await model.exportStl(s.tolerance), sanitizeFilename(s.filename));
    } catch (e) {
      flash(t("model_error", { err: e instanceof Error ? e.message : String(e) }));
    } finally {
      setExporting(false);
    }
  };

  const onExportYaml = () => {
    const text = yaml.dump(raw, { flowLevel: 3, lineWidth: 120 });
    download(new Blob([text], { type: "text/yaml" }), sanitizeFilename(s.filename).replace(/\.stl$/i, ".yaml"));
  };

  const onImportYaml = async (file: File | undefined) => {
    if (!file) return;
    try {
      setS(fromRawConfig(yaml.load(await file.text())));
    } catch (e) {
      flash(t("e_import_error", { err: e instanceof Error ? e.message : String(e) }));
    }
  };

  const onShare = async () => {
    const url = `${location.origin}${location.pathname}#c=${encodeShare(s)}`;
    history.replaceState(null, "", url);
    try {
      await navigator.clipboard.writeText(url);
      flash(t("e_share_done"));
    } catch {
      flash(url);
    }
  };

  const minLW = Math.min(s.length, s.width);
  const st = model.stats;
  const busy = model.kernel === "loading" || model.building;
  const canDownload = model.kernel === "ready" && !!st && !model.error && !model.building && !exporting;

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="brand">
          <h1>BoxForge</h1>
          <div className="toggles">
            <Segmented
              label="Language"
              value={lang}
              options={[
                { value: "zh", label: "中文" },
                { value: "en", label: "EN" },
              ]}
              onChange={setLang}
            />
            <Segmented
              label="Theme"
              value={theme}
              options={[
                { value: "light", label: t("theme_light") },
                { value: "dark", label: t("theme_dark") },
              ]}
              onChange={setTheme}
            />
          </div>
        </header>

        <Section title={t("sec_dimensions")} open>
          <NumberSlider label={t("f_length")} value={s.length} min={20} max={250} step={1} onChange={set("length")} />
          <NumberSlider label={t("f_width")} value={s.width} min={20} max={250} step={1} onChange={set("width")} />
          <NumberSlider label={t("f_height")} value={s.height} min={10} max={200} step={1} onChange={set("height")} />
          <NumberSlider label={t("f_wall")} value={s.wall} min={0.8} max={6} step={0.1} onChange={set("wall")} />
        </Section>

        <Section title={t("sec_fillet")}>
          <NumberSlider
            label={t("f_corner_radius")}
            value={s.cornerRadius}
            min={0}
            max={minLW / 2}
            step={0.5}
            onChange={set("cornerRadius")}
          />
          <NumberSlider label={t("f_edge_top")} value={s.edgeTop} min={0} max={s.wall / 2} step={0.05} onChange={set("edgeTop")} />
          <NumberSlider
            label={t("f_edge_bottom")}
            value={s.edgeBottom}
            min={0}
            max={Math.min(s.height, minLW / 2)}
            step={0.1}
            onChange={set("edgeBottom")}
          />
        </Section>

        <Section title={t("sec_partitions")}>
          <PartitionEditor
            tree={s.tree}
            onChange={set("tree")}
            length={s.length}
            width={s.width}
            height={s.height}
            wall={s.wall}
            t={t}
          />
        </Section>

        <Section title={t("sec_hollow")}>
          <NumberSlider label={t("h_hole_size")} value={s.holeSize} min={3} max={20} step={0.5} onChange={set("holeSize")} />
          <div className="field">
            <span>{t("h_border")}</span>
            <Segmented
              label={t("h_border")}
              value={s.borderAuto ? "auto" : "custom"}
              options={[
                { value: "auto", label: t("h_border_auto") },
                { value: "custom", label: t("h_border_custom") },
              ]}
              onChange={(v) => set("borderAuto")(v === "auto")}
            />
          </div>
          {!s.borderAuto && (
            <NumberSlider label={t("h_border_value")} value={s.border} min={0} max={20} step={0.5} onChange={set("border")} />
          )}
          <Checkbox label={t("h_bottom")} checked={s.ventBottom} onChange={set("ventBottom")} />
          <Checkbox label={t("h_partitions")} checked={s.ventPartitions} onChange={set("ventPartitions")} />
        </Section>

        <Section title={t("sec_export")}>
          <label className="field">
            <span>{t("e_tolerance")}</span>
            <select value={s.tolerance} onChange={(e) => set("tolerance")(Number(e.target.value))}>
              {TOLERANCES.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>{t("e_filename")}</span>
            <input type="text" value={s.filename} onChange={(e) => set("filename")(e.target.value)} />
          </label>
          <div className="button-row">
            <button type="button" className="btn" onClick={onExportYaml}>
              {t("e_export_yaml")}
            </button>
            <button type="button" className="btn" onClick={() => fileInput.current?.click()}>
              {t("e_import_yaml")}
            </button>
            <input
              ref={fileInput}
              type="file"
              accept=".yaml,.yml,text/yaml"
              hidden
              onChange={(e) => {
                void onImportYaml(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </div>
          <button type="button" className="btn" onClick={onShare}>
            {t("e_share")}
          </button>
        </Section>
      </aside>

      <main className="main">
        <div className="intro">
          <h2>{t("title")}</h2>
          <p>{t("caption")}</p>
        </div>

        {model.kernel === "failed" && <p className="error">{t("fatal", { err: model.fatal ?? "" })}</p>}
        {model.error && (
          <p className="error" data-testid="model-error">
            {t(model.error.kind === "config" ? "config_error" : "model_error", { err: model.error.message })}
          </p>
        )}
        {model.warnings.length > 0 && !model.error && (
          <p className="warning">
            {t("warnings")}: {model.warnings.join("; ")}
          </p>
        )}

        <div className="stage">
          <Viewer mesh={model.mesh} theme={theme} busy={busy} />
          {busy && model.kernel !== "failed" && (
            <div className="status">{model.kernel === "loading" ? t("loading_kernel") : t("building")}</div>
          )}
        </div>

        <div className="metrics" data-testid="metrics">
          <div>
            <span>{t("m_size")}</span>
            <strong>{st ? st.size.map((v) => v.toFixed(1)).join(" × ") : "—"}</strong>
          </div>
          <div>
            <span>{t("m_volume")}</span>
            <strong>{st ? (st.volume / 1000).toFixed(1) : "—"}</strong>
          </div>
          <div>
            <span>{t("m_valid")}</span>
            <strong data-testid="valid" className={st ? (st.valid ? "ok" : "bad") : ""}>
              {st ? t(st.valid ? "m_valid_ok" : "m_valid_fail") : "—"}
            </strong>
          </div>
          <div>
            <span>{t("m_time")}</span>
            <strong>{model.ms !== null ? `${Math.round(model.ms)} ms` : "—"}</strong>
          </div>
        </div>

        <button type="button" className="btn btn-primary download" disabled={!canDownload} onClick={onDownload}>
          {exporting ? t("downloading") : t("download_btn")}
        </button>
        {notice && <p className="notice">{notice}</p>}

        <footer className="footer">
          <p>
            {t("footer_project")}: <a href={PROJECT_URL}>{PROJECT_URL}</a>
          </p>
          <p>{t("footer_disclaimer")}</p>
        </footer>
      </main>
    </div>
  );
}
