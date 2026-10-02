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
