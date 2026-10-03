# Fuentes y cache de tracking

LAB-02. `VideoLibrary` prepara archivos en un hilo de trabajo. El worker de
percepción corre con el Python de HarMoCAP, reutiliza PoseBackend y SlotManager,
y usa PyAV para decodificar secuencialmente con PTS y timebase originales.
Los logs de librerías van por stderr; stdout transporta JSONL de observaciones.

Instalar `av>=12,<17` en ese entorno (en este host se verificó av 16.1.0):

```sh
uv pip install --python "$HARMOCAP_VENV/bin/python" 'av>=12,<17'
```

El worker no requiere instalar Weaver, FastAPI ni Pydantic en el entorno de
inferencia. `--probe` declara hashes de su código, percepción/identidad/captura,
trackers y versiones de paquetes. No descarga pesos implícitamente; se elige un
checkpoint local existente. PerceptionSettings pertenece a la fuente, no al preset.

## Persistencia

La clave incluye hash del video y modelo, configuración que afecta percepción,
identidad y versiones del extractor. Nombre/path y controles musicales no la
modifican. Cache en `<video>.weaver-cache/`; fallback al directorio de datos si
el sidecar no es escribible, con ubicación visible en el estado del job.

Cada generación tiene JSONL propio y checksum. Solo al completarse se publica
el manifest mediante reemplazo atómico. Cancelación, error o fuente modificada
conservan la generación válida anterior. Reprocesar crea una generación nueva;
no elimina la anterior. El índice local permite reutilizarla tras renombrar un
video. Reabrir verifica identidad e integridad; loops y seeks leen el resultado
sin iniciar workers. La primera pasada expone un prefijo completo mientras avanza.

Se conservan tiempo fuente, PTS/timebase, dimensiones reales, observación o
missingness e identidad por slot/generación. Las rotaciones de display de 90°
se aplican antes de percepción. Si falta PTS se declara `index_fps`; no se hace
pasar ese fallback por medición temporal. El filtrado musical ocurre después.

## Cámara y transporte

LiveCamera conserva una única observación y preview reciente en RAM. HarMoCAP
prioriza el cuadro más reciente; se informa cantidad de cuadros saltados y edad
desde captura. No escribe video, JPEG ni tracking live. Cambiar stream produce
otra identidad de fuente. El cierre termina únicamente el proceso propio.

Transport usa un reloj de reproducción independiente de la inferencia. Play,
pausa, seek y cruces de loop tienen epochs explícitos para reiniciar derivadas.
La reproducción no debe sintetizar fuera del prefijo procesado; loop de prefijo
se presenta como una opción distinta del loop completo al integrar la mesa.

## Evidencia

Pruebas: cache hit/reapertura/renombre, fuente/modelo/config/extractor modificados,
reproceso, cancelación, checksum corrupto, fallback sin permiso de sidecar,
intervalos VFR, lectura de loops sin reinferencia y discontinuidades del transporte.

Se ejecutó el worker real HarMoCAP sobre un MP4 VFR sintético: tres cuadros
completos, tiempos 0/.1/.4 s y cache hit al reabrir. La prueba del decoder compara
sus tiempos con ffprobe; el patrón sintético no contiene un cuerpo y no verifica
calidad de pose. Cámara física y escucha se verifican en integración LAB-08.
