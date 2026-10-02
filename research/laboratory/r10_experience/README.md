# R10 · Experiencia de practicantes y observadores

Issue #24; rama feat/r10-experience-protocol sobre PR #76. No cambia el
instrumento cotidiano ni hace obligatoria una evaluación para explorar.

## Corte 1 · Plan declarado y respuestas tipadas

experience_protocol.py y API /research/r10/preview generan calendario determinista
para estímulos/ventanas declarados, rol practitioner u observer y participant_slot
local (no nombre personal requerido). Configuration ofrece condiciones video_only,
sound_only, audiovisual y desynchronized opcional; repeticiones, preview_gain,
offset de desacoplamiento, escala y preguntas editables. Intervalos <=120s,
condiciones/estímulos/preguntas únicos, límites y entradas finitas/estrictas.

Order_index elige una permutación de condiciones; cada repetición avanza una
posición de ciclo. Todas las permutaciones balancean posiciones y transiciones
sólo al completar el ciclo (3 condiciones=6; 4=24). No se afirma balance para
reclutamiento incompleto. Orden de estímulos permanece explícito, sin optimización
por resultado. Cada trial tiene ID, condición, flags audio/video, ventana y offset
nominal. No reproduce ni prueba exposición; references no resuelve medios.

validate-response exige cada pregunta configurada: null sin respuesta, números
en escala. Mantiene placer, belleza, legibilidad, agencia, sorpresa y reorganización
agradable separados; defaults son preguntas de exploración, no escalas validadas.
Rol se conserva; no infiere placer/eficiencia/HIT/fisiología. Web edita protocolo y
respuesta, muestra calendario, exporta preview, config portable sin participante/
estímulos y respuesta declarada. Operaciones stateless, sin guardar datos humanos.

Validación: 3 pruebas núcleo/API pasaron (0,79 s): ciclo completo3 balancea posiciones/
transiciones, repetición exacta, flags/offset, null/escala/IDs y rechazos. Build completo
pasó. Chrome API aislada pasó (1,4 s): calendario3, exportación nativa config sin
slot/estímulos, respuesta sintética válida, respuesta fuera de escala rechazada y
export obsoleto ausente. Servidor apagado; no sesiones humanas, medios privados,
escucha, exposición o sincronía física verificadas. Audio/defaults intactos.

## Siguientes entregas y dependencias

1. Presets portables guardables/importables, protocolo congelado con manifest y
   procedencia de estímulos resueltos por IDs (EVAL/R05/video) para repetir selección.
2. Player de condiciones con clock/audio/video y eventos de exposición observados
   por software, separando abort/pause/gaps/seeks de ensayos completados. Relojes y
   ganancia nominal no prueban niveles ni sincronización físicos: registrar medición.
3. Registro explícito de respuestas por trial/slot/rol, versiones y faltantes; no
   convertir preview ni validación sintética en respuesta humana realizada.
4. Comparador de respuestas individuales sobre estímulos/condiciones comunes,
   cobertura/faltantes, repetición intraindividual y acuerdos/desacuerdos; estimaciones
   de incertidumbre requieren diseño y tamaño adecuados, nunca rellenar null con0.
5. Decidir preguntas/escala/contexto e instrucciones con participantes; niveles
   comparables, orden completo cuando posible, roles distintos y ventanas idénticas.
   Desacoplamiento temporal no equivale a todas las alternativas de control.
6. Conectar R11/R12 por sincronización/procedencia, conservando independencia del
   registro fenomenológico: ningún proxy EEG/energético sustituye una respuesta.

No es un experimento ejecutado ni resultado científico. Requiere fuentes verificadas,
participantes y aceptación humana; avanzar en software no resuelve esos requisitos.


## Corte 2 · Presets portables persistidos

API /research/r10/presets guarda/lista/exporta name/config versionados con lectura
regular acotada. Config estricto excluye slot, rol, order_index, estímulos, ratings
y trial_id. Exportación sin ID local; append-only, reapertura tras restart. Web guarda
config de preview validada; importa preset completo o config raw exportada (64 KiB),
no aplica automáticamente. Aplicar reemplaza sólo config del protocolo editable,
conserva participante/rol/order/stimuli y limpia preview/respuesta validada sin ejecutar.

Cuatro pruebas núcleo/API pasaron (0,92 s), build completo pasó. Chrome API aislada
pasó (1,7 s): guardar, descargar/importar envelope y raw config, aplicar conservando
selección, limpiar preview y tres presets tras reload. Mantiene pruebas de respuesta
sintética/rechazo fuera de escala. Servidor apagado; no exposición/participación
humanas ni niveles físicos verificados. Defaults del instrumento/audio intactos.
Pendientes protocolos congelados/manifests, resolución de estímulos, player,
exposición observada, respuestas persistentes y análisis sobre soporte común.
