import { useState } from "react";
import { predictorLabels } from "./ForecastControls";
type Data = Record<string, any>;
export function R01Comparison({ api, jobs }: { api: any; jobs: Data[] }) {
  const [selected, setSelected] = useState<string[]>([]),
    [support, setSupport] = useState("origin_target");
  const [report, setReport] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const complete = jobs.filter((j) => j.status === "complete");
  if (!complete.length) return null;
  return (
    <section aria-label="Comparación de corridas R01">
      <h3>Comparar corridas R01 guardadas</h3>
      <p>
        Elegí2–6 corridas con las mismas entradas congeladas. La primera elegida
        es referencia. Cada control se compara por separado; sólo se puntúan
        familias presentes en todas las corridas.
      </p>
      {complete.map((j) => (
        <label key={j.id}>
          <input
            type="checkbox"
            aria-label={`Comparar R01 ${j.id}`}
            disabled={
              busy || (!selected.includes(j.id) && selected.length >= 6)
            }
            checked={selected.includes(j.id)}
            onChange={(e) => {
              setSelected(
                e.target.checked
                  ? [...selected, j.id]
                  : selected.filter((id) => id !== j.id),
              );
              setReport(null);
              setError("");
            }}
          />
          Corrida R01 {j.id} · horizonte {j.settings?.horizon_steps} ·
          componentes {j.settings?.components} ·{" "}
          {j.settings?.predictors
            ?.map((p: string) => predictorLabels[p] || p)
            .join(", ")}
        </label>
      ))}
      <label>
        Soporte temporal de comparación R01
        <select
          value={support}
          disabled={busy}
          onChange={(e) => {
            setSupport(e.target.value);
            setReport(null);
            setError("");
          }}
        >
          <option value="origin_target">Mismo origen y objetivo</option>
          <option value="target">Mismo objetivo, orígenes pueden variar</option>
        </select>
      </label>
      <p>
        Con horizontes distintos puede no haber pares origen/objetivo comunes.
        Elegir mismo objetivo permite contrastar sus errores, pero compara
        diferente información pasada; el JSON conserva todos los orígenes.
      </p>
      <button
        disabled={busy || selected.length < 2}
        onClick={async () => {
          setBusy(true);
          setError("");
          setReport(null);
          try {
            setReport(
              await api("research/r01/compare", { run_ids: selected, support }),
            );
          } catch (e) {
            setError(String(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        Comparar soporte común R01
      </button>
      {busy && <p role="status">Comparando artefactos guardados…</p>}
      {error && <p role="alert">{error}</p>}
      {report && (
        <>
          <p>
            Soporte:{" "}
            {report.support_mode === "target"
              ? "mismo objetivo, orígenes pueden variar"
              : "mismo origen y objetivo"}
            . Referencia: {report.run_ids[0]}.
          </p>
          {report.controls.map((control: Data) => (
            <section key={control.control}>
              <h4>
                {control.control} · {control.common_count} objetivos comunes
              </h4>
              {!control.methods.length && (
                <p>No hay familias de predicción compartidas.</p>
              )}
              {!control.common_count && (
                <p>Sin soporte compartido; no hay puntuación.</p>
              )}
              <table aria-label={`Soporte común R01 ${control.control}`}>
                <thead>
                  <tr>
                    <th>Corrida</th>
                    <th>Elegibles</th>
                    <th>Excluidos</th>
                    {control.methods.map((m: string) => (
                      <th key={m}>
                        {predictorLabels[m] || m} MSE / Δ frente a referencia
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {control.conditions.map((c: Data) => (
                    <tr key={c.run_id}>
                      <td>{c.run_id}</td>
                      <td>{c.eligible_count}</td>
                      <td>{c.excluded_from_common}</td>
                      {control.methods.map((m: string) => (
                        <td key={m}>
                          {c.mean_mse[m]?.toPrecision(5) ?? "Sin soporte"} /{" "}
                          {c.mean_delta_mse_vs_first[m]?.toPrecision(5) ??
                            "Sin soporte"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ))}
          <button
            onClick={() => {
              const url = URL.createObjectURL(
                new Blob([JSON.stringify(report, null, 2)], {
                  type: "application/json",
                }),
              );
              const link = document.createElement("a");
              link.href = url;
              link.download = "r01-common-support.json";
              link.click();
              URL.revokeObjectURL(url);
            }}
          >
            Guardar comparación R01
          </button>
          <details>
            <summary>Soporte, orígenes y procedencia R01</summary>
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </details>
          <p>
            Lectura de errores archivados verificados, sin reajuste, síntesis ni
            cambios del instrumento. No demuestra HIT ni generalización
            corporal.
          </p>
        </>
      )}
    </section>
  );
}
