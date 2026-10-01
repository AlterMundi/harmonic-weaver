# R08 · Cuerda en plano de imagen

Primer contrato manual `rope_annotations.Annotation`: hash de medio, dimensiones,
frame index y timestamp de fuente explícitos. Estados observed/partial/
unidentifiable/absent y causas blur/occlusion/crossing_ambiguity/out_of_frame.
Segmentos visibles independientes; no se unen detrás de una oclusión. Métrica
inicial: longitud proyectada visible en píxeles, usando dimensiones reales de
imagen, sin confundir coordenadas normalizadas con escala isotrópica.

Dos pruebas pasan: segmentos separados y dato ausente, rechazo de observación
inventada, bool como índice y clocks repetidos. Datos exclusivamente sintéticos.
No hay nueva anotación humana, identidad inferida, tracker de cuerda ni 3D.

Próximos entregables necesarios:

- Binding verificable al medio local y selección de segmentos/frame clocks.
- Persistencia/versiones/edición web de curvas, quality causes y presets de
  herramientas; videos y anotaciones corporales siempre locales.
- Asistencia configurable de segmentación y propuesta de curvas, conservando
  qué es manual, propuesto y confirmado; ninguna interpolación invisible.
- Benchmark de blur/oclusiones/cruces y validación humana de clips difíciles.
- Trayectorias/extremos y propagación mano–cuerda sólo sobre soporte observable,
  con gaps, clocks/unidades y controles explícitos.
- R09: ambigüedad de cruces 2D no resuelve profundidad/nudos. Cámaras multivista
  calibradas/sincronizadas o sensores se eligen con evidencia del benchmark.

Referencia de alcance: issue #23 y research/laboratory/AGENDA.md. Rama apilada
sobre R07 PR #74; no merge automático. Las preguntas científicas siguen abiertas.

Segundo corte: `rope_media.probe/bind` usa ffprobe sobre video local regular,
hash antes/después, dimensiones y PTS de cada frame decodificado (no reloj
inventado desde FPS). Tiempo cero es el primer PTS, conservando su origen.
Binding exige mismo hash/dimensiones e índice/timestamp (tolerancia 1 µs).
Fuentes rotadas, píxel no cuadrado y dimensiones variables requieren adaptador
explícito y se rechazan por ahora. Clips de 1–14400 frames; timeout60s y límite
de JSON16MB tras probe (no garantiza límite de memoria del subprocess).
Tres pruebas conjuntas pasan con MP4 sintético real generado por FFmpeg,
incluyendo identidad/dimensiones/reloj/índice/symlink inválidos. No se procesó
video privado ni se anotó cuerda humana. Persistencia y UI continúan pendientes.

Tercer corte: `rope_run.run/verify` guarda revisiones en carpetas nuevas,
annotation/media-clock/result/manifest con hashes y lineage opcional al manifest
padre. Revalida medio antes de complete; no copia video ni guarda rutas/persona.
Verifica report recalculado y frames contra reloj congelado, rehash final.
Parent debe ser revisión verificable del mismo medio al crear hija; conservar
su hash no equivale a resolver toda la cadena después. Cuatro pruebas pasan,
incluyendo padre intacto, no overwrite y report alterado con checksum reescrito.
Estado actual del video requiere rebind explícito; UI/API y asistencia pendientes.

Cuarto corte: RopeService guarda sólo carpetas de revisión nuevas con IDs
UUID, inventario verificable restaurable, descarga whitelist y rebind explícito
al medio vigente. Resolución de source queda a cargo de biblioteca/API posterior;
no se guarda ruta privada en artifacts. Prueba con MP4 sintético real pasa:
dos revisiones/lineage/restauración/rebind, IDs/rutas inválidos, report alterado
y medio modificado rechazados. UI/API y anotaciones humanas aún pendientes.
