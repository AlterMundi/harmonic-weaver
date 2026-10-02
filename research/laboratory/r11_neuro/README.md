# R11 · Observaciones crudas y protocolo de señal/ruido

Corte 1. Línea #25, continuación de R09 clocks y R10 experiencia. Contrato de
importación implementado; no driver, adquisición, hardware o inferencia EEG
validados. No bloquea exploración cotidiana ni altera instrumento/sonido.

`neuro_observations.Stream` conserva unidades por canal, referencia declarada,
posición opcional, índices y timestamps originales, valores/null+causa y anotaciones
de artefactos. No filtra, interpola, convierte ni llama a un dispositivo. Clock usa
contrato afín R09 con incertidumbre y procedencia explícitas. Escala counts→µV
puede declararse con evidencia, nunca aplicarse silenciosamente. No asigna electrodos,
referencia, rate o identidad desde nombres de archivos. Inventario de hardware
real pendiente; provider openbci_export es declaración, no validación de formato.

Dos pruebas pasaron (0,14 s): cero vs null, raw intacto, índices saltados, artefacto
anotado, repetibilidad; causa/canal/tiempo/NaN/conversión/annotation inválidos
rechazados. Fixtures sintéticos, sin grabaciones humanas ni prueba física.

## Protocolo inicial para acordar antes de adquisición

- Definir señal observable y tarea por condición **antes** de elegir SNR. Una
  potencia de banda o amplitud no equivale a placer/belleza/agencia. Las preguntas
  subjetivas siguen en R10, separadas de medidas bioeléctricas.
- Inventariar placa/modelo/firmware/transporte, canales, referencias, unidades,
  gains por canal, formato export y relojes reales. No asumir Cyton/Daisy/Ganglion
  equivalentes ni interpretar timestamps de recepción como adquisición.
- Empezar por fixture sintética con señal y ruido separados conocidos. Declarar
  si el cociente es potencia señal/ruido, qué ventana/estimador utiliza y cómo trata
  potencia cero. Después controles de señal física definidos con colaboración
  apropiada; no llamar "ruido" a cualquier respuesta inesperada.
- Conservar original sin reescritura y SHA de procedencia. Segmentación/filtrado/
  referencia/normalización producirán derivados versionados, con parámetros y
  soporte de muestras. Rechazar índice/clock ambiguos, exponer gaps, no rellenar.
- Anotar movimiento, músculo, ojos, red eléctrica, saturación y pérdida de contacto
  como posibles causas, no diagnósticos automáticos ni exclusiones retrospectivas
  inventadas. La configuración de exclusión debe ser explícita y conservada.
- Comparar video_only/sound_only/audiovisual/desynchronized de R10 sólo con diseño
  predefinido. Practicante/observador por separado; rol/slot no autentican identidad.
  Registrar niveles y sincronización física independientemente del clock navegador.
- Medir anchors y reservar anchors de validación para reloj; reutilizar R09 si el
  reloj real es compatible, conservar incertidumbre y no extrapolar sin declararlo.
  Evento del player R10 es telemetría declarada, no trigger medido por placa.

## Referencias y límites

