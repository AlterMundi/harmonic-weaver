# Comparador local

Segunda iteración, 2026-09-29. Primer corte de #18: comparación descriptiva de
presets congelados × segmentos. Extensión 2026-09-30: render PCM opcional
con el motor compartido de Shaper; evaluación científica formal pendiente.

## Desde la web

En **Comparar**, seleccionar presets guardados y fuentes de la biblioteca con
tracking completo. El algoritmo se muestra junto al nombre: un preset editado
puede conservar un nombre histórico. Configurar inicio/fin y persona. **Agregar
otro segmento de esta fuente** permite comparar varias secciones del mismo video.
Para modelos distintos de baseline, seleccionar explícitamente una calibración
medida de esa fuente/persona. La UI no inventa ni transfiere escalas.

**Comparar presets** congela los valores, la escala/procedencia y el checksum del
manifest de tracking. Corre en un proceso separado, con un único trabajo activo
y un thread por biblioteca numérica. No modifica la configuración en vivo, no
controla la instancia en vivo de Shaper y no copia el video. Puede competir por CPU/disco: no constituye
una garantía de latencia bajo carga. Se puede cancelar; las corridas interrumpidas
se distinguen al reiniciar. Los trabajos terminados vuelven a aparecer.

**Repetir configuración congelada** usa la solicitud original incluso si luego
se editan los presets guardados. Si se modificó el archivo o la generación de
tracking, falla explícitamente: crear una nueva comparación. Las generaciones de
tracking anteriores no se borran, pero esta primera UI no permite elegirlas.
**Ver comparación** presenta el informe y permite descargarlo. Los JSONL completos
quedan en el directorio local indicado. No subirlos automáticamente a GitHub.

Defaults propios del comparador: 60 Hz, 2 s de historia previa, primeros 10 s
como selección inicial editable. No cambian defaults sonoros. Un segmento próximo
al inicio tendrá menos historia disponible: el calentamiento queda registrado.
Cada pareja preset/segmento comienza con estado nuevo y recorre causalmente la
historia previa; la ventana evaluada es [inicio, fin), muestreada sobre ese reloj.

## Artefactos y contrato

`~/.local/share/harmonic-weaver/laboratory/evaluations/<id>/` contiene:

- `request.json`: solicitud congelada; `process.log`: diagnóstico del proceso.
- `result/manifest.json`: estado, hashes de solicitud/código/medios/cache/salidas,
  head y estado Git, versiones Python/NumPy/Pydantic, parámetros y cobertura.
- `result/source-NN-preset-NN.jsonl`: ticks con features, estados/razones,
  targets y diagnóstico/ruteo.
- Con render habilitado: `source-NN-preset-NN.wav` estéreo float después del
  timbre, master y soft limiter; `*.voice-frames.jsonl` contiene el estado de
  osciladores por bloque antes del timbre/limitador, con recorte y reloj lógico.
- `result/comparison-NN.json`: señales del mismo nombre/unidad comparadas sobre
  exactamente los mismos ticks observados por **todos** los presets seleccionados.

Las medias `mean_available` y fracciones de actividad de cada corrida describen
esa corrida, no una comparación justa de eficacia. Para contrastar señales usar
`means_same_support`, junto con `common_count` y el hash del soporte. Held/missing
no se convierten en ceros observados. El informe conserva conteos por estado,
razones y máximo hueco de señal sobre el reloj de control. La cobertura de joints
se pondera por tiempo fuente; no equivale a precisión geométrica ni ausencia de
oclusiones. No mezclar unidades ni interpretar ganancias objetivo como loudness.

Replay ejecuta **LaboratoryRuntime.tick**, los mismos modelos, resets y ruteos del
modo live. El reloj es lógico y determinista; `available_monotonic_s` en esta
salida es disponibilidad lógica, no latencia física medida. No promete igualdad
bit a bit entre plataformas/versiones, ni reproduce jitter de captura/hardware.
La prueba de paridad usa idénticos frames, configuración y tiempos de control.

## CLI

Desde el checkout y entorno de Weaver, con una solicitud exportada/congelada:

```sh
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.evaluation \
  /ruta/local/request.json --output /ruta/local/resultado-nuevo
```

El destino debe ser nuevo. En el worktree de Legion, usar el Python de
`../harmonic-weaver/.venv/bin/python` si no hay `.venv` propio. El JSON acepta
`presets` completos, `sources` con media_path/cache_manifest/person_id/inicio-fin,
`control_hz` y `preroll_s`; consultar los modelos Request/Source del runner para
los nombres exactos (`start_s`, `end_s`, `torso_scale`, `calibration_provenance`).
No quitar `cache_manifest_sha256` de una solicitud congelada para forzar una
repetición: eso cambia la procedencia y debe ser una corrida nueva.

## Investigación y entregas posteriores

Integra las precauciones de Sai recogidas en NEXT_ITERATION: causalidad,
cobertura, separación geometría/tiempo y soporte común. La PR #36 de Oliva fue
revisada y sus ocho pruebas/banco sintético ejecutados contra esta iteración;
no se fusionó ni se introdujo en el runtime. Antes de extender su adaptador a
loops/múltiples épocas debe conservar la clave de época o rechazar duplicados.
Q diagonal no reemplaza un tensor/subespacio; R de fase no es R transversal de
Anni. El banco no valida HIT ni eficacia corporal.

