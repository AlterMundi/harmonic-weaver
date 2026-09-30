import { useEffect, useRef, useState } from "react";
import { Figure } from "./figure";
import { voicesAt, sourcePosition, type Block } from "./replayClock";
type Data = Record<string, any>;

export function ComparisonPlayer({
  report,
  run,
  onClose,
}: {
  report: Data;
  run: Data;
  onClose: () => void;
}) {
  const audio = useRef<HTMLAudioElement>(null),
    video = useRef<HTMLVideoElement>(null),
    canvas = useRef<HTMLCanvasElement>(null);
  const [blocks, setBlocks] = useState<Block[]>([]),
    [error, setError] = useState("");
  const [rate, setRate] = useState(1),
    [offset, setOffset] = useState(0);
  const source = report.manifest.request.sources[run.source_index];
  const preset = report.manifest.request.presets[run.preset_index];
  const base = `/api/evaluations/${report.job_id}`;
  useEffect(() => {
    const abort = new AbortController();
    setBlocks([]);
    setError("");
    fetch(`${base}/artifacts/${run.pcm.voice_frames}`, { signal: abort.signal })
      .then((r) => {
        if (!r.ok) throw Error(`Osciladores: HTTP ${r.status}`);
        return r.text();
      })
      .then((text) =>
        setBlocks(
          text
            .trim()
            .split("\n")
            .filter(Boolean)
            .map((line) => JSON.parse(line)),
        ),
      )
      .catch((e) => {
        if (e.name !== "AbortError") setError(String(e));
      });
    return () => abort.abort();
  }, [base, run.pcm.voice_frames]);
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
      <p>
        Fuente {run.source_index + 1} · Persona {source.person_id} ·{" "}
        {preset.name}. Reloj: WAV; figura de todos los osciladores antes del
        timbre/limitador.
      </p>
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
        controls={blocks.length > 0}
        preload="metadata"
        src={`${base}/artifacts/${run.pcm.file}`}
        onError={() => setError("No se pudo reproducir el WAV.")}
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
        queda en el fin del segmento.
      </p>
      {!blocks.length && !error && <p>Cargando estado de osciladores…</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
