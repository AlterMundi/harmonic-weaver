# Tiempo explícito en CSV de sensores

R11/R12 comparten un lector UTF-8. No detecta el formato de un dispositivo ni
asume zona horaria, escala, identidad o sincronía. Conserva original y mapeo en
archivos locales. El reloj del protocolo se aplica **después** de la conversión
que describe este documento; amplitudes no se convierten.

El mapeo numérico existente sigue usando `time_units` seconds, milliseconds o
microseconds, sin `schema_version` ni origen adicional. También admite tiempo
absoluto numérico; el offset/rate del Clock debe declararse para la ventana común.
No genera timestamps a partir de índices ni corrige reinicios de contadores.

Para fechas con hora, elegir **ISO 8601 con zona horaria** en Formato temporal CSV
R11/R12 y completar Origen ISO. Equivalente JSON del mapeo:

```json
{
  "schema_version": 2,
  "delimiter": ",",
  "index_column": "index",
  "time_column": "timestamp",
  "time_units": "iso8601",
  "time_origin": "2026-10-03T12:00:00Z",
  "channel_columns": {"hr": "pulse"},
  "missing_tokens": [""],
  "missing_cause": "declared_csv_missing"
}
```

Es un ejemplo de formato, no una medición. Cada timestamp y origen debe tener
forma YYYY-MM-DDTHH:MM:SS, con fracción opcional de 1–6 cifras y Z u offset ±HH:MM.
Rechaza zona ausente, fechas inválidas, leap seconds, más de seis cifras decimales
y muestras anteriores al origen. No redondea silenciosamente nanosegundos ni
interpreta zona local. Timestamps equivalentes con distintos offsets producen
el mismo tiempo relativo. Índices/tiempos relativos deben seguir aumentando;
gaps y faltantes conservan sus causas.

Orden: `(timestamp ISO - origen ISO)` → segundos relativos de la fuente →
`Clock.offset_s + Clock.rate * segundos_relativos` → reloj común. Por ejemplo,
12:00:01Z y 09:00:01-03:00 son ambos 1 s después de 12:00:00Z. Si Clock.offset_s
ya restaba una época absoluta, revisarlo explícitamente al elegir ISO para no
restar dos veces. No se modifica Clock automáticamente. Tarea/trials siguen en
el reloj común; unidades de valores y calibración permanecen declaradas.

Exportar/importar un **mapeo portable** conserva el método y limpia `time_origin`;
elegirlo para cada archivo. No transfiere cuerpo/reloj/calibración. Abrir un import
local archivado conserva su CSV, origen, mapeo y metadatos completos para recuperarlo
como la misma entrada, no como preset de otra fuente. Original UTF-8/BOM/CRLF se
mantiene byte por byte; `request.json`/`result.json`/`manifest.json` documentan la
conversión y verifican integridad. Integridad no acredita adquisición, calidad,
calibración, identidad ni sincronía física. Sensores/exports reales pendientes.

## CSV sin contador de muestras

En Índice CSV R11/R12 elegir **Numerar filas desde cero** explícitamente.
El default continúa Columna del archivo; ahora su nombre puede editarse sin
cambiar JSON. Al volver a ese modo propone `index`: declarar el nombre real.
No autodetecta ausencia de índice ni sustituye un contador inválido por filas.

Mapeo de filas usa `schema_version: 3`, `index_mode: "row_ordinal"` e
`index_column: null` (también puede omitirse). El resto conserva los campos
anteriores. Admite seconds/milliseconds/microseconds o iso8601; ISO sigue
requiriendo time_origin con zona, numérico no admite un origen ISO. Por ejemplo:

```json
{
  "schema_version": 3,
  "index_mode": "row_ordinal",
  "index_column": null,
  "time_column": "time_s",
  "time_units": "seconds",
  "channel_columns": {"hr": "pulse"}
}
```

Los índices 0,1,2... cuentan registros CSV después del header/preámbulo declarado,
no líneas físicas (un campo entre comillas puede contener saltos de línea).
Rechaza registros malformados. No genera timestamps, interpola faltantes ni
rellena gaps. `import_provenance.index_generation` conserva método, inicio/paso
y `device_counter_observed: false`. **Cero saltos de índice generados no demuestra
que el dispositivo no perdió muestras**; sólo puede analizarse soporte temporal
y faltantes declarados disponibles. Conservar contador físico en columna cuando
exista. Nominal rate y Clock permanecen metadatos explícitos, no se estiman.

Original/mapa/procedencia quedan en archivo local. Preset portable conserva modo
y versión, limpia origen ISO igual que antes; volver a declarar origen por fuente.
Los mapeos numéricos antiguos e ISO v2 no cambian. No adquisición de hardware.
