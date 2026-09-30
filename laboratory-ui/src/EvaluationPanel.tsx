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
  const [jobs, setJobs] = useState<Data[]>([]);
  const [report, setReport] = useState<Data | null>(null);
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
        completo; no genera audio ni cambia lo que está sonando.
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
          {j.status === "complete" && (
            <button
              onClick={() =>
                run(async () =>
                  setReport(await api(`evaluations/${j.id}/report`)),
                )
              }
            >
              Ver comparación
            </button>
          )}
          {j.status !== "running" && (
            <button
              disabled={jobs.some((job) => job.status === "running")}
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
          <small>Resultados locales: {j.directory}</small>
        </div>
      ))}
      {report && (
        <>
          <p>
            Etapa: targets antes de Shaper. No son medidas de volumen percibido
            ni eficacia corporal.
          </p>
          <table>
            <thead>
              <tr>
                <th>Fuente</th>
                <th>Preset</th>
                <th>Ticks</th>
                <th>Con sonido previsto</th>
              </tr>
            </thead>
            <tbody>
              {report.manifest.runs.map((r: Data, i: number) => (
                <tr key={i}>
                  <td>{r.source_index + 1}</td>
                  <td>{r.preset_id}</td>
                  <td>{r.rows}</td>
                  <td>{(r.sounding_fraction * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={download}>Descargar informe y manifest</button>
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
