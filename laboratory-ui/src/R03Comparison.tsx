import { useState } from "react";
type Data = Record<string, any>;
export function R03Comparison({ api, jobs }: { api: any; jobs: Data[] }) {
  const [selected, setSelected] = useState<string[]>([]),
    [report, setReport] = useState<Data | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const complete = jobs.filter((j) => j.status === "complete");
  if (!complete.length) return null;
  return (
    <section aria-label="Comparación de candidatos R03">
      <h3>Comparar señales o centros R03</h3>
      <p>
        Elegí2–6 corridas contra el mismo corte de marcas, cuerpo, generación y
        parámetros de coincidencia. La comparación restringe todas al soporte
        observado común; conserva los resultados disponibles originales.
      </p>
      {complete.map((j) => (
        <label key={j.id}>
          <input
            type="checkbox"
            aria-label={`Comparar R03 ${j.id}`}
            checked={selected.includes(j.id)}
            disabled={
              busy || (!selected.includes(j.id) && selected.length >= 6)
            }
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
          {j.candidate_summary?.signal_id || "Señal archivada"} · {j.id}
          {j.candidate_summary &&
            ` · ${j.candidate_summary.start_s}–${j.candidate_summary.end_s} s · ${j.candidate_summary.events} candidatos`}
        </label>
      ))}
      <button
        disabled={busy || selected.length < 2}
        onClick={async () => {
          setBusy(true);
          setError("");
          setReport(null);
          try {
            setReport(await api("research/r03/compare", { run_ids: selected }));
          } catch (e) {
            setError(String(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        Comparar soporte común R03
      </button>
      {busy && <p role="status">Comparando candidatos guardados…</p>}
      {error && <p role="alert">{error}</p>}
      {report && (
        <>
          <p>
            Soporte común R03: {report.support_duration_s.toPrecision(5)} s.
            Tolerancia: {report.matching.tolerance_s} s · offset de marcas:{" "}
            {report.matching.mark_offset_s} s.
          </p>
          {!report.support_duration_s && (
            <p>Sin soporte compartido; no hay puntuación.</p>
          )}
          <table aria-label="Candidatos R03 sobre soporte común">
            <thead>
              <tr>
                <th>Señal / corrida</th>
                <th>Unidad / umbrales bajo–alto</th>
                <th>Soporte disponible (s)</th>
                <th>Marcas / candidatos comunes</th>
                <th>Coincidencias</th>
                <th>Precisión</th>
                <th>Recall</th>
                <th>Marcas / candidatos excluidos</th>
              </tr>
            </thead>
            <tbody>
              {report.conditions.map((c: Data) => (
                <tr key={c.run_id}>
                  <td>
                    {c.candidate_request.signal_id} · {c.run_id}
                  </td>
                  <td>
                    {c.unit ?? "Unidad no archivada"} ·{" "}
                    {c.candidate_request.low}–{c.candidate_request.high}
                  </td>
                  <td>{c.available.support_duration_s.toPrecision(5)}</td>
                  <td>
                    {c.paired.eligible_marks} / {c.paired.eligible_candidates}
                  </td>
                  <td>{c.paired.matches.length}</td>
                  <td>{c.paired.precision ?? "Sin denominador"}</td>
                  <td>{c.paired.recall ?? "Sin denominador"}</td>
                  <td>
                    {c.paired.excluded_marks} / {c.paired.excluded_candidates}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            onClick={() => {
              const url = URL.createObjectURL(
                new Blob([JSON.stringify(report, null, 2)], {
                  type: "application/json",
                }),
              );
              const link = document.createElement("a");
              link.href = url;
              link.download = "r03-common-support.json";
              link.click();
              URL.revokeObjectURL(url);
            }}
          >
            Guardar comparación R03
          </button>
          <details>
            <summary>Intervalos, candidatos y procedencia R03</summary>
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </details>
          <p>
            Umbrales conservan la unidad de cada señal; comparar eventos no
            normaliza magnitudes. No selecciona un centro causal ni demuestra
            intención o HIT. No recalcula tracking ni cambia el instrumento.
          </p>
        </>
      )}
    </section>
  );
}
