# Dos o tres cámaras en vivo: plan de exploración 3D

2026-10-06. Nicolás pide planear esta etapa, sin implementar todavía ni instalar
sensores. Continuación de R09/#23 y del programa #7; sensores y VR quedan en #153.
La instalación cotidiana, sesión, presets y salida R24 permanecen como están.

Hardware declarado por Nicolás durante esta planificación: **tres Logitech C920**;
falta encontrar el hub. El primer ensayo se prepara para esas webcams USB, sin
necesidad de teléfonos, HDMI, visor ni sensores. La consulta de dispositivos del
host realizada ahora enumera cámara integrada y OBS virtual, sin C920 presente:
formatos, perfiles y conexión de las tres todavía no se comprobaron físicamente.

## Resultado buscado

Ver y escuchar un cuerpo reconstruido desde dos o tres vistas simultáneas.
Explorar orientación de caderas/hombros, giro relativo del tronco, flexión de
codos/rodillas, dirección de brazos/antebrazos y velocidades angulares. La web
permite configurar fuentes, reconstrucción, señales y ruteos mientras continúa
la captura; la calibración se hace antes de tocar, y se recupera al repetir setup.

Empezar con un cuerpo. Después incorporar dos cuerpos, con selección de persona
global que no cambie durante cruces. La disponibilidad de una tercera cámara no
debe exigir reconstruir el laboratorio ni recalibrar las dos existentes si sus
posiciones/óptica y marco común siguen válidos.

## Qué tenemos y qué falta

Disponible: detector e identidad HarMoCAP, captura de último cuadro, R09 con
calibración declarada K/R/t, triangulación DLT de dos vistas, inspector y relojes,
instrumento/ruteos/presets y seis voces continuas. La triangulación actual recibe
pares offline: no abre cámaras, sincroniza exposiciones ni asocia personas.

Hay tres diferencias concretas que hay que implementar:

- `LiveCamera` conserva una sola observación reciente. Multivista necesita un
  historial pequeño por cámara para elegir cuadros del mismo instante.
- `LatchingCamera` fecha después de `read()`: mide recepción en el host, no
  necesariamente exposición. Un reloj compartido no demuestra sincronización.
- `MotionFrame` admite 3D, pero `kinematics.person_points` recorta a `[:2]`;
  ángulos y canales colectivos también usan XY. Agregar Z al JSON no habilita
  análisis 3D. El contrato musical tampoco distingue puntos `inferred` de R09:
  definir un puente explícito, conservando procedencia, en lugar de llamar
  observado a lo reconstruido.

## Ubicación y cámaras

| Setup | Disposición inicial a ensayar | Qué esperamos ganar |
|---|---|---|
| Dos | Ambas miran el mismo volumen completo, separadas aproximadamente 60–90° alrededor del centro; evitar vistas casi paralelas y exactamente opuestas | Profundidad, ángulos espaciales y primera lectura de giro del tronco |
| Tres | Añadir una vista posterior oblicua, inicialmente alrededor de 200–240° respecto de la frontal; ajustar para que comparta el volumen y aporte otra perspectiva | Dos vistas útiles durante más giros y una tercera para contrastar detecciones incompatibles |

Son puntos de partida, no ángulos óptimos demostrados. Mirar cobertura de cuerpo
completo y manos extendidas en toda la zona de rope-flow. Colocar soportes fuera
del barrido de la cuerda. Comprobar cámaras reales antes de fijar distancia,
resolución o conectividad. La primera implementación se limita a las C920 USB
disponibles; no incluye adaptadores de teléfonos, red ni HDMI.

### Perfil concreto de las tres C920

Comenzar con **MJPEG, 1280×720, 30 FPS solicitados**, si cada unidad expone ese
formato; leer siempre el perfil efectivo. Subir a 1080p sólo si mejora joints
pequeños sin introducir atraso/drops. Separar resolución de captura de `imgsz`
del detector. Un formato comprimido reduce tráfico USB, pero añade decodificación
y no soluciona saturación de inferencia.

Al encontrar el hub, identificar A/B/C por serial o puerto físico estable, no por
`/dev/video0/2/4` cambiante. Las C920 son dispositivos USB 2.0: un hub USB 3.x no
convierte cada webcam en SuperSpeed ni garantiza ancho de banda independiente.
Revisar `lsusb -t` y comprobar las tres simultáneamente; distribuir en buses/puertos
distintos cuando sea posible. La consulta actual muestra dos buses raíz High-Speed
y la R24 en uno de ellos: evitar comprometer audio al probar video. Alimentación
externa del hub puede resolver energía, no agrega ancho de banda USB 2.0.

