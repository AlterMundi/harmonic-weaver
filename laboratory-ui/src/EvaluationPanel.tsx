import { ComparisonPlayer } from "./ComparisonPlayer";
import { useEffect, useState } from "react";
type Data = Record<string, any>;

export function EvaluationPanel({
  assets,
  presets,
  calibrations,
  person,
  api,
  run,
}: Data) {
  const [selected, setSelected] = useState<string[]>([]);
  const [segments, setSegments] = useState<Data>({});
  const [preroll, setPreroll] = useState(2);
  const [hz, setHz] = useState(60);
  const [batchRuns, setBatchRuns] = useState(1024);
  const [pcm, setPCM] = useState<Data>({
    enabled: false,
    sample_rate: 48000,
    block_frames: 256,
    shaper_master: 0.8,
    tail_s: 0,
  });
  const [jobs, setJobs] = useState<Data[]>([]);
  const [report, setReport] = useState<Data | null>(null);
  const [playRun, setPlayRun] = useState<Data | null>(null);
  useEffect(() => {
    let live = true;
    const poll = () =>
      api("evaluations")
        .then((x: Data[]) => {
          if (live) setJobs(x);
        })
        .catch(() => {});
    void poll();
    const timer = setInterval(poll, 1500);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [api]);
  const edit = (id: string, key: string, value: any) =>
    setSegments((s) => ({ ...s, [id]: { ...s[id], [key]: value } }));
  const download = () => {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "weaver-comparison.json";
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <>
      <h2>Comparación reproducible</h2>
      <p>
        Corre aparte de la sesión en vivo. Usa presets guardados y tracking
        completo; puede renderizar audio aparte sin cambiar lo que está sonando.
      </p>
      <fieldset>
        <legend>Presets guardados</legend>
        {presets.map((p: Data) => (
          <label key={p.id}>
            <input
              type="checkbox"
              checked={selected.includes(p.id)}
              onChange={(e) =>
                setSelected((s) =>
                  e.target.checked ? [...s, p.id] : s.filter((i) => i !== p.id),
                )
              }
            />
            {p.name} · {p.algorithm.id}
          </label>
        ))}
      </fieldset>
      <fieldset>
        <legend>Fuentes y segmentos</legend>
        {assets
          .flatMap((asset: Data) => [
            asset,
            ...Object.keys(segments)
              .filter((id) => id.startsWith(asset.id + ":"))
              .map((id) => ({
                ...asset,
                id,
                asset_id: asset.id,
                name: asset.name + " · otro segmento",
              })),
          ])
          .map((a: Data) => (
            <div key={a.id}>
              <label>
                <input
                  type="checkbox"
                  checked={!!segments[a.id]}
                  onChange={(e) =>
                    setSegments((s) => {
                      const next = { ...s };
                      if (e.target.checked)
                        next[a.id] = {
                          asset_id: a.asset_id || a.id,
                          person_id: a.person_ids?.[0] || person || "",
                          start_s: 0,
                          end_s: Math.min(10, a.duration_s),
                          calibration_id: null,
                        };
                      else delete next[a.id];
                      return next;
                    })
                  }
                />
                {a.name}
              </label>
              {segments[a.id] && (
                <div className="fields">
                  <button
                    onClick={() =>
                      setSegments((s) => ({
                        ...s,
                        [(a.asset_id || a.id) + ":" + crypto.randomUUID()]: {
                          ...s[a.id],
                        },
                      }))
                    }
                  >
                    Agregar otro segmento de esta fuente
                  </button>
                  <label>
                    Persona de {a.name}
                    <input
                      value={segments[a.id].person_id}
                      onChange={(e) => edit(a.id, "person_id", e.target.value)}
                    />
                  </label>
                  <label>
                    Inicio (s)
                    <input
                      type="number"
                      min="0"
                      max={a.duration_s}
                      step=".01"
                      value={segments[a.id].start_s}
                      onChange={(e) => edit(a.id, "start_s", +e.target.value)}
                    />
                  </label>
                  <label>
                    Fin (s)
                    <input
                      type="number"
                      min="0"
                      max={a.duration_s}
                      step=".01"
                      value={segments[a.id].end_s}
                      onChange={(e) => edit(a.id, "end_s", +e.target.value)}
                    />
                  </label>
                  <label>
                    Calibración de esta fuente
                    <select
                      value={segments[a.id].calibration_id || ""}
                      onChange={(e) =>
                        edit(a.id, "calibration_id", e.target.value || null)
                      }
                    >
                      <option value="">Sin escala (sólo baseline)</option>
                      {calibrations
                        .filter(
                          (c: Data) =>
                            c.source_id === (a.asset_id || a.id) &&
                            c.person_id === segments[a.id].person_id,
                        )
                        .map((c: Data) => (
                          <option value={c.id} key={c.id}>
                            {c.torso_scale.toFixed(4)} · {c.measured_at}
                          </option>
                        ))}
                    </select>
                  </label>
                </div>
              )}
            </div>
          ))}
      </fieldset>
      <div className="fields">
        <label>
          Historia previa (s)
          <input
            type="number"
            min="0"
            max="30"
            step=".1"
            value={preroll}
            onChange={(e) => setPreroll(+e.target.value)}
          />
        </label>
        <label>
          Reloj de control (Hz)
          <input
            type="number"
            min="10"
            max="240"
            step="1"
            value={hz}
            onChange={(e) => setHz(+e.target.value)}
          />
        </label>
      </div>
      <label>Máximo de corridas por tanda
        <input type="number" min={1} max={1024} step={1} value={batchRuns} onChange={e=>setBatchRuns(+e.target.value)}/>
      </label>
      <p>Una corrida es un preset × segmento. Al alcanzar el límite, continuar conserva las corridas terminadas y calcula las restantes con reset e historia previa; no recupera un estado a mitad de corrida.</p>
      <fieldset>
        <legend>Render de audio opcional</legend>
        <label>
          <input
            type="checkbox"
            checked={pcm.enabled}
            onChange={(e) => setPCM({ ...pcm, enabled: e.target.checked })}
          />
          Generar WAV y estado de osciladores
        </label>
        {pcm.enabled && (
          <div className="fields">
            {[
              ["sample_rate", "Frecuencia de muestreo (Hz)", 8000, 192000, 1],
              ["block_frames", "Muestras por bloque", 16, 4096, 1],
              ["shaper_master", "Master de Shaper para el render", 0, 1, 0.01],
              ["tail_s", "Cola después del segmento (s)", 0, 2, 0.01],
            ].map(([key, label, min, max, step]) => (
              <label key={key}>
                {label}
                <input
                  type="number"
                  value={pcm[key]}
                  min={min}
                  max={max}
                  step={step}
                  onChange={(e) => setPCM({ ...pcm, [key]: +e.target.value })}
                />
              </label>
            ))}
          </div>
        )}
        <p>
          WAV estéreo float después del timbre, master y limitador. La figura
          usa los osciladores antes del timbre y limitador. Bloques y master son
          independientes de la salida física: igualalos para comparar.
        </p>
      </fieldset>
      <button
        disabled={
          !selected.length ||
          !Object.keys(segments).length ||
          jobs.some((j) => j.status === "running")
        }
        onClick={() =>
          run(async () => {
            await api("evaluations", {
              preset_ids: selected,
              segments: Object.values(segments),
              preroll_s: preroll,
              control_hz: hz,
              max_runs_per_invocation: batchRuns,
              pcm,
            });
            setJobs(await api("evaluations"));
          })
        }
      >
        Comparar presets
      </button>
      {jobs.map((j) => (
        <div key={j.id}>
          <p>
            {j.status} · {j.completed_runs || 0}/{j.total_runs || "?"} corridas
            · {j.error}
          </p>
          {j.status === "running" && (
            <button
              onClick={() => run(() => api(`evaluations/${j.id}/cancel`, {}))}
            >
              Cancelar comparación
            </button>
          )}
          {j.resume_supported && <button disabled={jobs.some(job=>job.status==='running')} onClick={()=>run(async()=>{await api(`evaluations/${j.id}/resume`,{max_runs:batchRuns});setJobs(await api('evaluations'))})}>Continuar comparación congelada</button>}
          {j.status === "complete" && (
            <button
              onClick={() =>
                run(async () => {
                  setPlayRun(null);
                  setReport(await api(`evaluations/${j.id}/report`));
                })
              }
            >
              Ver comparación
            </button>
          )}
          {j.status !== "running" && (
            <button
              disabled={j.repeat_supported===false || jobs.some((job) => job.status === "running")}
              onClick={() =>
                run(async () => {
                  await api(`evaluations/${j.id}/repeat`, {});
                  setJobs(await api("evaluations"));
                })
              }
            >
              Repetir configuración congelada
            </button>
          )}
          {j.repeat_reason && <p>{j.repeat_reason}</p>}
          <small>Resultados locales: {j.directory}</small>
        </div>
      ))}
      {report && (
        <>
          <p>
            Features y targets antes de Shaper; WAV opcional después de
            síntesis. No son medidas de volumen percibido ni eficacia corporal.
          </p>
          {playRun && (
            <ComparisonPlayer
              key={report.job_id + ":" + playRun.file}
              report={report}
              run={playRun}
              onClose={() => setPlayRun(null)}
            />
          )}
          <table>
            <thead>
              <tr>
                <th>Fuente</th>
                <th>Preset</th>
                <th>Ticks</th>
                <th>Datos del análisis</th>
                <th>Con sonido previsto</th>
                <th>Render local</th>
              </tr>
            </thead>
            <tbody>
              {report.manifest.runs.map((r: Data, i: number) => (
                <tr key={i}>
                  <td>{r.source_index + 1}</td>
                  <td>{r.preset_id}</td>
                  <td>{r.rows}</td>
                  <td><a href={`/api/evaluations/${report.job_id}/artifacts/${r.file}`} download>Features y targets</a></td>
                  <td>{(r.sounding_fraction * 100).toFixed(1)}%</td>
                  <td>
                    {r.pcm ? (
                      <>
                        <button onClick={() => setPlayRun(r)}>
                          Ver video, sonido y figura
                        </button>
                        <audio
                          controls
                          preload="none"
                          src={`/api/evaluations/${report.job_id}/artifacts/${r.pcm.file}`}
                        />
                        <a
                          href={`/api/evaluations/${report.job_id}/artifacts/${r.pcm.file}`}
                          download
                        >
                          WAV
                        </a>
                        {" · "}
                        <a
                          href={`/api/evaluations/${report.job_id}/artifacts/${r.pcm.voice_frames}`}
                          download
                        >
                          Osciladores
                        </a>
                        <small>
                          RMS {r.pcm.rms.toFixed(4)} · pico{" "}
                          {r.pcm.peak.toFixed(4)} · {r.pcm.samples} muestras
                        </small>
                      </>
                    ) : (
                      "Sin render"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={download}>Descargar informe y manifest</button>
          {report.manifest.runs.some((r:Data)=>r.pcm) && <details>
            <summary>Entorno del render PCM</summary>
            <p>Las corridas nuevas fijan código y entorno. Un render legacy sin identidad de entorno no se repite como si su entorno original fuera conocido; crear una comparación nueva.</p>
            <pre>{JSON.stringify(report.manifest.runs.find((r:Data)=>r.pcm)?.pcm?.engine?.environment || {estado:'Entorno no registrado'},null,2)}</pre>
          </details>}
          <p>
            <a href={`/api/evaluations/${report.job_id}/artifacts/request.json`} download>Configuración congelada</a>
            {' · '}<a href={`/api/evaluations/${report.job_id}/artifacts/manifest.json`} download>Manifest original</a>
            {Object.keys(report.manifest.comparison_hashes || {}).map(name=><span key={name}>{' · '}<a href={`/api/evaluations/${report.job_id}/artifacts/${name}`} download>{name}</a></span>)}
          </p>
          <p>
            Contiene rutas y resultados locales: revisar antes de compartir.
          </p>
          <details>
            <summary>Señales sobre soporte común</summary>
            <pre>{JSON.stringify(report.comparisons, null, 2)}</pre>
          </details>
        </>
      )}
    </>
  );
}
