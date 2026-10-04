import { useEffect, useRef } from "react";
type Data = Record<string, any>;
const joints = [
  "Nariz",
  "Ojo izq.",
  "Ojo der.",
  "Oreja izq.",
  "Oreja der.",
  "Hombro izq.",
  "Hombro der.",
  "Codo izq.",
  "Codo der.",
  "Muñeca izq.",
  "Muñeca der.",
  "Cadera izq.",
  "Cadera der.",
  "Rodilla izq.",
  "Rodilla der.",
  "Tobillo izq.",
  "Tobillo der.",
];
function axisLabel(id: string) {
  const match = /^(\d+)\.([xy])$/.exec(id);
  return match ? `${joints[+match[1]] || match[1]} ${match[2]}` : id;
}
export function CollectiveGeometry({
  features,
  visual,
  algorithm,
}: {
  features?: Data;
  visual: Data;
  algorithm: string;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const view = visual.collective_view || "off",
    geometry = features?.diagnostics?.collective;
  const established = geometry?.state === "observed";
  const support: string[] = geometry?.support || [];
  const limit = visual.collective_max_axes ?? 12;
  const matrix: number[][] = established ? geometry?.[view] || [] : [];
  const rows = Math.min(limit, matrix.length),
    columns = Math.min(view === "basis" ? 34 : limit, matrix[0]?.length || 0);
  useEffect(() => {
    const node = canvas.current;
    if (!node) return;
    const context = node.getContext("2d");
    if (!context) return;
    const cell = 26,
      left = 145,
      top = 145;
    node.width = left + columns * cell + 10;
    node.height = top + rows * cell + 10;
    context.fillStyle = "#111a25";
    context.fillRect(0, 0, node.width, node.height);
    context.font = "11px sans-serif";
    for (let r = 0; r < rows; r++) {
      context.fillStyle = "#e1eef5";
      context.textAlign = "right";
      context.fillText(
        axisLabel(support[r] || String(r)),
        left - 8,
        top + r * cell + 17,
      );
      for (let c = 0; c < columns; c++) {
        const value = matrix[r][c],
          weight = Math.min(1, Math.abs(value));
        const color = value >= 0 ? [66, 216, 255] : [229, 129, 200];
        context.fillStyle = `rgb(${color.map((v, i) => Math.round([23, 39, 56][i] * (1 - weight) + v * weight)).join(",")})`;
        context.fillRect(left + c * cell, top + r * cell, cell - 1, cell - 1);
      }
    }
    for (let c = 0; c < columns; c++) {
      context.save();
      context.translate(left + c * cell + 15, top - 8);
      context.rotate(-Math.PI / 3);
      context.fillStyle = "#e1eef5";
      context.textAlign = "left";
      context.fillText(
        view === "basis" ? `Modo ${c + 1}` : axisLabel(support[c] || String(c)),
        0,
        0,
      );
      context.restore();
    }
  }, [matrix, rows, columns, support, view]);
  if (view === "off") return null;
  return (
    <section aria-label="Geometría colectiva" className="collective-geometry">
      <h2>
        Geometría del movimiento ·{" "}
        {view === "basis" ? "base y modos" : "proyector"}
      </h2>
      {!established ? (
        <p role="status">
          {algorithm === "baseline"
            ? "El baseline no expone este subespacio. Elegí un modelo local, relacional, angular o colectivo y calibrá el cuerpo."
            : geometry?.reason || "Esperando geometría colectiva observada."}
        </p>
      ) : (
        <>
          <p>
            Cuerpo {features?.person_id} · tiempo{" "}
            {features?.source_time_s?.toFixed(3)} s · {support.length} ejes ·
            rango {geometry.rank} · {geometry.components} componentes. Las seis
            voces siguen siendo independientes de estos componentes.
          </p>
          {!!geometry.excluded_support?.length && <p>
            Sin observaciones comunes en esta ventana: {geometry.excluded_support.map(axisLabel).join(", ")}.
            No se rellenan esas articulaciones ni se toman como movimiento cero.
          </p>}
          <canvas
            ref={canvas}
            aria-label={
              view === "basis"
                ? "Matriz de base colectiva"
                : "Matriz del proyector colectivo"
            }
            style={{ maxWidth: "100%", height: "auto" }}
          />
          <p>
            Negativo: violeta · cero: oscuro · positivo: celeste. Valores
            originales, sin normalización por frame. Mostrando {rows} de{" "}
            {support.length} ejes
            {view === "projector" ? ` y ${columns} columnas` : ""}; el cálculo
            conserva todos los ejes.
          </p>
          <p>
            Residuo: {geometry.residual?.toPrecision(4)} · amplitudes (
            {features?.signals?.["collective.mode.1"]?.unit ||
              "unidad del modelo"}
            ):{" "}
            {(geometry.amplitudes || [])
              .map((v: number) => v.toPrecision(4))
              .join(", ")}{" "}
            · ángulos entre ventanas:{" "}
            {geometry.principal_angles_deg
              ?.map((v: number) => v.toFixed(2))
              .join(", ") ?? "Sin ventana anterior comparable"}
            .
          </p>
          <details>
            <summary>Valores de la geometría observada</summary>
            <pre>{JSON.stringify(geometry, null, 2)}</pre>
          </details>
        </>
      )}
      <p>
        Subespacio del vector de velocidades analizado: no posición 3D del
        cuerpo, intención, eficiencia ni prueba HIT. La base depende de su
        orientación; el proyector describe el subespacio. Un bloque de matriz
        mostrado no es un subespacio reestimado.
      </p>
    </section>
  );
}