Permanecen en #18/#19 y agenda R01–R13: predicción con targets independientes,
reservas por sesión, controles marginales/no lineales y selección predeclarada,
publicación formal, exportación de video/figura, grabación opcional (#17), sensores/3D,
comparación de cymatics físicos y aceptación humana. No son requisitos para jugar.

## Render PCM opcional

En Comparar, activar **Generar WAV y estado de osciladores**. Configurar frecuencia
(48 kHz inicial), bloque (256 muestras), master de Shaper (0.8, default del motor)
y cola (0 s inicialmente, hasta 2 s). Estos controles no cambian la sesión live.
El master del preset ya está incluido en los targets; el master de Shaper es otra
etapa y debe igualarse explícitamente a la salida real para comparar.

El runner usa el mismo runtime causal y el mismo `AudioEngine.render_block` que
invoca el kernel del callback de Shaper. No abre PortAudio. Cada preset comienza
con motor nuevo; el preroll calienta tanto análisis como fases/envolventes, luego
se recorta el intervalo solicitado con precisión de muestra. Los controles se
consumen en el primer límite de bloque posterior a su timestamp lógico, sin
partir bloques; el manifest declara una cuantización máxima bloque/sample-rate.
La cola libera las voces al final; su comienzo también se cuantiza al bloque.
No reproduce jitter de red/dispositivo ni acredita latencia física.

El render guarda hashes de archivos de síntesis y del WAV/estado de voces,
versiones NumPy/soundfile/libsndfile, configuración, duración en muestras, RMS
lineal y pico post-limitador. No son loudness percibido ni medidas fisiológicas.
La figura representa todos los osciladores y conserva la distinción entre
pre-shape y PCM. El JSONL permite reconstruirla, pero todavía no entrega un video
renderizado de la figura. El reproductor conjunto está descrito abajo.

El timestamp de pared del chunk WAV PEAK se fija en cero: es un render lógico,
no una grabación física. Las muestras y los picos no se alteran. Una repetición
local debe producir hashes idénticos con el mismo motor y bibliotecas; no se
promete igualdad entre plataformas. Si cambió el motor congelado, repetir falla
explícitamente y se debe crear una nueva corrida.

Se requiere un Shaper compatible con `render_block`. El launcher pasa el checkout
seleccionado mediante `SHAPER_DIR`; la CLI acepta esa variable. No sustituye el
motor silenciosamente si falta o si ya se importó otro checkout. Instalar Weaver
con extras `[lab]` incluye soundfile; Shaper sigue siendo un repositorio separado.
En Legion, el desarrollo está en `harmonic-weaver-dev` / `harmonic-shaper-dev`;
la carpeta de prueba `harmonic-weaver-lab` sigue en la entrega anterior hasta
aplicar explícitamente esta revisión.

Ejemplo de render desde desarrollo, sin reiniciar ni tocar la salida R24:

```sh
SHAPER_DIR=../harmonic-shaper-dev PYTHONPATH=src \
  ../harmonic-weaver/.venv/bin/python -m harmonic_weaver.lab.evaluation \
  /ruta/local/request-con-pcm.json --output /ruta/local/resultado-nuevo
```

La solicitud añade `pcm: {"enabled": true, "sample_rate": 48000,
"block_frames": 256, "shaper_master": 0.8, "tail_s": 0}`. La API devuelve el
reporte y permite escuchar/descargar los artefactos declarados en el manifest
sólo cuando la corrida está completa. No publica archivos automáticamente.

## Reproducción conjunta de una corrida

Después de Ver comparación, elegir **Ver video, sonido y figura** en una corrida
con PCM. El WAV es el reloj: el reproductor mueve el video al inicio del segmento
más el tiempo del audio y reconstruye todas las voces a partir de sus bloques
pre-shape. En bloques recortados conserva la posición original dentro del bloque;
interpola gain/phase-offset y avanza fases, sin volver a analizar movimiento.
No recalcula tracking ni cambia presets/ruteos del instrumento en vivo.

Play, pausa y seek usan los controles del WAV. Durante la cola el video permanece
en el último tiempo visual del segmento (fin exacto con ajuste 0). Cerrar o cambiar de corrida detiene su reproductor. La
figura limpia persistencia al hacer seek. El selector de velocidad conserva pitch
mediante el navegador; esa transformación de escucha no es el PCM original ni
una nueva simulación de osciladores. **Ajuste visual del video** desplaza sólo la
imagen; no altera resultados ni el manifest, y no constituye una calibración de
latencia física. Comenzar con 1× y ajuste 0 para comparar el render congelado.

Video/WAV/voice-frames se sirven sólo desde corridas completas, con verificación
de hashes. Un archivo cambiado se rechaza. El checksum se reutiliza para requests
Range sólo mientras identidad/tamaño/mtime/ctime del archivo sigan iguales; evita
releer todo el video en cada seek. No se duplica ni sube la fuente. Navegador y
formatos pueden limitar reproducción (usar MP4 H.264 cuando sea necesario).

Esta coordinación usa relojes de elementos HTML media, no una salida audiovisual
con reloj físico común: la prueba de navegador usa tolerancia de 0.25 s para el
video y verifica pausa/seek/dibujo. El JSONL conserva el reloj exacto de muestras
para análisis. Exportar un video sincronizado de la figura sigue pendiente.

Si WebGL no está disponible, se informa la ausencia de figura y video/audio
siguen coordinados. El reproductor no necesita WebGL para avanzar el video.

## Descargar datos congelados desde la web

Al abrir una comparación terminada, cada corrida ofrece **Features y targets**:
JSONL con reloj/tick, señales/unidades/estados/causas, targets y diagnóstico del
runtime compartido. No requiere habilitar PCM. También se pueden descargar la
configuración congelada, el manifest original y los `comparison-*.json` con
estadísticas sobre soporte común; WAV y estado de osciladores conservan sus
controles existentes.

La API `/api/evaluations/{id}/artifacts/{filename}` sirve únicamente archivos
declarados de una corrida completa. Traces y comparaciones se verifican por los
hashes del manifest; request debe coincidir con su digest y contenido congelado.
Una comparación alterada se rechaza también al abrir el informe, no se muestra
como evidencia intacta. Rechaza nombres fuera del contrato y symlinks de
artefactos. JSON usa `application/json`, traces `application/x-ndjson` y WAV
`audio/wav`; Range/206 permite lectura parcial. Las descargas siguen siendo
locales y pueden contener información corporal/rutas: no se publican solas.

Esto permite inspección e intercambio deliberado de datos para R01/R02/R07;
no implementa todavía la ingestión corporal en esos bancos ni resuelve sus
hipótesis. No altera calibración, presets, fuentes ni síntesis en vivo.

## Identidad del entorno PCM

Las corridas nuevas congelan `pcm.environment_sha256` además de `engine_sha256`.
El entorno declarado incluye Python, plataforma, NumPy, soundfile y libsndfile;
el manifest del renderer conserva esos valores. Un cambio se rechaza antes de
escribir PCM: elegir deliberadamente una comparación nueva con su propia identidad.
No cambia los venvs ni el instrumento. La web muestra el entorno del render.

Los resultados legacy siguen consultables/descargables, pero su request sólo
fijaba código: repetir no puede inventar su entorno original. Web/CLI rechazan
re-render de un pin de código sin pin de entorno. Crear un request nuevo sin
pins heredados es otra comparación, no una reproducción demostrada de la antigua.
No quitar un hash del motor para forzar un resultado incompatible.

Este fingerprint declara dependencias relevantes, no es una attestation completa
de hardware/build/CPU ni prueba universal de identidad numérica. Una igualdad
comprobada sobre fixtures tampoco mide latencia física o escucha humana.

El inventario de comparaciones declara `repeat_supported` y `repeat_reason` para
corridas cuyo entorno original no quedó registrado. La web deshabilita **Repetir
configuración congelada** en esos casos y muestra el motivo antes del intento.
**Ver comparación**, reproducción y descargas permanecen disponibles; no se
ocultan resultados históricos ni se presentan como una falla nueva de audio.

## Integridad al repetir

Repetir verifica el contenido del request guardado contra su identidad canónica
antes de lanzar otro proceso. Las corridas nuevas guardan request-identity.json
antes del worker; resultados con manifest también deben coincidir con su
request_sha256. Un request alterado no puede convertirse silenciosamente en otra
corrida bajo la etiqueta de configuración congelada. La comprobación sobrevive
al reinicio y no depende del preset actual editable.

Resultados antiguos sin sidecar pueden usar el digest del manifest existente.
Sin ninguna identidad confirmada, crear una comparación nueva: calcular hoy un
hash de un archivo desconocido no confirma cuál era el request original. Esto
no es una firma/attestation contra un atacante que reescriba todos los artefactos;
es integridad de contenido/procedencia dentro del almacenamiento local. Los
requisitos de código/entorno del PCM siguen verificándose por separado.

Antes del hash nuevo se validan también los defaults explícitos como hará el
worker, evitando diferencias accidentales int/float (0 frente a 0.0). Para
históricos, el manifest debe verificar su propio digest y tener el mismo
contenido del request; equivalencia numérica int/float no acepta bool/número,
valores distintos, campos agregados ni presets alterados.


## Alternar presets sin volver al comienzo

Abrir Ver video, sonido y figura en una corrida con PCM. Si la comparación incluye
varios presets para ese mismo segmento, el selector **Preset del mismo segmento**
permite cambiarlos manteniendo el instante y si estaba en pausa o reproduciendo.
Carga WAV y estado de osciladores antes de reanudar; el video permanece ligado al
mismo segmento/persona. Las otras fuentes/segmentos no se mezclan en ese selector.
**Pausar comparación** detiene ambos medios y cancela una reanudación pendiente
si se pulsa durante la carga. Cerrar detiene la reproducción.

Esto permite contrastar un gesto específico sin reiniciar cada preset. Conserva
niveles y artefactos originales: no ajusta loudness, no hace crossfade y el cambio
puede tener una interrupción audible. No modifica el instrumento live ni sus
fases. Probar a1×, ajuste visual0 y nivel explícito; velocidades/offsets siguen
siendo controles de escucha, no cambios al experimento congelado.

Validado automáticamente con tres renders del minuto corporal local existente y
medios/API reales; reproducción Chrome muted y posición preservada a15s. Aceptación
auditiva/sincronización física pendientes. Datos/resultados privados permanecen
locales. La prueba reproducible de software es comparisonRealNetwork.spec.ts y
requiere LAB_AB_API_URL, LAB_AB_JOB (corrida completa ≥2 presets del mismo segmento)
y LAB_COMPONENT_TEST_URL con proxy /api hacia esa API aislada; no apunta por
defecto a sesiones compartidas ni inicia hardware.