[Formato oficial Cyton](https://docs.openbci.com/Cyton/CytonDataFormat/) distingue
counter, canales, AUX y variantes con timestamp. Su escala depende de configuración;
por eso este contrato exige metadatos explícitos, no defaults de una placa supuesta.
[SDK Cyton](https://docs.openbci.com/Cyton/CytonSDK/) documenta comandos y variantes.
Estas fuentes no establecen nuestro hardware ni una hipótesis científica.

Pendientes: API/UI/import y persistencia/manifest de observaciones; estimadores y
controles SNR explícitos; adaptador de export real y clocks/bindings R10; hardware,
configuración/electrodos/protocolo acordados, adquisición y validación física.
R12/R13 siguen abiertos. No resultados sobre estados mentales o fisiología.


## Corte 2 · API e inventario web

POST /api/research/r11/inspect valida Stream y devuelve inventario/raw. NeuroPanel
en Investigación permite native JSON import16MiB/editor, inspect explícito y
exportación; tabla unidades/referencia/support/artefactos declarados. Editar limpia
resultado y generaciones descartan respuestas tras unmount. No default hardware,
no normalización/filtrado/SNR ni archivo persistente.

Build y tres pruebas núcleo/API pasaron (0,88 s; warning AnyIO sin fallo), Chrome
real contra fixture API pasó (1,4 s): import/export mantiene0/null/.008/unidad,
gap visible, causa vacía rechazada y tabla inválida no revive. Datos sintéticos,
sin audio/hardware humano. Servidor fixture detenido. Pendientes manifest/servicio,
SNR/control synthetic y unidades/clocks de export real; aceptación física pendiente.


## Corte 3 · Observaciones persistentes y manifest

neuro_run publica Stream/request, inventario/result y manifest con hashes/código/
entorno. Recalcula inventory actual, histórico dice integridad sólo y siempre exige
raw/result binding. NeuroService usa identidad por contenido para retry/restart,
listado y attachments; POST/GET observations y artifacts API. No registra dispositivo
ni normaliza/filtra; importación raw explícita conserva metadata y datos.

Cinco pruebas núcleo/runner/API pasaron (1,08 s): retry/restart/export idéntico,
0/null/causas preservadas, inventory alterado con hashes rehechos rechazado,
histórico y rawbinding, traversal/artefacto desconocido. Warning AnyIO sin fallo.
Pendientes guardar/recovery/reabrir web, presupuestos de tamaño/latencia, estimadores
SNR, adaptador/hardware real y sync física. Fixtures sintéticas; sonido intacto.


## R11 · Corte 4: guardado y recuperación web

Investigación → R11 permite guardar el Stream inspeccionado, listar registros y
reabrir inventario/raw, con enlaces a request/result/manifest. Antes del POST se
congela el envío en sessionStorage; si falla la respuesta, un reintento explícito
tras recargar conserva el contenido y reutiliza la identidad del servidor. No se
reenvía automáticamente. El pendiente puede exportarse o descartarse sin borrar
registros del servidor. Si el navegador no puede guardar el pendiente, no envía.
SessionStorage no sustituye un archivo duradero y no garantiza recuperación al
cerrar la pestaña; datos grandes y latencia requieren una evaluación posterior.

Chrome contra API sintética: 1 prueba pasó (2,0 s total, 1,2 s ejecución), incluyendo
POST aceptado con respuesta perdida, recarga, reintento idéntico, registro único,
reapertura y request original con cero/null/unidades/clock/gaps intactos. Cinco
pruebas Python de contrato/runner/API pasaron (1,50 s; deprecación AnyIO sin fallo).
Build TypeScript/Vite pasó. Servidor de prueba detenido, sin hardware ni audio.
Pendientes estimadores/controles SNR, export real, presupuestos de datos, hardware,
adquisición y sincronización física. No cambia sonido, presets ni defaults.


## R11 · Corte 5: control sintético de señal/ruido conocido

neuro_snr y POST /api/research/r11/synthetic-snr generan dos tonos dimensionless
independientes y su suma. La designación señal/ruido es parte del control: no se
estima separación desde EEG ni se interpreta ruido fisiológico. Config estricto
con amplitud/frecuencia/fase/offset por componente, rate/count (2–20000), ventana
[start,stop), gaps y exclusiones explícitos; frecuencias estrictamente bajo Nyquist.
No dispositivos ni cambios de sonido/defaults.

Métrica known_component_mean_square_v1: media cuadrática de cada componente
sobre idénticos índices retenidos, con retiro opcional de media independiente sobre
ese mismo soporte. No ponderación temporal, interpolación, filtro o inferencia de
banda. Cociente en dB = 10(log10(Pseñal)−log10(Pruido)). Conserva componentes,
suma, timestamps, soporte exacto y config. Potencias numéricas cero producen
noise_zero/signal_zero/both_zero y dB null, nunca Infinity; menos de dos muestras
produce insufficient_support. Magnitudes son dimensionless², no watts físicos.
Esta definición con componentes conocidos coincide con el caso documentado en
[referencia SNR MathWorks](https://www.mathworks.com/help/signal/ref/snr.html);
no adopta sus estimadores espectrales ni los aplica al registro de un cuerpo.

NeuroSNRPanel ofrece controles para todos los parámetros, import/export de config
portable y export del resultado completo. Editar invalida resultado; validación
API explícita rechaza configuración inválida. Cambiar el control no cambia las
observaciones crudas ni adquiere hardware. El resultado se descarga localmente;
aún no tiene archivo/manifest de servidor ni verificador de código histórico.

Evidencia: 12 pruebas Python pasaron (1,36 s; AnyIO deprecación sin fallo), build
TypeScript/Vite, dos recorridos Chrome contra API sintética (2,4 s total). Control
analítico amplitudes2:1 da6,0206dB; DC3 cambia potencia2→11 y retiro media devuelve2;
soporte común [10,12,14,16] tras ventana/gaps/exclusiones; ceros/support insuficiente,
frecuencia Nyquist, índices inválidos y NaN rechazados. Chrome verifica export de
resultado, import/export de configuración, ventana/gaps, ruido cero e invalidez sin
tabla anterior. Servidor de prueba detenido. Datos sintéticos, sin escucha humana.
Pendientes manifests/verificación de corridas SNR, controles adicionales, datos
reales/adaptador, inventario hardware, protocolo/estimador sobre señal física y sync.
Roadmap R01–R13 abierto; sin resultados sobre estados mentales o fisiología.