No activar micrófonos de webcams ni cambiar la salida R24. Resolver foco y
exposición manuales en controles visibles; la captura actual de HarMoCAP fuerza
ajustes V4L2 para C920e al abrir y tras el primer frame. El adaptador multivista
debe controlar/documentar esa política y no pisar silenciosamente los ajustes
del usuario. Foco/zoom/resolución que cambian requieren revisar calibración.

Las tres C920 no se considerarán sincronizadas por iniciarlas juntas: comenzar
con señales visuales comunes, estimar desfases y conservar el diagnóstico de
incertidumbre durante movimiento rápido. No comprar hardware de sincronización
por adelantado; decidir a partir del primer ensayo con las cámaras disponibles.

Perfil inicial a probar: captura a 30 FPS, resolución suficiente para articulaciones
y costo de inferencia 320/640 seleccionable. Fijar foco/zoom y exposición cuando
el dispositivo lo permita, con iluminación que reduzca blur. Verificar frecuencia
efectiva, ancho de banda USB y si comparten controlador; no confundir captura
30 FPS con tres inferencias simultáneas a 30 FPS.

## Calibración recuperable

Un recorrido web guiado con tablero ChArUco o damero plano de dimensiones medidas:

1. Intrínsecos/distorsión por cámara, con distintas inclinaciones y posiciones.
2. Extrínsecos con el tablero visible entre cámaras en una zona común; ajustar
   todas al mismo marco. No exigir que aparezca en las tres a la vez si hay
   suficientes observaciones enlazadas y el setup es identificable.
3. Definir escala, suelo/origen y ejes del laboratorio; verificar con posiciones
   reservadas del tablero y una distancia conocida en el volumen de trabajo.
4. Guardar el rig: dispositivos estables, resolución, óptica/crop, K/distorsión,
   R/t, tablero, escala y comprobación. Preview calibrado y datos corresponden a
   la misma imagen; convertir `x_iso/y_iso` de HarMoCAP a píxeles antes de corregir
   distorsión. Si hay resize/crop, transformar intrínsecos coherentemente.

Reutilizar cuando no cambió el setup. Resolución/crop/zoom o movimiento de una
cámara invalida la parte afectada; comprobar extrínsecos al volver a montarla.
Agregar la tercera exige sus intrínsecos y su enlace al marco existente. Mantener
separada calibración de cámaras y escala corporal: los presets musicales no
transportan extrínsecos a otra habitación. Conservar el guardado/restauración de
calibración que Nicolás acaba de aceptar, con contexto espacial adicional.

## Sincronización y demora: antes de triangulación musical

Capturar cada cámara independientemente; conservar timestamp fuente/driver,
recepción e inferencia por separado. Consultar timestamps de V4L2 si existen,
incluidos su reloj y origen exposición/fin de cuadro. No confundir el momento
de lectura del buffer con el momento físico de exposición.

Hacer una señal visual común visible en todas las cámaras para estimar offsets
y comprobarlos con otras marcas durante la toma. A 30 FPS no se demuestra
sincronía submilisegundo: hay fase de muestreo, exposición y rolling shutter.
Si sólo tenemos timestamps de recepción, el estado debe indicar aproximación y
su incertidumbre; la web permite explorar con esa limitación visible.

El coordinador selecciona observaciones nuevas, ya recibidas, dentro de una
ventana temporal configurable y con espera máxima acotada. Publica tiempo fuente
y disponibilidad reales por separado; no usa muestras futuras que aún no llegaron.
Un pequeño historial permite elegir mejor que combinar las tres últimas muestras
sin atender a sus tiempos. Los conjuntos publicados deben avanzar en tiempo.

Configurar desfase permitido, edad máxima y espera. El error temporal importa más
en muñecas rápidas que en el core: informar ambas regiones, no escoger un umbral
por apariencia del esqueleto. Si llegan tarde cuadros, descartarlos sin acumular
retraso; si falta soporte, declarar pérdida. Medir costos de captura, inferencia,
emparejamiento y publicación, además del desfase audiovisual observado. Metas
de frecuencia/latencia se fijan después de probar las cámaras disponibles.

## Reconstrucción con dos o tres vistas

