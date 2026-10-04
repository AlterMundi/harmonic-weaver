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

## Corridas SNR recuperables — 2026-10-02

Investigación → R11 → control sintético: calcular, **Guardar corrida SNR R11**,
actualizar listado y abrir una corrida. Recupera parámetros y resultado congelados;
request/result/manifest se descargan por separado. Cambiar parámetros invalida el
resultado visible. El cálculo exploratorio sigue sin guardar por defecto.

POST/GET `/api/research/r11/snr-records` y GET
`/api/research/r11/snr-records/{id}/artifacts/{request.json|result.json|manifest.json}`
usan identidad de configuración para reintento/reinicio sin duplicar resultados.
Publicación en staging; una interrupción previa a promoción no publica un registro
parcial. El navegador conserva el envío en sessionStorage antes del POST y permite
recuperación explícita, exportarlo o descartarlo. No reenvía automáticamente;
conservar el JSON exportado sigue siendo necesario para persistencia entre sesiones
de navegador. Máximo del control: 20000 muestras, artifacts de lectura hasta 32 MiB.

El manifest separa hashes de artefactos, hashes de módulos efectivamente importados
y entorno. `verify(recompute=True)` recalcula componentes/soporte/métricas; exige
estructura, índices y configuración exactos, y compara floats con rel_tol=1e-12,
abs_tol=1e-12. Diferencias de entorno/procedencia aparecen como flags, no bloquean
un resultado numéricamente equivalente. `recompute=False` declara sólo integridad,
no recomputación. Los hashes no son firmas ni validación de hardware/EEG.

Evidencia: 18 tests núcleo/API/archivo pasan y Chrome contra API/UI reales prueba
respuesta POST perdida después de guardar, reload/reintento idéntico, un solo
registro y reapertura de configuración/resultados. Build pasa. Fixture sintético
sin hardware ni audio. Quedan adaptador/export real, inventario de placa, adquisición,
control de señal física y sincronización medida; esto no resuelve #25 científicamente.

## Importación CSV explícita — 2026-10-02

Investigación → R11 → Importar tabla CSV: cargar UTF-8 o pegar tabla, declarar
metadatos y mapeo, convertir, exportar conversión/procedencia y usar observaciones
en R11 para guardarlas con el recorrido existente. Metadatos exigen source/slot/
provider/hardware/rate/clock/channels completos; no se deducen del archivo.
El mapeo portable se importa/exporta separado de cuerpo/fuente/calibración.

POST `/api/research/r11/import-csv` recibe schema_version1, csv_text, metadata y
mapping. Mapping declara delimiter (coma/punto y coma/tab), skip_rows, index_column,
time_column, time_units(seconds/milliseconds/microseconds), channel_columns por ID
y missing_tokens/missing_cause. Todos los canales requieren columnas distintas.
Preamble explícito, header único, filas completas y contador/time estrictamente
crecientes. Un contador de paquete que se reinicia o envuelve NO es un índice
monótono: se rechaza, sin inventar pérdida/tiempo ni unwrap de una placa supuesta.
No es un parser automático de cualquier export OpenBCI; hay que conocer su formato.

Conserva cero/null/gaps/unidades; tokens faltantes son literales elegidos. Convierte
sólo la unidad de timestamp a segundos, sin filtrado ni conversión de amplitud.
Digest SHA256 del UTF-8 completo incluye BOM/newlines originales de archivo;
parser ignora BOM inicial. Browser usa decodificación UTF-8 estricta y conserva
BOM al enviar, sin inferir otro encoding. Editar texto puede cambiar el digest.
Ignorados y mapping quedan en import_provenance del resultado exportable.

Guardar observaciones conserva Stream y raw_source_sha256; **no archiva el CSV ni
el mapeo** en el registro nativo. El archivo separado de importación descrito abajo
conserva ambos; no atribuir al registro Stream una procedencia que no guarda.
Raw CSV hasta16MiB, samples decodificados hasta16MiB y120000 filas; se rechaza
expansión excesiva de etiquetas de faltantes antes de construir un registro enorme.

Evidencia: 13 controles importer (incluida expansión bounded), integración API
convertir→guardar→reabrir y Chrome UI/API real con BOM/CRLF, digest exacto, null/
cero/tiempo, descarga de procedencia y recuperación desde archivo R11. No CSV de
hardware ni medición humana verificados; hardware/clocks físicos siguen pendientes.

## Archivo local de importaciones CSV — 2026-10-03

Después de convertir, **Guardar importación CSV R11** conserva en
`research/r11-csv-imports/` del data root: `source.csv` (bytes UTF-8 completos,
incluyendo BOM/CRLF), `request.json` (original, metadatos y mapeo normalizado),
`result.json` y `manifest.json`. No se archiva automáticamente al convertir.
Contenido idéntico recupera el mismo registro; editar el CSV o su mapeo crea otro.
Una publicación interrumpida queda oculta y no impide un reintento nuevo.

Actualizar/Abrir importación restaura texto, metadatos, mapeo y conversión desde
el servidor después de recargar. Descargas de los cuatro artefactos disponibles.
Recalcular importación compara conversión actual con la archivada sin sobrescribir
ni exigir igualdad del entorno o hashes de código. Lecturas ordinarias verifican
integridad y binding del original; no ejecutan conversión implícita.
Si se pierde la respuesta del guardado, actualizar el listado o repetir la misma
entrada recupera el registro publicado. No depende de guardar un CSV grande en
sessionStorage; el servidor es local y el navegador no reenvía al recargar.

API: POST/GET `/api/research/r11/csv-imports`, GET `/{id}/artifacts/{name}` y
`/{id}/verification` (integridad), `?recompute=true` (conversión explícita).
El registro Stream existente sigue compatible y separado. Esto conserva la
fuente declarada; no autentica adquisición, hardware, sujetos o sincronización.
