import { useEffect, useState, useRef } from "react";
type Data = Record<string, any>;
export function EvaluationPackages({ report, api, run }: Data) {
  const [indices, setIndices] = useState<number[]>([]),
    [requests, setRequests] = useState(false),
    [traces, setTraces] = useState(false),
    [pcm, setPCM] = useState(false),
    [maxMB, setMaxMB] = useState(64),
    [preview, setPreview] = useState<Data | null>(null),
    [jobs, setJobs] = useState<Data[]>([]);
  useEffect(() => {
    let live = true;
    const poll = () =>
      api("evaluation-packages")
        .then((value: Data[]) => {
          if (live) setJobs(value);
        })
        .catch(() => {});
    void poll();
    const id = setInterval(poll, 1500);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, [api]);
  const generation = useRef(0);
  const invalidate = () => {
    generation.current++;
    setPreview(null);
  };
  const selection = {
    run_indices: indices,
    include_requests: requests,
    include_traces: traces,
    include_pcm: pcm,
    max_mb: maxMB,
  };
  const active = jobs.some((j) => ["queued", "running"].includes(j.status));
  return (
    <section aria-label="Paquete seleccionable de comparación">
      <h3>Preparar paquete local para revisar</h3>
      <p>
        El resumen omite nombres, rutas, identidades y escala corporal. Los
        resultados derivados pueden seguir siendo sensibles. No incluye video ni
        tracking y no publica nada automáticamente.
      </p>
      <fieldset>
        <legend>Corridas que incluir</legend>
        {report.manifest.runs.map((r: Data, i: number) => (
          <label key={i}>
            <input
              type="checkbox"
              checked={indices.includes(i)}
              onChange={(e) => {
                setIndices((old) =>
                  e.target.checked ? [...old, i] : old.filter((n) => n !== i),
                );
                invalidate();
              }}
            />
            Corrida {i + 1} · fuente {r.source_index + 1} · preset{" "}
            {r.preset_index + 1}
          </label>
        ))}
      </fieldset>
      <label>
        <input
          type="checkbox"
          checked={requests}
          onChange={(e) => {
            setRequests(e.target.checked);
            invalidate();
          }}
        />
        Incluir pedidos de reproducción (rutas, persona y escala privadas)
      </label>
      <label>
        <input
          type="checkbox"
          checked={traces}
          onChange={(e) => {
            setTraces(e.target.checked);
            invalidate();
          }}
        />
        Incluir features y targets (datos corporales)
      </label>
      <label>
        <input
          type="checkbox"
          checked={pcm}
          onChange={(e) => {
            setPCM(e.target.checked);
            invalidate();
          }}
        />
        Incluir WAV y estados de osciladores disponibles
      </label>
      <label>
        Máximo de datos del paquete (MiB)
        <input
          type="number"
          min={1}
          max={4096}
          value={maxMB}
          onChange={(e) => {
            setMaxMB(+e.target.value);
            invalidate();
          }}
        />
      </label>
      <button
        disabled={!indices.length}
        onClick={() =>
          run(async () => {
            const version = generation.current;
            const value = await api(
              `evaluations/${report.job_id}/package-preview`,
              selection,
            );
            if (version === generation.current) setPreview(value);
          })
        }
      >
        Ver contenido del paquete
      </button>
      <button
        onClick={() => {
          const preferences = {
            include_requests: requests,
            include_traces: traces,
            include_pcm: pcm,
            max_mb: maxMB,
          };
          const url = URL.createObjectURL(
            new Blob([JSON.stringify(preferences, null, 2)], {
              type: "application/json",
            }),
          );
          const a = document.createElement("a");
          a.href = url;
          a.download = "evaluation-package-preferences.json";
          a.click();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        }}
      >
        Descargar preferencias del paquete
      </button>
      <label>
        Importar preferencias del paquete
        <input
          type="file"
          accept="application/json,.json"
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (file)
              run(async () => {
                if (file.size > 65536)
                  throw Error("Preferencias demasiado grandes");
                const value = JSON.parse(await file.text());
                if (
                  !value ||
                  typeof value !== "object" ||
                  Object.keys(value).sort().join(",") !==
                    "include_pcm,include_requests,include_traces,max_mb" ||
                  ["include_requests", "include_traces", "include_pcm"].some(
                    (k) => typeof value[k] !== "boolean",
                  ) ||
                  !Number.isInteger(value.max_mb) ||
                  value.max_mb < 1 ||
                  value.max_mb > 4096
                )
                  throw Error("Preferencias de paquete inválidas");
                setRequests(value.include_requests);
                setTraces(value.include_traces);
                setPCM(value.include_pcm);
                setMaxMB(value.max_mb);
                setIndices([]);
                invalidate();
              });
          }}
        />
      </label>
      {preview && (
        <>
          <p>
            {preview.payload_bytes} bytes de datos antes del contenedor.{" "}
            {preview.private_context
              ? "Incluye contexto, traces o PCM privados."
              : "Sólo resumen sin nombres ni rutas."}{" "}
            El soporte común conserva la matriz completa original.
          </p>
          <pre>{JSON.stringify(preview.files, null, 2)}</pre>
          <button
            disabled={active}
            onClick={() =>
              run(async () => {
                await api(`evaluations/${report.job_id}/packages`, {
                  selection,
                  preview_sha256: preview.preview_sha256,
                });
                setJobs(await api("evaluation-packages"));
              })
            }
          >
            Generar paquete local
          </button>
        </>
      )}
      {jobs.map((j) => (
        <div key={j.id}>
          {j.status} · {j.file_count || 0} archivos ·{" "}
          {j.error_type || j.error || ""}
          {["queued", "running"].includes(j.status) && (
            <button
              onClick={() =>
                run(async () => {
                  await api(`evaluation-packages/${j.id}/cancel`, {});
                  setJobs(await api("evaluation-packages"));
                })
              }
            >
              Cancelar paquete
            </button>
          )}
          {j.status === "complete" && (
            <a
              href={`/api/evaluation-packages/${j.id}/artifacts/package.zip`}
              download
            >
              Descargar paquete ZIP
            </a>
          )}
        </div>
      ))}
    </section>
  );
}