- Detector y tracking independientes por vista. Un `track_id`/slot de una cámara
  no identifica a la misma persona en otra. En la primera prueba elegir un único
  cuerpo; luego asociación global por geometría epipolar, tiempo y continuidad,
  con confirmación visual/manual cuando haya ambigüedad entre personas.
- Con dos vistas: reutilizar el núcleo DLT, controles de geometría, profundidad
  positiva y reproyección, con su entrada streaming bien definida.
- Con tres: elegir soporte **por articulación**, no una sola cámara ganadora
  para todo el cuerpo. Probar triangulación conjunta ponderada y consenso de
  pares. Si una vista contradice a las otras, mostrar exclusión/ambigüedad; tres
  detecciones no garantizan saber cuál es correcta. Rechazar geometría degenerada.
- Con al menos dos vistas válidas, reconstruir aunque la tercera pierda ese
  joint. Con una sola, el joint 3D queda sin soporte; el preview 2D puede seguir.
  No sustituir silenciosamente profundidad ni cambiar el instrumento a 2D.
- Estado por joint: cámaras contribuyentes, tiempos/desfase, reproyección,
  ángulo de rayos y causa de pérdida. Confianza del detector no es precisión en
  centímetros. Conservar puntos 2D originales y XYZ inferidos por separado.
- Condicionamiento posterior a la fusión, causal y configurable; comparar sin
  filtro/con rechazo de outliers. Cambiar pares no debe provocar saltos ficticios.
  Longitudes constantes sólo se consideran en 3D y con tolerancias, nunca sobre
  proyección 2D. No introducir una espera/suavizado grande para ocultar fallos.

Una cámara caída pasa de tres a dos cuando hay soporte. Con dos cámaras, perder
una suspende señales 3D dependientes y libera suavemente las voces. Reabrir una
cámara limpia su historia temporal; moverla exige comprobar calibración. Los
resets no inventan velocidad, giro ni articulaciones retenidas como movimiento.

## Qué rotaciones podemos explorar con COCO-17

| Señal inicial | Construcción / límite |
|---|---|
| Giro de caderas y hombros respecto al mundo | Ejes izquierda–derecha triangulados, proyectados al plano del suelo o transversal del tronco; elegir y mostrar el marco |
| Giro relativo hombros–caderas | Ángulo firmado entre esos ejes alrededor del eje de tronco declarado; separar inclinación global de torsión aparente |
| Inclinación y orientación del tronco | Centros de hombros/caderas y ejes laterales; marco geométrico aproximado, no medición independiente de todas las rotaciones de pelvis/tórax |
| Flexión de codo/rodilla y dirección segmentaria | Tres joints para flexión; dos para dirección espacial. Puede funcionar durante movimiento hacia/desde cámara |
| Velocidad angular y relación entre regiones | Derivadas causales con soporte continuo; unwrap/matrices/cuaterniones sin saltos ficticios en ±180° ni derivar a través de gaps |

COCO-17 no describe dedos/palma, pies completos ni varios landmarks internos del
tronco. Dos extremos de un segmento no determinan su giro longitudinal. Con este
tracking no prometer pronación/supinación fiel del antebrazo ni una orientación
anatómica completa e independiente de la pelvis. Para ese segundo corte, evaluar
pose con más landmarks de manos/pies o referencias visuales simples; no requiere
comprar sensores. Una orientación degenerada queda inválida, no se fija por azar.

## Web, presets y sonido

Una sección **Cámaras / 3D en vivo** en la web actual:

- Fuentes A/B/C, perfiles efectivos, previews con skeleton y overlays de calidad,
  conexión, FPS, demoras y selección de persona global.
- Crear/guardar/cargar/verificar rig calibrado, tablero y sincronización; controles
  avanzados para sus umbrales, sin editar JSON/código para explorar normalmente.
- Vista 3D orbitable, ejes de regiones, trazas y señales; vista por cámara con
  reproyección. Calidad y razones en un panel estable, sin saltos de layout.
- Selección 2D/3D explícita, marcos mundo/core, normalización, filtros y ventana
  de derivadas. Preview actualizado mientras se ajusta todo salvo parámetros que
  realmente requieran reiniciar captura/recalibrar; explicarlo en ese control.
- Matriz de ruteos para giro/velocidad/relación hacia activación y articulación
  existentes. Conservar seis voces, afinación y fases continuas; modulaciones de
  pitch/fase siguen siendo otra opción explícita. No reataques por cada cuadro.
