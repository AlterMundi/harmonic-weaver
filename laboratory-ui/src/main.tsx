import {CollectiveGeometry} from "./CollectiveGeometry";
import {MovementMarks} from "./MovementMarks";
import {PerformanceControls} from "./PerformanceControls";
import {CalibrationReuse} from "./CalibrationReuse";

import { CapturePanel } from "./CapturePanel";
import { VideoFollower } from "./videoFollower";
import { EvaluationPanel } from "./EvaluationPanel";
import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Figure } from "./figure";
import "./style.css";

import {AudioOutputPanel} from './AudioOutputPanel';
const diagnosticReason = (reason:string) => ({
  'warming collective window':'Acumulando historia de movimiento colectivo',
  'missing collective support':'Faltan articulaciones para el análisis colectivo',
  'insufficient common observed collective support':'Faltan articulaciones observadas en común dentro de la ventana',
  'no established collective mode':'Todavía no hay un modo colectivo establecido',
  'degenerate component boundary':'Los componentes elegidos no se distinguen de forma estable',
  'requested mode exceeds established collective components':'Este modo excede los componentes colectivos establecidos',
  'no previous collective basis for angle comparison':'Falta una base colectiva anterior para comparar su cambio',
  'missing observation or warming history':'Faltan observaciones o historia suficiente',
} as Record<string,string>)[reason] || reason;
const ResearchPanel = lazy(() => import("./ResearchPanel").then(module => ({default: module.ResearchPanel})));

