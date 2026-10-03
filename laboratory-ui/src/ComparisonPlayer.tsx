import { useEffect, useRef, useState } from "react";
import { ComparisonExport } from "./ComparisonExport";
import { Figure } from "./figure";
import { voicesAt, sourcePosition, type Block } from "./replayClock";
type Data = Record<string, any>;

export function ComparisonPlayer({
  report,
  run: initialRun,
  onClose,
}: {
  report: Data;
  run: Data;
  onClose: () => void;
}) {
  const [run, setRun] = useState<Data>(initialRun);
  const [mediaReady, setMediaReady] = useState("");
  const [switching, setSwitching] = useState(false);
  const pendingSwitch = useRef<{
    file: string;
    position: number;
    resume: boolean;
  } | null>(null);
  const [loadedFrames, setLoadedFrames] = useState<{
    file: string;
    blocks: Block[];
  }>({ file: "", blocks: [] });
  const alternatives = (report.manifest.runs || []).filter(
    (r: Data) => r.pcm && r.source_index === initialRun.source_index,
  );
  const audio = useRef<HTMLAudioElement>(null),
    video = useRef<HTMLVideoElement>(null),
    canvas = useRef<HTMLCanvasElement>(null);
  const blocks =
    loadedFrames.file === run.pcm.voice_frames ? loadedFrames.blocks : [];
  const [error, setError] = useState("");
  const [rate, setRate] = useState(1),
    [offset, setOffset] = useState(0);
  const source = report.manifest.request.sources[run.source_index];
  const preset = report.manifest.request.presets[run.preset_index];
  const base = `/api/evaluations/${report.job_id}`;
  useEffect(() => {
    const abort = new AbortController();
    let live = true;
    setError("");
    fetch(`${base}/artifacts/${run.pcm.voice_frames}`, { signal: abort.signal })
      .then((r) => {
        if (!r.ok) throw Error(`Osciladores: HTTP ${r.status}`);
        return r.text();
      })
      .then((text) => {
        if (!live) return;
        const parsed = text
          .trim()
          .split("\n")
          .filter(Boolean)
          .map((line) => JSON.parse(line));
        if (!parsed.length)
          throw Error("La corrida no tiene estado de osciladores.");
        setLoadedFrames({ file: run.pcm.voice_frames, blocks: parsed });
      })
      .catch((e) => {
        if (live && e.name !== "AbortError") {
          audio.current?.pause();
          video.current?.pause();
          pendingSwitch.current = null;
          setSwitching(false);
          setError(String(e));
        }
      });
    return () => {
      live = false;
      abort.abort();
    };
  }, [base, run.pcm.voice_frames]);
  const switchRun = (next: Data) => {
    if (next.pcm.file === run.pcm.file) return;
    const a = audio.current;
    const previous = pendingSwitch.current;
    pendingSwitch.current = {
      file: next.pcm.file,
      position: previous?.position ?? a?.currentTime ?? 0,
      resume: previous?.resume ?? (!!a && !a.paused && !a.ended),
    };
    a?.pause();
    video.current?.pause();
    setError("");
    setMediaReady("");
    setSwitching(true);
    setRun(next);
  };
  useEffect(() => {
    const pending = pendingSwitch.current,
      a = audio.current;
    if (
      !pending ||
      !a ||
      mediaReady !== pending.file ||
      !blocks.length ||
      pending.file !== run.pcm.file
    )
      return;
    const position = Math.min(
      pending.position,
      Number.isFinite(a.duration) ? a.duration : pending.position,
    );
    a.currentTime = position;
    a.playbackRate = rate;
    a.preservesPitch = true;
    pendingSwitch.current = null;
    setSwitching(false);
    if (pending.resume && position < a.duration) {
      void a.play().catch((e) => {
        if (
          a.getAttribute("src") === `${base}/artifacts/${pending.file}` &&
          e.name !== "AbortError"
        )
          setError(`No se pudo reanudar: ${String(e)}. Usar Play.`);
      });
    }
  }, [blocks, mediaReady, run, base, rate]);
  useEffect(() => {
    if (!audio.current || !video.current || !canvas.current) return;
    const a = audio.current,
      v = video.current;
    let figure: Figure | null = null;
    try {
      figure = new Figure(canvas.current);
    } catch (e) {
      setError(String(e));
    }
    let disposed = false,
      timer = 0,
      pending = false,
      lastCorrection = -Infinity;
    a.playbackRate = rate;
    a.preservesPitch = true;
    v.playbackRate = rate;
    const sync = () => {
      if (disposed) return;
      const desired = sourcePosition(
        Math.min(a.currentTime, source.end_s - run.pcm.segment_source_start_s) +
          offset,
        run.pcm.segment_source_start_s,
        source.end_s,
      );
      const inTail =
        a.currentTime + run.pcm.segment_source_start_s >= source.end_s;
      if ((a.paused || inTail) && !v.paused) v.pause();
      const now = performance.now();
      if (
        v.readyState >= 1 &&
        !v.seeking &&
        Math.abs(v.currentTime - desired) > (a.paused ? 0.04 : 0.2) &&
        (a.paused || now - lastCorrection > 750)
      ) {
        v.currentTime = desired;
        lastCorrection = now;
      }
      if (
        !a.paused &&
        !inTail &&
        v.readyState >= 1 &&
        !v.seeking &&
        v.paused &&
        !pending
      ) {
        pending = true;
        void v
          .play()
          .catch((e) => {
            if (!disposed && e.name !== "AbortError") setError(String(e));
          })
          .finally(() => {
            pending = false;
            if (disposed || a.paused) v.pause();
          });
      }
      if (!a.paused)
        figure?.draw(
          voicesAt(blocks, a.currentTime),
          preset.visual,
          preset.fundamental_hz,
        );
      timer = requestAnimationFrame(sync);
    };
    const redraw = () => {
      figure?.clear();
      figure?.draw(
        voicesAt(blocks, a.currentTime),
        preset.visual,
        preset.fundamental_hz,
      );
    };
    a.addEventListener("seeked", redraw);
    a.addEventListener("pause", redraw);
    redraw();
    sync();
    return () => {
      disposed = true;
      cancelAnimationFrame(timer);
      v.pause();
      a.removeEventListener("seeked", redraw);
      a.removeEventListener("pause", redraw);
      figure?.dispose();
    };
  }, [blocks, rate, offset, preset, source, run]);
  useEffect(() => {
    const a = audio.current,
      v = video.current;
    return () => {
      a?.pause();
      v?.pause();
    };
  }, []);
  return (
    <section aria-label="Reproducción de comparación">
      <button onClick={onClose}>Cerrar reproducción</button>
      <button
        onClick={() => {
          if (pendingSwitch.current) pendingSwitch.current.resume = false;
          audio.current?.pause();
          video.current?.pause();
        }}
      >
        Pausar comparación
      </button>
      <p>
        Fuente {run.source_index + 1} · Persona {source.person_id} ·{" "}
        {preset.name}. Reloj: WAV; figura de todos los osciladores antes del
        timbre/limitador.
      </p>
      {alternatives.length > 1 && (
        <label>
          Preset del mismo segmento
          <select
            value={run.pcm.file}
            onChange={(e) => {
              const next = alternatives.find(
                (r: Data) => r.pcm.file === e.target.value,
              );
              if (next) switchRun(next);
            }}
          >
            {alternatives.map((r: Data) => (
              <option key={r.pcm.file} value={r.pcm.file}>
                {report.manifest.request.presets[r.preset_index].name}
              </option>
            ))}
          </select>
        </label>
      )}
      {switching && (
        <p role="status">Cargando otra versión del mismo instante…</p>
      )}
      <div className="comparison-media">
        <video
          ref={video}
          muted
          playsInline
          preload="auto"
          src={`${base}/sources/${run.source_index}`}
          onError={() => setError("No se pudo reproducir la fuente congelada.")}
        />
        <canvas
          ref={canvas}
          aria-label="Figura de la corrida"
          style={{ width: "100%", height: 300 }}
        />
      </div>
      <audio
        ref={audio}
        controls={blocks.length > 0 && !switching}
        preload="metadata"
        src={`${base}/artifacts/${run.pcm.file}`}
        onLoadedMetadata={(e) => {
          const a = e.currentTarget;
          if (a.currentSrc.endsWith(`${base}/artifacts/${run.pcm.file}`))
            setMediaReady(run.pcm.file);
        }}
        onError={() => {
          pendingSwitch.current = null;
          setSwitching(false);
          audio.current?.pause();
          video.current?.pause();
          setError("No se pudo reproducir el WAV.");
        }}
      />
      <label>
        Velocidad de reproducción
        <select value={rate} onChange={(e) => setRate(+e.target.value)}>
          {[0.25, 0.5, 1, 1.5, 2].map((n) => (
            <option key={n} value={n}>
              {n}×
            </option>
          ))}
        </select>
      </label>
      <label>
        Ajuste visual del video (s)
        <input
          type="number"
          value={offset}
          min={-2}
          max={2}
          step={0.01}
          onChange={(e) => setOffset(+e.target.value)}
        />
      </label>
      <p>
        El ajuste mueve sólo el video; no modifica las muestras, la figura ni el
        manifest. Velocidades distintas de 1× usan el ajuste temporal del
        navegador con afinación preservada; la figura sigue el reloj del
        archivo, no esa transformación de escucha. Durante la cola el video
        queda en el fin del segmento. Alternar presets conserva posición y
        pausa/reproducción; espera el WAV y sus osciladores antes de reanudar.
        El cambio de archivo puede tener una interrupción audible: no es un
        crossfade ni modifica fases, niveles o artefactos renderizados.
      </p>
      <ComparisonExport report={report} run={run} />
      {!blocks.length && !error && <p>Cargando estado de osciladores…</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