- Presets guardan método/ruteos; rig y offsets quedan ligados a fuentes/setup.
  Restaurar calibración compatible y preguntar ante otro contexto. No convertir
  escala de torso proyectada en metros ni aplicar umbrales 2D a 3D silenciosamente.

Primero dejar sonar la ruta 2D seleccionada mientras se inspecciona 3D en paralelo
dentro de la misma sesión. Habilitar sonificación 3D explícitamente cuando el
usuario quiera probarla; jamás cambiarla automáticamente al perder una cámara.
No iniciar grabación de las vistas por defecto.

## Entregas de implementación cuando se decida avanzar

1. **Captura y tiempo:** dos fuentes con previews/telemetría, soporte temporal
   acotado y medición de costo en este host. Adaptar captura local sin cambiar
   HarMoCAP upstream por esta planificación. Comprobar CPU/GPU antes de elegir
   arquitectura: dos workers separados reutilizan el camino actual; si hace
   falta compartir modelo/inferencias, separar trackers por vista. El actual
   `YOLO.track(persist=True)` no admite alternar cámaras como si fueran un stream.
2. **Rig y 3D visible:** calibración web + dos vistas trianguladas + inspector
   temporalmente coherente. Prueba de profundidad/distancia reservada y pérdida
   de cámara; comparación con 2D dentro de la misma web.
3. **Rotaciones y sonido:** puente tipado 3D con estados/procedencia, cinemática
   y modelos compatibles con XYZ, señales de la tabla y ruteos. Presets 2D
   aceptados conservados; escala/unidades/resets comprobados. Escucha de Nicolás.
4. **Tercera vista y dos personas:** soporte/outliers por joint y recuperación
   3→2; después identidad global en cruces. No hace falta esperar este corte
   para explorar con dos cámaras y un cuerpo.

Cada entrega usa el checkout y launcher únicos. Pruebas concretas: reconstrucción
de puntos conocidos con ruido/desfase, causalidad y edad de cuadros, pérdida/
reconexión y ausencia de derivadas falsas, identidad entre vistas, conservación de
Z en análisis, unidades/calibración y continuidad de audio. El ensayo físico
consiste en movimientos separados de tronco/brazos, acercamiento/alejamiento,
giros y rope-flow; medir sincronía y revisar si retiene movimiento y mejora
rotaciones. No repetir bancos no afectados ni convertirlo en evaluación formal.

## Decisiones abiertas que dependen del hardware

Modelo nominal disponible: tres C920. Quedan hub/soportes y puertos efectivos,
formatos y revisión de cada unidad; necesidad de captura V4L2/GStreamer; costo de dos/tres inferencias,
calidad del tracking en vistas lateral/trasera. No prometemos 30 FPS de 3D con
el actual modelo en CPU ni inferimos exposición sincronizada porque hay tres USB.
Si la limitación es cómputo, ajustar detector/resolución/cadencia con telemetría;
si es sincronía o cobertura, corregir captura/ubicación antes de añadir filtros.

## Referencias y base

- Código local: [captura](../../src/harmonic_weaver/lab/perception.py),
  [worker](../../src/harmonic_weaver/lab/perception_worker.py),
  [DLT R09](../../src/harmonic_weaver/lab/research/spatial_multiview.py),
  [cinemática actual](../../src/harmonic_weaver/lab/kinematics.py).
- [OpenCV: calibración y reconstrucción](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html),
  [ChArUco](https://docs.opencv.org/4.13.0/da/d13/tutorial_aruco_calibration.html).
- [V4L2: relojes y origen del timestamp](https://docs.kernel.org/6.8/userspace-api/media/v4l/buffer.html).
- [Anipose: preparación y calibración multivista](https://anipose.readthedocs.io/en/latest/start3d.html),
  referencia de calibración; no insertar su pipeline offline como runtime live.
- [Logitech: ficha C920-C, 1080p hasta 30 FPS](https://www.logitech.com/assets/52363/logitech-webcam-c920c-datasheetweb.pdf)
  y [ficha C920e, USB 2.0](https://hub.sync.logitech.com/c920e/post/specifications---c920e-business-webcam-TKnike7FetCzuAt).
  Son variantes de la familia: la revisión y formatos de nuestras tres unidades
  se verificarán al conectarlas, no se deducen de estas fichas.

Los ángulos de colocación, perfiles y entregas son propuestas de ingeniería para
nuestro laboratorio. Todavía no son mediciones con dos/tres cámaras ni aceptación
humana de sonificación 3D.
