# Comparador local v1

Segunda iteración, 2026-09-29. Primer corte de #18: comparación descriptiva de
presets congelados × segmentos; no render PCM ni evaluación científica formal.

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
controla Shaper y no copia el video. Puede competir por CPU/disco: no constituye
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
  targets y diagnóstico/ruteo; nunca PCM.
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
publicación formal, render PCM offline, grabación opcional (#17), sensores/3D,
comparación de cymatics físicos y aceptación humana. No son requisitos para jugar.