type Data = Record<string, any>;
let signalUnits: Data = {};
const labels: Record<string, string> = {
  master: "Master",
  transient_decay_s: "Cola de transientes (s)",
  expression_window_s: "Duración del contraste (s)",
  fundamental_hz: "Fundamental (Hz)",
  release_ms: "Liberación (ms)",
  pause_behavior: "Al pausar",
  id: "Identificador",
  label: "Nombre",
  ratio: "Relación con la fundamental",
  gain: "Ganancia",
  detune: "Desvío de afinación",
  phase_deg: "Fase (°)",
  pan: "Panorama",
  shape: "Forma de onda",
  muted: "Silenciar",
  solo: "Solo",
  voices: "Voces",
  response: "Respuesta del instrumento",
  core_falloff: "Atenuación por distancia",
  snap: "Recuperación de afinación",
  phase_depth: "Profundidad de fase (°)",
  pluck_enabled: "Impulsos con envolvente",
  attack_ms: "Ataque (ms)",
  tail_ms: "Cola del impulso (ms)",
  impulse_threshold: "Umbral de impulso",
  zones: "Regiones",
  sensitivity: "Sensibilidad",
  distance: "Distancia de referencia",
  speed_range: "Rango de velocidad (T/s)",
  accel_range: "Rango de aceleración (T/s²)",
  reference: "Referencia espacial",
  fixed_x: "Origen fijo X",
  fixed_y: "Origen fijo Y",
  joints: "Joints para análisis colectivo y velocidad global",
  tracking_filter_enabled: "Filtrar glitches de tracking",
  tracking_smoother: "Filtro: bounded = mediana/límite; harmocap_one_euro = HarMoCAP",
  tracking_one_euro_mincutoff: "One-Euro: corte mínimo (Hz)",
  tracking_one_euro_beta: "One-Euro: respuesta a velocidad (β)",
  tracking_one_euro_dcutoff: "One-Euro: corte de derivada (Hz)",
  tracking_hip_swap_guard: "Corregir intercambios de caderas por continuidad",
  tracking_one_euro_hip_swap_guard: "One-Euro: corregir intercambios de caderas antes de suavizar",
  tracking_median_frames: "Mediana causal (cuadros)",
  tracking_smoothing_s: "Suavizado del tracking (s)",
  tracking_joint_accel_limits: "Aceleración máxima por joint (T/s²)",
  show_raw_tracking: "Ver esqueleto crudo en vez del filtrado",
  smoothing_s: "Suavizado (s)",
  derivative_window_s: "Ventana de derivada (s)",
  horizon_s: "Horizonte de predicción (s)",
  history_s: "Historia relacional (s)",
  noise_velocity: "Ruido de velocidad (T/s)",
  noise_delta: "Ruido de contribución (T/s)",
  relation_reference: "Referencia relacional",
  window_s: "Ventana colectiva (s)",
  components: "Componentes",
  collective_support: "Soporte colectivo (observed: articulaciones visibles; fixed: todas)",
  ridge: "Regularización ridge",
  lag_s: "Retardo central a explorar (s)",
  propagation_interval_s: "Intervalo de ajuste retardado (s)",
  event_threshold: "Umbral de evento / ruido",
  refractory_s: "Refractario (s)",
  event_duration_s: "Duración de candidato (s)",
  max_gap_s: "Gap máximo (s)",
  routes: "Ruteos",
  voice: "Voz destino",
  target: "Parámetro destino",
  terms: "Entradas de la mezcla",
  source: "Señal de entrada",
  input_unit: "Unidad de entrada",
  weight: "Peso",
  offset: "Offset",
  exponent: "Exponente",
  deadband: "Zona muerta",
  absolute: "Valor absoluto",
  mix: "Mezcla",
  enabled: "Habilitado",
  clamp_min: "Límite mínimo",
  clamp_max: "Límite máximo",
  missing: "Si falta la señal",
  window_periods: "Ventana de dibujo (períodos)",
  samples: "Muestras de la figura",
  persistence: "Persistencia visual",
  collective_view: "Geometría del movimiento",
  collective_max_axes: "Ejes visibles de la geometría",
  line_width: "Grosor del trazo (px)",
  brightness: "Brillo",
  scale: "Escala",
  auto_scale: "Escala automática",
  color: "Paleta",
  mirror_video: "Espejar video",
  show_skeleton: "Mostrar esqueleto",
  on_disconnect: "Sin telemetría",
  macros: "Definición de macros",
  targets: "Destinos de macro",
  path: "Campo de configuración",
  minimum: "Mínimo",
  maximum: "Máximo",
  value: "Valor de macro",
  checkpoint: "Modelo pose local",
  device: "Dispositivo de tracking",
  imgsz: "Tamaño de inferencia",
  confidence: "Confianza de detección",
  joint_confidence: "Confianza por joint",
  max_detections: "Detecciones máximas",
  max_slots: "Personas máximas",
  tracker: "Tracker",
  reacquisition: "Reidentificación",
  camera_width: "Ancho de cámara",
  camera_height: "Alto de cámara",
  camera_fps: "FPS de cámara",
};
async function api(path: string, body?: any, method = "POST") {
  const response = await fetch(
    "/api/" + path,
    body === undefined
      ? {}
      : {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok)
    throw Object.assign(new Error(
      typeof data.detail === "string" ? data.detail : JSON.stringify(data),
    ), { status: response.status });
  return data;
}
const clone = (x: any) => structuredClone(x);
function defaults(schema: Data, defs: Data): any {
  if (schema.$ref) return defaults(defs[schema.$ref.split("/").pop()], defs);
  if (schema.default !== undefined) return clone(schema.default);
  if (schema.const !== undefined) return schema.const;
  if (schema.type === "object")
    return Object.fromEntries(
      Object.entries(schema.properties || {}).map(([k, s]) => [
        k,
        defaults(s as Data, defs),
      ]),
    );
  if (schema.type === "array") return [];
  if (schema.type === "boolean") return false;
  if (schema.enum) return schema.enum[0];
  return schema.type === "number" || schema.type === "integer"
    ? schema.minimum || 0
    : "";
}
function Fields({
  value,
  schema,
  defs,
  onChange,
  name = "",
  locked = false,
}: {
  value: any;
  schema: Data;
  defs: Data;
  onChange: (v: any) => void;
  name?: string;
  locked?: boolean;
}) {
  if (schema.$ref) schema = defs[schema.$ref.split("/").pop()];
  if (
    schema.const !== undefined ||
    ["schema_version", "version"].includes(name)
  )
    return null;
  if (schema.type === "object")
    return (
      <div className="fields">
        {Object.entries(schema.properties || {})
          .filter(
            ([key]) =>
              (schema.title !== "AlgorithmSettings" ||
              value?.id !== "baseline" ||
              (["id", "version", "horizon_s", "max_gap_s"].includes(key) || key.startsWith("tracking_"))) &&
              (schema.title !== "AlgorithmSettings" ||
                (key.startsWith("tracking_one_euro_")
                  ? value?.tracking_smoother === "harmocap_one_euro"
                  : !["tracking_hip_swap_guard", "tracking_median_frames", "tracking_smoothing_s", "tracking_joint_accel_limits"].includes(key) || value?.tracking_smoother !== "harmocap_one_euro")),
          )
          .map(([key, sub]) => (
            <Fields
              key={key}
              name={key}
              schema={sub as Data}
              defs={defs}
              value={value?.[key]}
              onChange={(v) =>
                onChange({
                  ...value,
                  [key]: v,
                  ...(schema.title === "AlgorithmSettings" && key === "id" && v === "collective" && value.id !== "collective"
                    ? {collective_support: "observed"} : {}),
                  ...(key === "source" && signalUnits[v]
                    ? { input_unit: signalUnits[v] }
                    : {}),
                })
              }
            />
          ))}
      </div>
    );
  if (schema.type === "array" && name === "joints")
    return (
      <fieldset>
        <legend>Articulaciones del análisis colectivo</legend>
        <div className="fields">
          {[
            "Nariz",
            "Ojo izquierdo",
            "Ojo derecho",
            "Oreja izquierda",
            "Oreja derecha",
            "Hombro izquierdo",
            "Hombro derecho",
            "Codo izquierdo",
            "Codo derecho",
            "Muñeca izquierda",
            "Muñeca derecha",
            "Cadera izquierda",
            "Cadera derecha",
            "Rodilla izquierda",
            "Rodilla derecha",
            "Tobillo izquierdo",
            "Tobillo derecho",
          ].map((label, index) => (
            <label className="check" key={index}>
              <input
                type="checkbox"
                checked={value.includes(index)}
                disabled={value.includes(index) && value.length <= 2}
                onChange={(e) =>
                  onChange(
                    e.target.checked
                      ? [...value, index].sort((a, b) => a - b)
                      : value.filter((j: number) => j !== index),
                  )
                }
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>
    );
  if (schema.type === "array" && name === "tracking_joint_accel_limits")
    return <fieldset><legend>{labels[name]}</legend><div className="fields">
      {["Nariz","Ojo izquierdo","Ojo derecho","Oreja izquierda","Oreja derecha","Hombro izquierdo","Hombro derecho","Codo izquierdo","Codo derecho","Muñeca izquierda","Muñeca derecha","Cadera izquierda","Cadera derecha","Rodilla izquierda","Rodilla derecha","Tobillo izquierdo","Tobillo derecho"].map((label,index) =>
        <label key={index}>{label}<input aria-label={`Aceleración máxima ${label}`} type="number" min="0.1" max="2000" step="1" value={value[index]} onChange={e => {const next=clone(value);next[index]=Number(e.target.value);onChange(next);}}/></label>)}</div>
      <p>T = torso proyectado; son límites ajustables del filtro, no límites anatómicos.</p></fieldset>;
  if (schema.type === "array")
    return (
      <fieldset>
        <legend>{labels[name] || name.replaceAll("_", " ")}</legend>
        {(value || []).map((v: any, i: number) => (
          <details key={i}>
            <summary>
              {v.label ||
                v.id ||
                (name === "zones"
                  ? [
                      "Caderas",
                      "Hombros",
                      "Rodillas",
                      "Codos",
                      "Tobillos",
                      "Muñecas",
                    ][i]
                  : `${labels[name] || name} ${i + 1}`)}
            </summary>
            <Fields
              value={v}
              schema={schema.items}
              defs={defs}
              onChange={(newValue) => {
                const next = clone(value);
                next[i] = newValue;
                onChange(next);
              }}
            />
            {value.length > (schema.minItems || 0) && (
              <button
                onClick={() =>
                  onChange(value.filter((_: any, j: number) => i !== j))
                }
              >
                Quitar
              </button>
            )}
          </details>
        ))}
        {value?.length < (schema.maxItems || 64) && (
          <button
            onClick={() => {
              const item = defaults(schema.items, defs);
              if (item && typeof item === "object" && !Array.isArray(item)) {
                if ("id" in item)
                  item.id =
                    name === "voices"
                      ? Math.max(0, ...value.map((v: any) => v.id)) + 1
                      : "route-" + crypto.randomUUID().slice(0, 8);
                if (name === "voices") {
                  item.ratio = item.id;
                  item.label = "Voz " + item.id;
                }
              }
              onChange([...(value || []), item]);
            }}
          >
            Agregar {labels[name] || name}
          </button>
        )}
      </fieldset>
    );
  const title =
    name === "components" && schema.type === "boolean"
      ? "Mostrar componentes"
      : labels[name] || name.replaceAll("_", " ");
  if (schema.enum)
    return (
      <label>
        {title}
        <select
          aria-label={title}
          value={value ?? schema.enum[0]}
          onChange={(e) => onChange(e.target.value)}
        >
          {schema.enum.map((v: any) => (
            <option key={v} value={v}>{name === "collective_view"
              ? ({off:"Apagada",projector:"Proyector del subespacio",basis:"Base y modos"} as Data)[v] : v}</option>
          ))}
        </select>
      </label>
    );
  if (schema.type === "boolean")
    return (
      <label className="check">
        <input
          type="checkbox"
          checked={!!value}
          onChange={(e) => onChange(e.target.checked)}
        />
        {title}
      </label>
    );
  if (schema.type === "number" || schema.type === "integer")
    return (
      <label>
        {title}
        <input
          aria-label={title}
          type="number"
          step={schema.multipleOf || (schema.type === "integer" ? 1 : "any")}
          min={schema.minimum ?? schema.exclusiveMinimum}
          max={schema.maximum}
          value={value ?? ""}
          onChange={(e) => {
            if (
              e.target.value !== "" &&
              Number.isFinite(e.target.valueAsNumber)
            )
              onChange(e.target.valueAsNumber);
          }}
        />
        <small>
          {schema.description ||
            `${schema.minimum ?? schema.exclusiveMinimum ?? "−∞"} … ${schema.maximum ?? "∞"}`}
        </small>
      </label>
    );
  return (
    <label>
      {title}
      <input
        aria-label={title}
        disabled={locked}
        list={name === "source" ? "signal-catalog" : undefined}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function App() {
  const [performance, setPerformance] = useState(() => {
    try { return localStorage.getItem("weaver-lab-performance") === "true"; } catch { return false; }
  });
  const [state, setState] = useState<Data>({}),
    [schemas, setSchemas] = useState<Data>({}),
    [draft, setDraft] = useState<Data | null>(null);
  const [tab, setTab] = useState("Fuente"),
    [error, setError] = useState(""),
    [connected, setConnected] = useState(false);
  const [perception, setPerception] = useState<Data | null>(null),
    [path, setPath] = useState(""),
    [camera, setCamera] = useState(0),
    [assets, setAssets] = useState<Data[]>([]),
    [presets, setPresets] = useState<Data[]>([]);
  const [presetName, setPresetName] = useState(""),
    [savedCalibrations, setSavedCalibrations] = useState<Data[]>([]);
  const [sourcePreferences, setSourcePreferences] = useState<Data>({default_person:"best_coverage", autoplay_video:true});
  const [qualityResult, setQuality] = useState<{jobId:string,report:Data} | null>(null);
  const quality = qualityResult?.jobId === state.source?.job?.id ? qualityResult?.report : null;
  const [algorithms, setAlgorithms] = useState<Data[]>([]);
  const [pending, setPending] = useState(false),
    [figureError, setFigureError] = useState("");
  const current = useRef<Data | null>(null),
    revision = useRef(0),
    dirty = useRef(false),
    generation = useRef(0),
    sending = useRef(false),
    timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const video = useRef<HTMLVideoElement>(null),
    canvas = useRef<HTMLCanvasElement>(null),
    figure = useRef<Figure | null>(null);
  const figureStream = useRef<string | null>(null);
  const macroQueue = useRef<{ id: string; value: number } | null>(null);
  const macroBusy = useRef(false);
  const presetBusy = useRef(false);
  const presetQueue = useRef<{preset: Data; generation: number} | null>(null);
  const [presetProgress, setPresetProgress] = useState("");
  const run = async (action: () => Promise<any>) => {
    try {
      setError("");
      return await action();
    } catch (e) {
      setError(String(e));
    }
  };
  const applyPreset = (preset: Data) => {
    presetQueue.current = {preset, generation: generation.current};
    setPresetProgress(`Elegido: ${preset.name}`);
    if (presetBusy.current) return;
    presetBusy.current = true;
    void run(async () => {
      try {
        while (presetQueue.current) {
          const choice = presetQueue.current;
          presetQueue.current = null;
          // A subsequent control edit takes precedence over an older choice.
          if (choice.generation !== generation.current) continue;
          const next = await api(`presets/${choice.preset.id}/apply`, {
            expected_revision: revision.current,
          });
          if (choice.generation !== generation.current ||
              next.session.desired_revision < revision.current) continue;
          revision.current = next.session.desired_revision;
          dirty.current = false;
          current.current = next.preset;
          setDraft(next.preset);
        }
      } finally {
        presetQueue.current = null;
        presetBusy.current = false;
        setPresetProgress("");
      }
    });
  };
  const inventoryRequests = useRef<Record<string, number>>({});
  const refreshInventory = async (path: string, accept: (rows: Data[]) => void) => {
    const request = (inventoryRequests.current[path] ?? 0) + 1;
    inventoryRequests.current[path] = request;
    try {
      const rows = await api(path);
      if (inventoryRequests.current[path] === request) accept(rows);
    } catch (e) {
      if (inventoryRequests.current[path] === request) throw e;
    }
  };
  useEffect(() => () => {
    presetQueue.current = null;
    // Invalidate in-flight reads without reusing tokens on a StrictMode remount.
    for (const path of Object.keys(inventoryRequests.current))
      inventoryRequests.current[path] += 1;
  }, []);
  const refresh = () =>
    Promise.all([
      refreshInventory("media", setAssets),
      refreshInventory("presets", setPresets),
      refreshInventory("calibrations", setSavedCalibrations),
    ]);
  useEffect(() => {
    if (state.source?.job?.status === "ready")
      refreshInventory("media", setAssets)
        .catch((e) => setError(String(e)));
  }, [state.source?.job?.id, state.source?.job?.status]);
  useEffect(() => {
    let active = true;
    setQuality(null);
    if (state.source?.job?.status === "ready") {
      const jobId = state.source.job.id;
      api(`media/${jobId}/quality`)
        .then((report) => { if (active) setQuality({jobId,report}); })
        .catch((e) => { if (active) setError(String(e)); });
    }
    return () => { active = false; };
  }, [state.source?.job?.id, state.source?.job?.status]);
  useEffect(() => {
    api("source-preferences").then(setSourcePreferences).catch((e) => setError(String(e)));
    api("algorithms")
      .then(setAlgorithms)
      .catch((e) => setError(String(e)));
    api("signals")
      .then((x) => {
        signalUnits = x;
      })
      .catch((e) => setError(String(e)));
    api("schemas")
      .then(setSchemas)
      .catch((e) => setError(String(e)));
    api("environment")
      .then((x) => setPerception(x.perception))
      .catch((e) => setError(String(e)));
    refresh().catch((e) => setError(String(e)));
  }, []);
  useEffect(() => {
    let closed = false,
      socket: WebSocket,
      reconnect: ReturnType<typeof setTimeout>;
    const connect = () => {
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
      );
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => {
        const next = JSON.parse(e.data);
        setState(next);
        if (!dirty.current) {
          revision.current = next.session.desired_revision;
          dirty.current = false;
          current.current = next.preset;
          setDraft(next.preset);
        }
      };
      socket.onclose = () => {
        setConnected(false);
        if (!closed) reconnect = setTimeout(connect, 1000);
      };
    };
    connect();
    return () => {
      closed = true;
      clearTimeout(reconnect);
      socket?.close();
    };
  }, []);
  const flush = async () => {
    if (sending.current || !current.current) return;
    sending.current = true;
    const g = generation.current;
    try {
      const result = await api(
        "configuration",
        { expected_revision: revision.current, preset: current.current },
        "PUT",
      );
      revision.current = result.session.desired_revision;
      if (g === generation.current) {
        dirty.current = false;
        setPending(false);
        setError("");
      }
    } catch (e) {
      setError(String(e));
      setPending(false);
    } finally {
      sending.current = false;
      if (g !== generation.current) void flush();
    }
  };
  const edit = (next: Data) => {
    current.current = next;
    setDraft(next);
    dirty.current = true;
    generation.current++;
    setPending(true);
    if (timer.current === undefined)
      timer.current = setTimeout(() => {
        timer.current = undefined;
        void flush();
      }, 16);
  };
  const change = (key: string, value: any) => {
    if (current.current) edit({ ...current.current, [key]: value });
  };
  const applyMacro = async (id: string, value: number) => {
    macroQueue.current = { id, value };
    setDraft((previous) =>
      previous
        ? {
            ...previous,
            macros: previous.macros.map((macro: Data) =>
              macro.id === id ? { ...macro, value } : macro,
            ),
          }
        : previous,
    );
    if (macroBusy.current) return;
    macroBusy.current = true;
    dirty.current = true;
    try {
      while (macroQueue.current) {
        const next = macroQueue.current;
        macroQueue.current = null;
        const result = await api(`macros/${next.id}`, {
          value: next.value,
          expected_revision: revision.current,
        });
        revision.current = result.session.desired_revision;
        current.current = result.preset;
        const queued = macroQueue.current as {
          id: string;
          value: number;
        } | null;
        const shown = clone(result.preset);
        if (queued)
          shown.macros = shown.macros.map((macro: Data) =>
            macro.id === queued.id ? { ...macro, value: queued.value } : macro,
          );
        setDraft(shown);
      }
      setError("");
    } catch (e) {
      macroQueue.current = null;
      setError(String(e));
    } finally {
      macroBusy.current = false;
      dirty.current = false;
    }
  };
  const transport = (body: Data) => run(() => api("transport", body));
  const playback = useRef({ position: 0, playing: false, epoch: 0 });
  const follower = useRef<VideoFollower | null>(null);
  playback.current = { position: state.session?.position_s || 0,
    playing: !!state.session?.playing, epoch: state.runtime?.epoch || 0 };
  useEffect(() => {
    const el = video.current;
    if (!el || state.source?.kind !== "video") return;
    const instance = new VideoFollower(el, () => playback.current, setError);
    follower.current = instance;
    instance.sync();
    return () => { instance.dispose(); follower.current = null; };
  }, [state.source?.kind, state.source?.job?.id, !!draft, !!schemas.Preset]);
  useEffect(() => { follower.current?.sync(); },
    [state.session?.position_s, state.session?.playing, state.runtime?.epoch]);
  useEffect(() => {
    if (!canvas.current) return;
    try {
      figure.current = new Figure(canvas.current);
      figureStream.current = null;
    } catch (e) {
      setFigureError(String(e));
    }
    return () => figure.current?.dispose();
  }, [!!draft, !!schemas.Preset]);
  useEffect(() => {
    if (!figure.current || !draft) return;
    if (connected && state.shaper?.telemetry_valid) {
      const stream = state.voice_frame?.audio_health?.engine_id;
      if (stream && stream !== figureStream.current) {
        figure.current.clear();
        figureStream.current = stream;
      }
      figure.current.draw(
        state.voice_frame.voices,
        draft.visual,
        draft.fundamental_hz,
      );
    } else if (draft.visual.on_disconnect === "clear") figure.current.clear();
  }, [
    connected,
    state.voice_frame?.sample_index,
    state.voice_frame?.audio_health?.engine_id,
    state.shaper?.telemetry_valid,
    draft?.visual,
    draft?.fundamental_hz,
  ]);
  if (!draft || !schemas.Preset)
    return (
      <main>
        <h1>Weaver / laboratorio corporal</h1>
        <p>Conectando con el laboratorio…</p>
        <p role="alert">{error}</p>
      </main>
    );
  const defs = schemas.Preset.$defs,
    props = schemas.Preset.properties,
    job = state.source?.job,
    session = state.session || {};
  const canMeasureScale = !pending && state.motion_frame?.persons?.some((p:Data)=>p.person_id===session.person_id &&
    [5,6,11,12].every(index=>p.joints.some((j:Data)=>j.index===index && j.state==='observed' && j.position)));
  const displayedMotion = (draft.visual.show_raw_tracking ? state.motion_frame : state.conditioned_motion_frame) || state.motion_frame;
  const form = (key: string) => (
    <Fields
      name={key}
      value={draft[key]}
      schema={props[key]}
      defs={defs}
      onChange={(v) => change(key, v)}
    />
  );
  const exportPreset = () => {
    const blob = new Blob([JSON.stringify(current.current, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = (draft.name || "preset") + ".json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const saveCurrentPreset = () => run(async () => {
    const preset = {...current.current, id:crypto.randomUUID().replaceAll("-", ""), name:presetName || draft.name};
    await api("presets",preset);
    await refresh();
  });
  const changeView = (value:boolean) => {
    setPerformance(value);
    try { localStorage.setItem("weaver-lab-performance",String(value)); } catch { /* view still works without browser storage */ }
  };
  return (
    <main className={performance ? "performance-mode" : undefined}>
      <datalist id="signal-catalog">
        {Object.entries(signalUnits).map(([key, unit]) => (
          <option key={key} value={key}>
            {String(unit)}
          </option>
        ))}
      </datalist>
      <header>
        <div>
          <span className="eyebrow">MOVIMIENTO · SONIDO · GEOMETRÍA</span>
          <h1>
            Weaver <span>/ laboratorio corporal</span>
          </h1>
        </div>
        <div className="actions" role="group" aria-label="Vista del laboratorio">
          <button aria-pressed={!performance} onClick={()=>changeView(false)}>Explorar</button>
          <button aria-pressed={performance} onClick={()=>changeView(true)}>Performance</button>
        </div>
        <div className="status">
          <i className={connected ? "lit" : ""} />
          {connected ? "En línea" : "Reconectando"}
          <span>
            {pending
              ? "Aplicando…"
              : `rev ${session.desired_revision ?? 0} → ${state.shaper?.applied_revision ?? "—"}`}
          </span>
        </div>
      </header>
      <div className="stage">
        <section className="source-view">
          <div className="stage-label">
            {job?.name ||
              (state.source?.kind === "camera" ? "Cámara" : "Tu movimiento")}
            <span>{session.status || "Sin fuente"}</span>
          </div>
          <div
            className={
              "video-wrap " + (draft.visual.mirror_video ? "mirror" : "")
            }
          >
            {state.source?.kind === "video" && (
              <video
                ref={video}
                src={`/api/media/${job.id}/file`}
                preload="auto"
                muted
                playsInline
                onError={() =>
                  setError(
                    "El navegador no puede reproducir este formato. Probá un MP4 H.264.",
                  )
                }
              />
            )}
            {state.source?.kind === "camera" && (
              <img
                alt="Cámara en vivo"
                src={`/api/camera/preview?t=${state.motion_frame?.sequence ?? 0}`}
              />
            )}
            {!state.source?.kind && (
              <div className="empty">
                <b>El cuerpo como instrumento</b>
                <p>Abrí un video o encendé la cámara para explorar.</p>
              </div>
            )}
            {draft.visual.show_skeleton && displayedMotion && (
              <svg
                className="skeleton"
                viewBox={`0 0 ${displayedMotion.width / displayedMotion.height} 1`}
                preserveAspectRatio="xMidYMid meet"
              >
                {displayedMotion.persons.map((p: Data) => (
                  <g
                    key={p.person_id}
                    opacity={p.person_id === session.person_id ? 1 : 0.3}
                  >
                    {[
                      [5, 6],
                      [5, 7],
                      [7, 9],
                      [6, 8],
                      [8, 10],
                      [5, 11],
                      [6, 12],
                      [11, 12],
                      [11, 13],
                      [13, 15],
                      [12, 14],
                      [14, 16],
                    ].map(([a, b]) => {
                      const ja = p.joints.find((j: Data) => j.index === a),
                        jb = p.joints.find((j: Data) => j.index === b);
                      return ja?.state === "observed" &&
                        jb?.state === "observed" ? (
                        <line
                          key={`${a}-${b}`}
                          x1={ja.position[0]}
                          y1={ja.position[1]}
                          x2={jb.position[0]}
                          y2={jb.position[1]}
                        />
                      ) : null;
                    })}
                    {p.joints
                      .filter((j: Data) => j.state === "observed")
                      .map((j: Data) => (
                        <circle
                          key={j.index}
                          cx={j.position[0]}
                          cy={j.position[1]}
                          r=".007"
                        />
                      ))}
                  </g>
                ))}
              </svg>
            )}
          </div>
          <div className="transport">
            <button
              disabled={!state.source?.kind}
              onClick={() => transport({ playing: !session.playing })}
            >
              {session.playing ? "Pausar" : "Reproducir"}
            </button>
            <input
              aria-label="Posición del video"
              type="range"
              min="0"
              max={job?.duration_s || 1}
              step=".01"
              disabled={!job}
              value={session.position_s || 0}
              onChange={(e) =>
                transport({ position_s: Number(e.target.value) })
              }
            />
            <span>{(session.position_s || 0).toFixed(1)} s</span>
            <label className="check">
              <input
                type="checkbox"
                checked={session.loop ?? true}
                onChange={(e) => transport({ loop: e.target.checked })}
              />
              Loop
            </label>
            {(job?.status === 'building' || session.loop_end_s != null) && <>
              <label className="check"><input type="checkbox" checked={session.loop_end_s != null}
                disabled={pending || !(job?.prefix_s > 0)}
                onChange={e=>transport({tracked_prefix:e.target.checked})}/>Loop sobre prefijo trackeado</label>
              {session.loop_end_s != null && <span>
                Hasta {session.loop_end_s.toFixed(1)} s · límite fijo
                <button disabled={pending || !(job?.prefix_s > session.loop_end_s)}
                  onClick={()=>transport({tracked_prefix:true})}>Ampliar al prefijo disponible</button>
              </span>}
            </>}
          </div>
        </section>
        <section className="figure-view">
          <div className="stage-label">
            Figura polifónica
            <span>
              {state.voice_frame?.voices?.length || 0} osciladores efectivos
            </span>
          </div>
          <canvas ref={canvas} />
          <p className="figure-caption">
            Suma de todos los armónicos activos · antes de shape / limiter ·
            aproximación geométrica, no cymatics físico
          </p>
          {figureError && <p role="alert">{figureError}</p>}
        </section>
      </div>
      <CollectiveGeometry features={state.features} visual={draft.visual} algorithm={draft.algorithm.id}/>
      {state.shaper?.audio_disabled && (
        <aside role="status">
          Modo diagnóstico sin audio (--no-audio). Reiniciá sin esa opción para
          escuchar y ver la figura de las voces efectivas.
        </aside>
      )}
      {(error ||
        state.runtime?.error ||
        state.shaper?.error ||
        state.source?.camera?.error ||
        job?.error) && (
        <aside className="error" role="alert">
          {error ||
            state.runtime?.error ||
            state.shaper?.error ||
            state.source?.camera?.error ||
            job?.error}
          <button
            onClick={() => {
              dirty.current = false;
              setPending(false);
              setError("");
            }}
          >
            Recuperar estado aplicado
          </button>
        </aside>
      )}
      <div className="workspace">
        <section className="controls">
          <nav hidden={performance}>
            {[
              "Fuente",
              "Instrumento",
              "Modelos",
              "Ruteos",
              "Figura",
              "Presets",
              "Comparar",
              "Captura",
              "Investigación",
            ].map((t) => (
              <button
                className={tab === t ? "active" : ""}
                key={t}
                onClick={() => setTab(t)}
              >
                {t}
              </button>
            ))}
          </nav>
          <div className="panel">
            {performance && <PerformanceControls draft={draft} presets={presets} pending={pending}
              change={change} applyPreset={applyPreset} applyMacro={applyMacro} save={saveCurrentPreset}
              exportPreset={exportPreset} name={presetName} setName={setPresetName} personId={session.person_id}
              personIds={[...new Set<string>([session.person_id,...(job?.person_ids || []),...(state.motion_frame?.persons || []).map((p:Data)=>p.person_id)].filter(Boolean))]}
              choosePerson={id=>run(()=>api("person",{person_id:id}))}
              selectionStatus={state.runtime?.selection_status}
              canConfirmPerson={state.runtime?.can_confirm_person === true}
              mark={()=>run(()=>api("marks",{text:"Se siente bien",category:"experience"}))}/>}
            <div hidden={performance}>
            {tab === "Investigación" && <Suspense fallback={<p>Cargando bancos de investigación…</p>}><ResearchPanel api={api} run={run}/></Suspense>}
            {tab === "Captura" && <CapturePanel api={api} run={run}/>}
            {tab === "Comparar" && (
              <EvaluationPanel
                assets={assets}
                presets={presets}
                calibrations={savedCalibrations}
                person={session.person_id}
                api={api}
                run={run}
              />
            )}
            {tab === "Fuente" && (
              <>
                <h2>Fuente y percepción</h2>
                <p>
                  El tracking del archivo se guarda y se reutiliza. Cambiar el
                  sonido no lo recalcula.
                </p>
                <label>
                  Ruta del video
                  <input
                    value={path}
                    onChange={(e) => setPath(e.target.value)}
                    placeholder="/home/…/rope-flow.mp4"
                  />
                </label>
                <div className="actions">
                  <button
                    disabled={!path || !perception}
                    onClick={() =>
                      run(async () => {
                        await api("sources/video", { path, perception });
                        await refresh();
                      })
                    }
                  >
                    Abrir video
                  </button>
                  <button
                    disabled={!job}
                    onClick={() =>
                      run(() =>
                        api("sources/video", {
                          path: job.path,
                          perception,
                          force: true,
                        }),
                      )
                    }
                  >
                    Forzar tracking
                  </button>
                  {job &&
                    ["hashing", "probing", "building"].includes(job.status) && (
                      <button
                        onClick={() =>
                          run(() => api(`media/${job.id}/cancel`, {}))
                        }
                      >
                        Cancelar tracking
                      </button>
                    )}
                </div>
                {job && (
                  <p className="notice">
                    {job.status} · {job.processed_frames} frames ·{" "}
                    {job.prefix_s?.toFixed(1)} s procesados ·{" "}
                    {job.cache_hit ? "cache reutilizado" : "extracción"}{" "}
                    {job.error}
                  </p>
                )}
                {job && ["error", "cancelled"].includes(job.status) && (
                  <button
                    onClick={() =>
                      run(async () => {
                        await api(`media/${job.id}/retry-cpu`, {});
                        await refresh();
                      })
                    }
                  >
                    Recuperar tracking con CPU
                  </button>
                )}
                {job && (
                  <p>
                    Backend solicitado:{" "}
                    {job.requested_device || job.perception?.device} · efectivo:{" "}
                    {job.effective_device || job.perception?.device}
                  </p>
                )}
                {quality && (
                  <details>
                    <summary>Cobertura de tracking y huecos</summary>
                    <p>{quality.warning}</p>
                    {Object.entries(quality.persons || {}).map(
                      ([id, value]) => (
                        <div key={id}>
                          <h3>{id}</h3>
                          <table>
                            <thead>
                              <tr>
                                <th>Articulación</th>
                                <th>Observado</th>
                                <th>Hueco máximo</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries((value as Data).joints).map(
                                ([joint, q]) => (
                                  <tr key={joint}>
                                    <td>
                                      {
                                        [
                                          "Nariz",
                                          "Ojo izquierdo",
                                          "Ojo derecho",
                                          "Oreja izquierda",
                                          "Oreja derecha",
                                          "Hombro izquierdo",
                                          "Hombro derecho",
                                          "Codo izquierdo",
                                          "Codo derecho",
                                          "Muñeca izquierda",
                                          "Muñeca derecha",
                                          "Cadera izquierda",
                                          "Cadera derecha",
                                          "Rodilla izquierda",
                                          "Rodilla derecha",
                                          "Tobillo izquierdo",
                                          "Tobillo derecho",
                                        ][Number(joint)]
                                      }
                                    </td>
                                    <td>
                                      {(
                                        (q as Data).observed_fraction * 100
                                      ).toFixed(1)}
                                      %
                                    </td>
                                    <td>
                                      {(q as Data).max_gap_s.toFixed(2)} s
                                    </td>
                                  </tr>
                                ),
                              )}
                            </tbody>
                          </table>
                        </div>
                      ),
                    )}
                  </details>
                )}
                <label className="file-button">
                  Elegir y cargar un video
                  <input
                    type="file"
                    accept="video/*"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f)
                        void run(async () => {
                          const body = new FormData();
                          body.append("file", f);
                          body.append(
                            "perception_json",
                            JSON.stringify(perception),
                          );
                          const r = await fetch("/api/sources/upload", {
                            method: "POST",
                            body,
                          });
                          const d = await r.json();
                          if (!r.ok) throw new Error(JSON.stringify(d));
                        });
                    }}
                  />
                </label>
                <label>
                  Videos de la biblioteca
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) {
                        setPath(e.target.value);
                        void run(() =>
                          api("sources/video", {
                            path: e.target.value,
                            perception,
                          }),
                        );
                      }
                    }}
                  >
                    <option value="">Elegir archivo guardado…</option>
                    {assets.map((a) => (
                      <option key={a.id} value={a.path}>
                        {a.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="actions">
                  <label>
                    Cámara
                    <input
                      type="number"
                      min="0"
                      max="32"
                      value={camera}
                      onChange={(e) => setCamera(e.target.valueAsNumber)}
                    />
                  </label>
                  <button
                    onClick={() =>
                      run(() =>
                        api("sources/camera", { index: camera, perception }),
                      )
                    }
                  >
                    Usar cámara
                  </button>
                  <button
                    disabled={!state.source?.kind}
                    onClick={() => run(() => api("sources/close", {}))}
                  >
                    Cerrar fuente / apagar cámara
                  </button>
                </div>
                <fieldset>
                  <legend>Al abrir un video</legend>
                  <label>Cuerpo por defecto
                    <select value={sourcePreferences.default_person} onChange={(e) => run(async () => {
                      const next={...sourcePreferences, default_person:e.target.value};
                      setSourcePreferences(await api("source-preferences", next));
                    })}>
                      <option value="best_coverage">Mejor cobertura de tracking</option>
                      <option value="first">Primera persona de la lista</option>
                    </select>
                  </label>
                  <label><input type="checkbox" checked={sourcePreferences.autoplay_video}
                    onChange={(e) => run(async () => {
                      const next={...sourcePreferences, autoplay_video:e.target.checked};
                      setSourcePreferences(await api("source-preferences", next));
                    })}/>Reproducir automáticamente cuando el tracking esté listo</label>
                  <small>La cobertura mide observaciones disponibles, no precisión. Una elección guardada tiene prioridad en el mismo tracking.</small>
                </fieldset>
                <label>
                  Persona
                  <select
                    value={session.person_id || ""}
                    onChange={(e) =>
                      run(() => api("person", { person_id: e.target.value }))
                    }
                  >
                    <option value="" disabled>
                      Elegir cuerpo…
                    </option>
                    {[
                      ...new Set<string>([
                        ...(state.source?.job?.person_ids || []),
                        ...(state.motion_frame?.persons || []).map(
                          (p: Data) => p.person_id,
                        ),
                      ]),
                    ].map((id) => (
                      <option key={id}>{id}</option>
                    ))}
                  </select>
                </label>
                <p role="status">
                  {
                    (
                      {
                        automatic: "Selección automática del cuerpo por defecto.",
                        explicit: "Cuerpo elegido explícitamente.",
                        restored:
                          "Selección recuperada de esta misma generación de tracking.",
                        automatic_changed:
                          "Tracking nuevo: cuerpo por defecto elegido nuevamente; verificá la selección.",
                      } as Data
                    )[state.runtime?.selection_status]
                  }
                </p>
                {state.runtime?.can_confirm_person === true && ['automatic','automatic_changed'].includes(state.runtime?.selection_status) &&
                  <button disabled={pending || !session.person_id}
                    onClick={()=>run(()=>api("person",{person_id:session.person_id}))}>Fijar esta persona</button>}
                <button
                  disabled={!canMeasureScale}
                  onClick={() =>
                    run(async () => {
                      await api("calibrate", {});
                      await refresh();
                    })
                  }
                >
                  Calibrar escala con este cuerpo
                </button>
                <p>
                  {state.calibration
                    ? `Escala fija: ${state.calibration.torso_scale.toFixed(4)} · ${state.calibration.provenance}`
                    : "Sin calibración. El baseline conserva su escala adaptativa; los otros modelos requieren calibrar."}
                </p>
                {state.calibration_notice&&<p role="status">{state.calibration_notice}</p>}
                <CalibrationReuse calibrations={savedCalibrations} sourceId={session.source_id}
                  personId={session.person_id} pending={pending}
                  reuse={id=>run(()=>api("calibrate",{reuse_id:id}))}/>
                {perception && schemas.PerceptionSettings && (
                  <details>
                    <summary>
                      Configuración de percepción (aplica al abrir / reprocesar)
                    </summary>
                    <Fields
                      value={perception}
                      schema={schemas.PerceptionSettings}
                      defs={schemas.PerceptionSettings.$defs || {}}
                      onChange={setPerception}
                    />
                  </details>
                )}
              </>
            )}
            {tab === "Instrumento" && (
              <>
                <h2>El instrumento</h2>
                <div className="fields">
                  {form("fundamental_hz")}
                  {form("master")}
                  <label>
                    Realce expresivo · {(draft.expression ?? 0).toFixed(2)}
                    <input
                      aria-label="Realce expresivo"
                      type="range"
                      min="-1"
                      max="10"
                      step=".01"
                      value={draft.expression ?? 0}
                      onChange={(e) =>
                        change("expression", Number(e.target.value))
                      }
                    />
                    <small>
                      − Más selectivo · 0 Neutral · 1 Máximo anterior · 10
                      Realce ×10. Acentúa subidas y bajadas sin elevar el
                      sostenido ni cambiar la afinación.
                    </small>
                    <button onClick={() => change("expression", 0)}>
                      Volver a neutral
                    </button>
                  </label>
                  {form("expression_window_s")}
                  <label>
                    Articulación ·{" "}
                    {Math.round((draft.transient_mix ?? 0) * 100)}% transientes
                    <input
                      aria-label="Articulación"
                      type="range"
                      min="0"
                      max="1"
                      step=".01"
                      value={draft.transient_mix ?? 0}
                      onChange={(e) =>
                        change("transient_mix", Number(e.target.value))
                      }
                    />
                    <small>
                      0 Sostenido · 100% Sólo impulsos de subida. Conserva fase
                      y afinación.
                    </small>
                  </label>
                  {form("transient_decay_s")}
                  {form("release_ms")}
                  {form("pause_behavior")}
                </div>
                {form("voices")}
                {form("response")}
                {draft.macros.map((m: Data) => (
                  <label key={m.id}>
                    {m.label}
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step=".01"
                      value={m.value}
                      disabled={pending}
                      onChange={(e) =>
                        void applyMacro(m.id, Number(e.target.value))
                      }
                    />
                  </label>
                ))}
                {form("macros")}
              </>
            )}
            {tab === "Modelos" && (
              <>
                <h2>Cómo interpretar el movimiento</h2>
                <p>
                  El modelo produce mediciones; Ruteos elige cuáles controlan
                  el sonido. Los presets afinados 08–11 hacen audible el error
                  local, la oposición relativa, la velocidad angular o los
                  modos colectivos mediante intensidad, con seis voces.
                  Elegilos en Presets y calibrá el torso de esta fuente/persona.
                </p>
                <p>
                  T = longitud de torso calibrada. Modelos exploratorios:
                  describen relaciones cinemáticas. No prueban intención,
                  causalidad ni eficacia corporal.
                </p>
                <p className="notice">
                  {
                    algorithms.find((a) => a.id === draft.algorithm.id)
                      ?.description
                  }
                </p>
                {form("algorithm")}
                {draft.algorithm.tracking_filter_enabled && <p role="status">
                  Filtro causal activo: {draft.algorithm.tracking_smoother || "bounded"}. {state.features?.diagnostics?.tracking_filter?.hip_labels_swapped ? "Intercambio de caderas corregido en este cuadro. " : ""}
                  Joints limitados ahora: {(state.features?.diagnostics?.tracking_filter?.acceleration_limited_joints || []).join(", ") || "ninguno"}.
                  En Figura podés alternar el esqueleto crudo y el filtrado.
                  {draft.algorithm.tracking_smoother === "harmocap_one_euro" && " One-Euro reemplaza la mediana y el límite de aceleración. La corrección de caderas es opcional e independiente: puede confundir un giro real con un intercambio de etiquetas. No rellena articulaciones perdidas."}
                </p>}
              </>
            )}
            {tab === "Ruteos" && (
              <>
                <h2>Señales → voces</h2>
                <p>
                  Una mezcla por destino. Cada entrada declara su unidad; los
                  cambios inválidos conservan la configuración anterior.
                </p>
                {form("routes")}
                <details>
                  <summary>Catálogo de señales actuales</summary>
                  <pre>{JSON.stringify(state.features?.signals, null, 2)}</pre>
                </details>
              </>
            )}
            {tab === "Figura" && (
              <>
                <h2>El dibujo del sonido</h2>
                <p>
                  Las fases, ganancias y envolventes vienen del motor de audio.
                  La figura reúne todas las voces, independientemente de los
                  componentes del análisis.
                </p>
                {form("visual")}
              </>
            )}
            {tab === "Presets" && (
              <>
                <h2>Volver a un lugar que se siente bien</h2>
                {form("favorite")}
                <label>
                  Nombre
                  <input
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    placeholder={draft.name}
                  />
                </label>
                <div className="actions">
                  <button
                    disabled={pending}
                    onClick={saveCurrentPreset}
                  >
                    Guardar como nuevo
                  </button>
                  <button onClick={exportPreset}>Exportar JSON</button>
                  <label className="file-button">
                    Importar JSON
                    <input
                      type="file"
                      accept=".json"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f)
                          void run(async () => {
                            const p = JSON.parse(await f.text());
                            await api("presets", p);
                            await refresh();
                          });
                      }}
                    />
                  </label>
                </div>
                {presetProgress && <p role="status">{presetProgress} · esperando confirmación</p>}
                <div className="preset-list">
                  {presets.map((p) => (
                    <button
                      key={p.id}
                      disabled={pending}
                      onClick={() => applyPreset(p)}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
                <div className="actions">
                  <button
                    disabled={!state.can_undo || pending}
                    onClick={() =>
                      run(() =>
                        api("undo", { expected_revision: revision.current }),
                      )
                    }
                  >
                    Deshacer
                  </button>
                  <button
                    disabled={!state.can_redo || pending}
                    onClick={() =>
                      run(() =>
                        api("redo", { expected_revision: revision.current }),
                      )
                    }
                  >
                    Rehacer
                  </button>
                </div>
                <p>
                  Los presets no llevan video, identidad, calibración ni
                  historia del análisis.
                </p>
              </>
            )}
            </div>
          </div>
        </section>
        <aside className="inspector">
          <h2>Lo que está pasando</h2>
          <p role="status" data-testid="model-status">
            {state.runtime?.diagnostic?.message}
          </p>
          <p>
            Señales observadas:{" "}
            {state.runtime?.diagnostic?.observed_signals ?? 0} · Articulaciones
            observadas: {state.runtime?.diagnostic?.pose?.observed ?? 0}/17
          </p>
          {state.runtime?.diagnostic?.audio_error && (
            <p role="alert">Audio: {state.runtime.diagnostic.audio_error}</p>
          )}
          {state.runtime?.diagnostic?.routed_signal_count != null && <p>
            Señales usadas por el ruteo: {state.runtime.diagnostic.routed_observed_signals}/{state.runtime.diagnostic.routed_signal_count} disponibles.
          </p>}
          {state.runtime?.routing?.voices && <details>
            <summary>Qué ocurre en cada voz</summary>
            {Object.entries(state.runtime.routing.voices).map(([id,value])=>{const v=value as Data;return <div key={id}>
              <strong>{v.label || `Voz ${id}`}</strong> · {v.reason} · ganancia enviada: {Number(v.target_gain).toFixed(3)}
              {v.issues?.length>0 && <ul>{v.issues.map((issue:Data,index:number)=><li key={index}>
                {issue.source || issue.route_id}: {diagnosticReason(issue.reason)} · {issue.target} {issue.effect==='zero'?'usa cero en este término':'bloquea esta voz'}.
              </li>)}</ul>}
            </div>;})}
          </details>}
          <details>
            <summary>Por qué faltan señales</summary>
            <pre>
              {JSON.stringify(
                state.runtime?.diagnostic?.routed_missing_signals ?? state.runtime?.diagnostic?.missing_signals,
                null,
                2,
              )}
            </pre>
          </details>
          {draft.algorithm.id !== "baseline" && !state.calibration && (
            <div role="status">
              <p>
                Este modelo necesita calibrar la escala corporal para producir
                señales.
              </p>
              <button
                disabled={!canMeasureScale}
                onClick={() =>
                  run(async () => {
                    await api("calibrate", {});
                    await refresh();
                  })
                }
              >
                Calibrar con el cuerpo visible
              </button>
              {!canMeasureScale && !pending && <p>Para medir, deben estar observados ambos hombros y ambas caderas de la persona seleccionada.</p>}
              <CalibrationReuse calibrations={savedCalibrations} sourceId={session.source_id}
                personId={session.person_id} pending={pending} matchingOnly
                reuse={id=>run(async()=>{await api("calibrate",{reuse_id:id});await refresh();})}/>
            </div>
          )}
          <AudioOutputPanel api={api} playing={session.playing}/>
          <dl>
            <dt>Algoritmo</dt>
            <dd>{state.features?.algorithm_id || draft.algorithm.id}</dd>
            <dt>Análisis por tick</dt>
            <dd>{state.runtime?.tick_ms?.toFixed(1) || "—"} ms</dd>
            <dt>Control a Shaper (ida y vuelta)</dt>
            <dd>{state.shaper?.control_roundtrip_ms?.toFixed(1) || "—"} ms</dd>
            <dt>Control → bloque de audio</dt>
            <dd>
              {state.shaper?.control_to_audio_block_ms?.toFixed(1) || "—"} ms
            </dd>
            <dt>Edad de telemetría</dt>
            <dd>{state.shaper?.telemetry_age_ms?.toFixed(0) || "—"} ms</dd>
            <dt>Buffer / frecuencia efectivos</dt>
            <dd>{state.shaper?.telemetry_valid ? `${state.voice_frame.block_frames} muestras / ${state.voice_frame.sample_rate} Hz` : "Sin telemetría vigente"}</dd>
            <dt>Cortes reportados por PortAudio (desde inicio del motor)</dt>
            <dd>{state.shaper?.telemetry_valid && state.voice_frame?.audio_health
              ? state.voice_frame.audio_health.output_underflows : "Diagnóstico no disponible"}</dd>
            {state.shaper?.telemetry_valid && state.voice_frame?.audio_health?.last_status && <>
              <dt>Último estado de PortAudio</dt>
              <dd>{state.voice_frame.audio_health.last_status} (muestra {state.voice_frame.audio_health.last_status_sample_index})</dd>
            </>}
          </dl>
          <p className="muted">
            Estas medidas no equivalen a latencia física movimiento → sonido.
            Un contador de cortes en cero no descarta clicks producidos por la síntesis ni fallos posteriores en la salida.
          </p>
          <div className="meters">
            {draft.voices.map((v: Data) => {
              const effective = state.voice_frame?.voices?.find(
                (x: Data) => x.harmonic_n === v.id,
              );
              return (
                <div key={v.id}>
                  <span>{v.label}</span>
                  <meter min="0" max="1" value={effective?.gain || 0} />
                  <small>{effective?.frequency_hz?.toFixed(1) || "—"} Hz</small>
                </div>
              );
            })}
          </div>
          <div hidden={performance}><MovementMarks api={api} run={run} sourceId={session.source_id} personId={session.person_id} currentSessionId={session.session_id} observedEpoch={state.runtime?.observed_epoch}/></div>
          <details>
            <summary>Diagnóstico del modelo</summary>
            <pre>{JSON.stringify(state.features?.diagnostics, null, 2)}</pre>
          </details>
          <details>
            <summary>Ruteos</summary>
            <pre>{JSON.stringify(state.runtime?.routing, null, 2)}</pre>
          </details>
        </aside>
      </div>
      <footer>
        Exploración en vivo · sin grabación de cámara ni audio por defecto ·
        seis voces iniciales
      </footer>
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
