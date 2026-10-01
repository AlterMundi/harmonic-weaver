# Auditoría de integración — 2026-09-30

Estado revisado: Weaver `547c81e` (PR #60), Shaper `00893ad` (PR #6).
Workspaces `harmonic-weaver-dev` / `harmonic-shaper-dev`, ambos con venv propio.
GitHub confirma heads publicados; PRs abiertas, sin merges. Laboratorio habitual
`harmonic-weaver-lab` y originales preservados; no se iniciaron sus servicios.

## Evidencia automática acumulada

- Weaver: 143 tests laboratorio + R01, 38.55 s.
  `PYTHONPATH=src:../harmonic-shaper-dev/src .venv/bin/python -m pytest tests/test_lab_*.py tests/research/test_r01_grassmann.py -q`.
- Shaper: 153 tests de su suite completa, 15.91 s.
  `.venv/bin/python -m pytest tests -q` en Shaper-dev.
- Chrome: 7 tests aislados (captura/preview MP4, body/R01, comparación video/WAV/
  figura, export PCM, reloj de samples y seguidor de video), 8.4 s. Vite en 8877,
  medios sintéticos; audio del playback silenciado. Servidor detenido al terminar.
- Builds pertinentes TypeScript/Vite documentados en VALIDATION para cada cambio.

Esto verifica contratos/modelos/cache/recuperación/replay/UI en sus fixtures;
no equivale a escuchar ni medir latencia física o exactitud de tracking. No se
regrabaron cuerpos ni se publicaron medios/traces privados. No prueba todas las
preguntas R01–R13 ni completa software pendiente de captura/bancos/colaboraciones.

## Diferencia de entorno pendiente de resolver en #18

Weaver-dev: Python 3.12.13, NumPy 2.5.1. Shaper-dev: Python 3.13.5, NumPy 2.4.6.
Render offline importa el motor en el proceso Weaver; síntesis live corre en el
proceso Shaper. Comparten código/kernel, pero las pruebas sample-for-sample
existentes comparan rutas dentro de un mismo entorno, no estos dos procesos.

`engine_identity()` fija hashes de cinco módulos del motor. El request congela
`engine_sha256`, pero no un hash obligatorio del entorno. El manifest externo
registra Python/plataforma/NumPy; repetir no rechaza su cambio automáticamente.
Por tanto, no declarar PCM idéntico live/offline entre entornos ni conservación
bit a bit al migrar dependencias a partir de estos checks.

Siguiente entrega concreta: identidad separada de entorno del renderer (Python,
NumPy, soundfile/libsndfile/plataforma relevantes), pin en requests nuevos y
rechazo claro ante discrepancias; tratamiento explícito de requests legacy cuya
identidad no fue congelada. Añadir contrato de repetición y una comparación
hardware-free entre los dos intérpretes con controles idénticos. Si difieren,
registrar diferencia y ofrecer ejecución con entorno compatible deliberado;
no alterar venvs originales/aceptados ni eliminar hashes para forzar éxito.

## Dependencias abiertas

Overlays y prefijos audiovisuales recovered; recovery in-flight con polling;
medición física/cámara/escucha; bancos y controles R02–R13; integración del aporte
Oliva por contrato sin modificar sus directorios reservados. Las notas históricas
en VALIDATION no sustituyen la verificación de estas entregas faltantes.

## Incremento posterior: entorno fijado y fixture entre intérpretes

Requests PCM nuevos fijan environment_sha256; discrepancias y requests legacy
sin entorno se rechazan por API/CLI. La web expone el entorno registrado.
Protocolo audio_environment verifica igualdad exacta de 38400 muestras estéreo
sobre seis voces sintéticas entre los intérpretes auditados, con código coincidente.
El pendiente universal de paridad live/renderer no se cierra con un fixture;
protocolo/identidades permiten ampliar las condiciones sin asumir resultados.


## Captura y recuperación — auditoría posterior a #67

Fecha 2026-09-30. Weaver 339812b, Shaper 00893ad; workspaces dev limpios al
inicio. GitHub #67 OPEN con head 339812b4fd6b62d2e60a1696c46e038042e890b6.
Sin merges ni arranque de dispositivos.

- Weaver: 64 tests de test_lab_capture, camera, journal_recovery, export,
  recovered_input y timeline; 7.12 s.
- Shaper: 15 tests capture/capture_recovery; 1.25 s.
- Advertencias: deprecaciones TestClient/AnyIO; ninguna falla.

La suite integrada incluye writer/cierre, prefijos de journal e imágenes,
reintentos por contrato, persistencia de recuperación y fallos de disco, export
FFmpeg y PCM exacto, camera prefix, API/reinicio/Range y mutación durante render.
No agrega prueba física de R24/cámara, latencia, aceptación ni navegador unido
a servidor por red. El audio aceptado y los defaults no cambian.

Pendientes LAB-09: job polling en Shaper para confirmar operaciones largas sin
rePOST; overlays configurables; recorrido navegador-servidor completo; medición
de sincronía física y límites/cobertura de journal. El export de prefijos ya
existe y no debe reimplementarse. Investigación R02–R13 permanece abierta.
