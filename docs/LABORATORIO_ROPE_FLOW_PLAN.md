> **Documento histórico de exploración.** La especificación vigente es [laboratory/SPEC.md](laboratory/SPEC.md), con [decisiones](laboratory/DECISIONS.md) y [agenda completa](../research/laboratory/AGENDA.md). Las revisiones posteriores prevalecen sobre el orden y las hipótesis de implementación de este borrador.

# Laboratorio de movimiento, sonido y geometría

Fecha: 2026-09-29. Estado: propuesta de construcción; no implementado.

## 1. Propósito y decisiones iniciales

Construir una aplicación web local para explorar cómo la organización del movimiento corporal y de la cuerda puede transformarse en sonido y geometría visual. Primera entrada: videos de rope-flow de Nicolás. El laboratorio permite importar, inspeccionar, reproducir, variar algoritmos/ruteos, comparar y guardar experimentos sin editar código.

Prioridad confirmada por Nicolás: exploración en tiempo real con máxima libertad y versatilidad. Dejar un video corriendo o recibir cámara en vivo, modificar parámetros/ruteos/algoritmos y sentir cómo cambia la respuesta sonora y visual. Guardar y recuperar configuraciones independientes de la fuente es esencial; grabar/exportar fragmentos de video + audio es opcional. Comparación formal y análisis offline son herramientas adicionales, nunca pasos obligatorios. La ubicación y selección de videos queda pendiente. No se presupone hardware nuevo ni se instala ningún modelo en esta etapa de planificación.

El criterio principal de la primera entrega es que se pueda encontrar y recuperar una configuración que «se siente bien» para quien se mueve y para quienes observan y escuchan. Con cámara hay un ciclo cuerpo→instrumento→percepción→nuevo movimiento; con video grabado el movimiento permanece fijo mientras el operador explora la respuesta. Ambos modos comparten todos los controles compatibles.

Tres preguntas independientes:

1. ¿Qué representación anticipa mejor el despliegue de un gesto, especialmente después de un Jpsh!?
2. ¿Qué transformación sonora conserva relaciones del movimiento que podemos reconocer y disfrutar?
3. ¿Qué propiedades sobreviven hasta una representación visual derivada exclusivamente del audio?

El laboratorio no presupone que predecibilidad, agrado musical y eficacia biomecánica sean equivalentes. Tampoco que el core sea siempre el iniciador: será una hipótesis seleccionable y contrastable, con referencias alternativas.

Decisiones de arquitectura propuestas: aplicación hermana lógica dentro de harmonic-weaver, servicio Python/FastAPI, frontend TypeScript/React, representación corporal y curvas mediante WebGL/Three.js, metadatos locales SQLite y artefactos en archivos. Reutilizar HarMoCAP para percepción y Shaper para síntesis; Weaver conserva organización, transformaciones y contratos. La UI existente de consonancia es un prototipo aprovechable, no la arquitectura completa del laboratorio. Verificar dependencias exactas al implementar, sin actualizaciones generales del entorno.

## 2. Corregir una distinción que afecta al diseño

Requisito explícito de Nicolás: preservar el Lissajous polifónico del software actual, formado por todos los armónicos que están sonando en función del movimiento. Los dos ejes X(t), Y(t) de la figura no limitan el número de voces: cada coordenada puede combinar todas las componentes activas. Antes de implementar, identificar el visualizador existente y documentar su fórmula, entrada y comportamiento; esa implementación será el baseline visual, sin sustituirla por un osciloscopio estéreo genérico.

Un Lissajous polifónico representa relaciones entre componentes sonoras. No es por sí solo una simulación de una placa, membrana o superficie de agua. Una figura cimática depende también del medio, sus condiciones de borde, excitación, amortiguamiento y evolución.

La aplicación tendrá tres vistas explícitas:

- Dibujo corporal/cuerda: observado o reconstruido desde video.
- Lissajous polifónico: conserva la composición de todos los armónicos activos del visualizador actual. Puede recibir muestras por voz o estado de síntesis sincronizado —frecuencia, amplitud, fase y envolvente— según la implementación existente. Un osciloscopio sobre la mezcla final será una vista complementaria.
- Medio virtual: respuesta modal de una membrana especificada, excitada por ese audio; aproximación física posterior. Mostrar desplazamiento, envolvente/RMS y nodos por separado. No simular arena ni llamarla placa de Chladni sin un modelo apropiado.

Para probar el recorrido cuerpo→sonido→imagen, las vistas sonoras no recibirán keypoints, nombres de gestos ni métricas corporales. Distinguir imagen derivada del estado/stems de síntesis de imagen derivada exclusivamente del PCM final: la primera puede conservar información de voces que no es recuperable de la mezcla. Ambas son válidas, con procedencia explícita. Una superposición artística directa podrá existir como modo distinto, nunca como evidencia de transferencia a través del sonido.

## 3. Estado observado del stack

- HarMoCAP: YOLO-pose, 17 puntos 2D con confianza/estado, normalización isotrópica, identidad, grabación y replay. La tercera componente es confianza, no profundidad. Su webapp ya distingue RunConfig/RenderConfig y procesa video con exportación; inspeccionar y reutilizar componentes, no duplicar percepción.
- El capturador en vivo emplea pacing y frames recientes. La sesión viva necesita colas acotadas y priorizar cuadros recientes, mostrando pérdidas y edad de muestra. La extracción offline opcional necesita decodificación secuencial con timestamps del medio, sin omitir cuadros por lentitud de inferencia. Auditar también la ruta de webapp antes de reutilizarla como extractor.
- Consonancia: seis zonas, predicción inercial, métricas cinemáticas, controles web, articulación cruda/plucks y configuración persistente. Hay cambios locales no publicados; preservar el estado exacto antes de migrar.
- Shaper: síntesis estéreo con continuidad de fase y render por bloques. El callback mezcla síntesis, lectura de estado y salida. El tap actual de grabación está ANTES del limitador final: no asumir que es el mismo PCM que se escucha.
- Weaver: rutas declarativas, validación, generaciones atómicas, contratos y estado autoritativo en servidor. Mantener estos principios. La integración del laboratorio no depende del gate de polifonía de Bands.

## 4. Flujo de datos y contratos

Video en reproducción o cámara → percepción en vivo o tracking cacheado → preparación causal de señales → representación/modelo → control y síntesis continuos → sonido y Lissajous polifónico sincronizados. La UI modifica este recorrido mientras la fuente continúa. Percepción, audio, visualización y trabajos pesados tienen ejecuciones desacopladas y colas acotadas.

Cada etapa declara inputs, outputs, unidades, marco de coordenadas, validez, temporalidad y versión. Separar tres clases de evidencia: observación 2D, inferencia 3D y reconstrucción multivista. El suavizado y las correcciones nunca sobrescriben la observación original.

Contratos de datos (su persistencia no es requisito para explorar; cámara y audio no se graban por defecto):

- MediaAsset: hash, duración, PTS/timebase, rotación, resolución, audio original y proxy de reproducción.
- PoseTrack: identidad, joint IDs, posiciones, timestamp original, confianza, observed/held/missing, backend/model hash, marco y unidades; z ausente en 2D.
- RopeTrack opcional: máscara o curva/puntos anotados, calidad y procedencia; cruces 2D no implican nudos 3D.
- FeatureTrack: definición/versionado, parámetros, ventana y timestamp de disponibilidad; unidades e incertidumbre disponible.
- GraphPreset: configuración portable con nombre, nodos/aristas, algoritmos/versiones, parámetros, ruteos, voces y configuración del Lissajous. No contiene una ruta obligatoria de video ni historia dinámica de la toma. Guardar/guardar como/duplicar/importar/exportar desde web.
- SessionState: fuente, dispositivo, posición, loop y disposición de paneles, separados del preset. Calibración de cada fuente separada; al reutilizar preset se recalibra o se aplica una calibración elegida explícitamente. Checkpoints de replay son un tercer objeto, no se trasladan a otro video.
- ExperimentRun: hashes anteriores, revisiones de repos y snapshot/patch de cambios locales relevantes, semillas, plataforma, eventos de edición, warmup, rango temporal y estado final.
- AudioArtifact: sample rate, canales, PCM final, stems/buses opcionales y correspondencia exacta entre muestras y tiempo fuente.
- Annotations/Evaluation: etiquetas humanas, regiones excluidas, particiones y resultados; separadas de las señales disponibles para el predictor.

Cache por dependencias para archivos y análisis opcionales. En sesión viva, cambiar ganancia modifica los siguientes bloques; no recalcula el pasado. Cambiar ventana migra o precalienta solo el estado afectado. Cambiar color no toca sonido. Un cambio de pose/modelo costoso se prepara en segundo plano, mantiene la ruta activa hasta estar listo y anuncia cuándo se aplica. Extracción anticipada/cache de videos es una optimización opcional, no condición de entrada.

## 5. Experiencia web

Una mesa con transporte común: video/esqueleto a la izquierda, sonido/Lissajous a la derecha, curvas y eventos abajo. Espacios de trabajo guardables: Explorar, Comparar, Ruteos, Calidad de tracking, Modelos, Experimentos. Controles en español y explicación breve con unidades; inspector avanzado para fórmulas y diagnóstico.

Recorrido principal: elegir archivo o cámara → iniciar → mover controles y ruteos mientras corre → guardar preset cuando se siente bien → recuperarlo sobre esa u otra fuente. Acciones siempre accesibles: play/pause/loop, selección de persona, mute/solo, deshacer, volver al preset y guardar como. No exigir recortar, etiquetar, generar un experimento ni exportar. Comparar A/B, anotar y grabar son acciones opcionales.

Dos disposiciones principales: Operar (controles junto al feedback) y Performance (imagen/Lissajous grande, controles esenciales). Permitir un segundo cliente web para que otra persona ajuste mientras Nicolás se mueve; autoridad en servidor y revisiones para evitar sobrescrituras. Macros asignables agrupan parámetros con rangos configurables; guardado rápido y favoritos ayudan a recuperar hallazgos. Interpolar presets solo entre parámetros compatibles; cambios discretos de algoritmo/topología usan transición declarada, no interpolación ficticia.

| Área | Controles disponibles desde web |
|---|---|
| Entrada | archivo/cámara, dispositivo, persona, loop, recorte opcional, rotación, espejo de visualización separado del analítico, original/proxy |
| Percepción | backend instalado, modelo, resolución, stride, confianza, revisar/corregir puntos, exclusiones y nueva extracción |
| Coordenadas | cámara, torso/core, referencia fija, 3D cuando exista; escala fija/calibrada; mantener traslación global como canal |
| Señales | filtro y ventana, causal/retrospectivo, derivador, ruido, gaps, validación, normalización por toma o calibración congelada |
| Cuerpo | selección de joints, pares/cadenas, pesos, referencia core o alternativa, lado separado/combinado |
| Modelos | algoritmo, horizonte, ventanas, rango de modos, regularización, lags, ajuste/aplicación, conjunto de entrenamiento |
| Ruteo | matriz fuente→destino, curvas, mezcla, signo, ganancia, offset, clamp, deadband, mute/solo, bypass, estado inválido |
| Sonido | fundamental, ratios/escala, frecuencias libres, snap, pitch/gain/phase/pan, envolventes, plucks/drone, buses, límites |
| Lissajous | composición polifónica original, todas las voces activas, contribuciones/proyección, persistencia, escala; osciloscopio de mezcla como vista adicional |
| Medio virtual | tipo/geometría soportada, modos, amortiguamiento, excitadores, canales→excitadores, visualización y tiempo de asentamiento |
| Comparación | presets A/B, fragmento común, nivel original o compensado, orden ciego opcional, gráficos, métricas y anotaciones |
| Barridos | parámetros discretos/rangos, cantidad máxima de variantes, presupuesto de cómputo, cola, cancelar/reanudar y galería |
| Salidas | render, resolución/FPS, WAV, stems, datos, preset y paquete reproducible |

Cada parámetro registrado debe tener esquema con tipo, rango, unidad, default, ayuda, dependencia, costo y política de aplicación: inmediata, próxima frontera de bloque, reinicio del estado, recomputación o reentrenamiento. La UI distingue valor solicitado de aplicado. Undo/redo, diff entre presets, reset de sección y snapshots. No exponer variables internas sin significado operativo.

La promesa de no tocar código cubre composición y configuración de algoritmos implementados. Un método matemático nuevo requiere implementar un plugin; su esquema genera sus controles, evitando rehacer la UI. No ejecutar Python arbitrario desde un campo de texto.

## 6. Relojes, audio y reproducción

Separar tiempo fuente del video, tiempo de procesamiento y tiempo de reproducción. Derivar velocidad con PTS del video, no con duración de inferencia. Preservar VFR y gaps reales. Un único planificador relaciona tiempo fuente con índices de muestra.

Primer modo obligatorio: síntesis continua en tiempo real, modificable desde web sin detener fuente ni esperar un render. En el host local, conservar inicialmente salida nativa de Shaper y enviar al navegador estado de síntesis/stems sincronizados para el Lissajous existente. La web es la superficie de control y visualización; no es obligatorio transportar audio por navegador. Si se agrega escucha en navegador, usar buffers acotados/AudioWorklet y evitar doble salida. Render offline es una opción posterior con el mismo núcleo DSP.

Aplicar parámetros ligeros en la siguiente frontera de control/bloque; rampas de transición configurables evitan clics sin añadir un suavizado corporal oculto. Compilar ruteos fuera del hilo de audio y conmutar atómicamente. Ante cambios estructurales, preservar estados compatibles, precalentar nuevos y liberar voces retiradas. Modelos con ajuste pesado preparan una versión candidata en segundo plano. La UI declara qué métodos pueden operar causalmente en vivo y cuáles necesitan preparación o son exclusivamente retrospectivos.

Extraer de Shaper una función de render por bloques comprobable, separada de dispositivo y reloj de pared. Registrar eventos de control y estado de voces; el limitador pertenece al camino final común. El callback no realiza inferencia, I/O pesado ni compilación del grafo.

Seek de exploración: reiniciar historial local con warmup explícito, sin confundir el salto de video con un impulso corporal. Modo de replay exacto opcional: checkpoints de estado y preroll desde checkpoint; restaurar filtros, estimadores, normalización adaptativa, eventos, fase, envelopes y medio. Loop con dos modos declarados: reinicio de estado o continuidad sonora; en ambos reiniciar derivadas en la discontinuidad de la fuente para evitar un Jpsh! ficticio. Cambio de archivo/cámara conserva preset pero reinicia identidad, historia y calibración según política visible. A/B usa idéntico intervalo fuente y estados iniciales conocidos; compensación de loudness opcional y registrada.

Cámara lenta tiene dos modalidades distintas: escuchar el render existente a otra velocidad, o recalcular como si el gesto ocurriera más lento. La segunda transforma el tiempo de la dinámica; nunca activarla implícitamente. Una vista silenciosa frame-by-frame no obliga a sintetizar audio estático.

## 7. Familias de representación y predicción

Implementar por etapas, como plugins seleccionables:

A. Baselines: posición constante, velocidad constante, controlador actual congelado; conservar sus particularidades, sin corregirlo silenciosamente durante la comparación.

B. Relacional Anni v0: I/R/A, referencias instantánea e histórica separadas, ángulo firmado, ruido estimado, Δu y Δu/Δt explícitos; categorías sin modo/sin contribución. R no es independiente de I en 2D. Añadir rotación uniforme y FPS variable a sus cuatro ejemplos.

C. Geometría corporal: vectores de segmentos, ángulos relativos, distancias normalizadas, rotación global y configuración interna separadas. Predictor angular; gaps y singularidades marcados.

D. Modos colectivos: PCA/SVD en variables de escala declarada y rango fijo para empezar. Representar el subespacio en Gr(k,D), comparar por ángulos principales/proyectores. Conservar coordenadas/amplitudes además del subespacio. Alinear bases para evitar saltos de signo/permutaciones que se oirían como cambios ficticios. Estabilidad del rango y degeneraciones deben ser visibles.

E. Dinámica colectiva: modelos lineales con retardos y DMD regularizada, frente a baselines. Fase/coherencia solo donde existan ciclos y soporte temporal; no estimar un ratio estable a partir de un impulso aislado. DMD/Koopman es una aproximación identificada, no descubrimiento automático de leyes universales.

F. Activación Jpsh!: marcas humanas iniciales y detector cinemático opcional. Comparar predicción de extremidades a partir de historia propia, cuerpo completo, core e historia, y referencias alternativas. Ablaciones sin core y lags alterados. Solo información previa al horizonte de predicción. Residuos de predicción no se llaman energía perdida ni carga correctiva física.

HIT guía preguntas sobre recurrencia informativa, activación y preservación de relaciones. No imponer ratios simples ni positividad grassmanniana como criterio de éxito. La rama de Grassmannianos no presupone que un subespacio de movimiento esté en su parte positiva o sea un amplituedro.

## 8. Sonificación y visualización: opciones comparables

Dos familias de sonificación: mapeo de parámetros (señales→pitch/gain/phase/pan/envelope) y modelo excitado (impulso y estado corporal excitan resonadores acoplados). La segunda operacionaliza directamente el interrogante Jpsh!: qué parte de la respuesta viene del impulso y qué parte de la organización del medio.

Un prototipo de resonadores tendrá topología, frecuencias, acoples y amortiguamiento visibles. Sus parámetros expresan un instrumento virtual; no se presentan como identificación biomecánica del cuerpo. Mantener la excitación corporal y la respuesta autónoma del instrumento como tracks distintos.

Separar fase corporal, fase del oscilador sonoro y fase introducida para visualizar. Especificar cómo traducimos escalas temporales de movimiento a frecuencias audibles: transposición de relaciones, modulación de portadoras o audificación acelerada son modalidades diferentes.

El modo principal preservará el Lissajous polifónico actual, con todos los armónicos activos y sus aportes sincronizados. Auditar su fórmula y fijar fixtures de equivalencia antes de migrarlo. Ofrecer inspección/mute/solo por voz y composición completa sin reducirla a un par de armónicos. Las reglas de proyección visual serán configurables a partir de ese baseline, conservando su preset original.

Como instrumento complementario, el osciloscopio XY de mezcla tendrá dos buses asignables. Si L=R, la diagonal es el resultado correcto en ese modo; no extrapolar esa limitación al visualizador polifónico. El modo mono-retardo o Hilbert será explícito, con su propio retardo/lookahead. Mostrar escalas físicas de amplitud junto a normalización visual opcional.

Medio virtual inicial: membrana rectangular idealizada de bordes fijos con expansión modal. Forma de trabajo: q''_j + 2 ζ_j ω_j q'_j + ω_j² q_j = Σ B_jc s_c(t); campo w(r,t)=Σ q_j(t)φ_j(r). Los canales excitan posiciones definidas. Elegir paso de integración estable o actualización modal exacta por bloque y validar con excitaciones simples. La figura nodal estimada no equivale a la dinámica de granos ni a líquido.

Las visualizaciones visualmente parecidas pueden provenir de señales distintas. Conservar orden temporal, escalas y espectro; no equiparar semejanza de imagen con invertibilidad.

## 9. Cuerda y 3D

El primer recorrido funciona con cuerpo 2D y video original de la cuerda visible. Añadir anotación asistida de cuerda en fragmentos seleccionados: máscara y, si es confiable, curva central/extremos. Segmentar una cuerda fina con blur/cruces es una investigación propia; SAM 2 es candidato, no garantía. Validar a mano algunos cuadros antes de usar sus derivados. El cuerpo no sustituye la cuerda como dato.

3D monocular: benchmark acotado de GVHMR y un candidato reciente con disponibilidad práctica comprobada (por ejemplo OnlineHMR), sobre giros, oclusiones, pies y muñecas. Etiquetar estimado, comprobar reproyección, longitudes y continuidad; ni un mesh plausible ni bajo error de reproyección demuestran profundidad correcta. No congelar dependencias pesadas antes del ensayo de viabilidad local.

3D medido/reconstruido: fase posterior con cámaras sincronizadas, calibración intrínseca/extrínseca, escala y validación independiente. Elegir cantidad/posiciones según oclusiones observadas. IMUs en torso/pelvis/manos solo si resuelven una incertidumbre concreta; medir sincronización, deriva y desalineación. Fuerza/tensión requerirán sensores propios si la pregunta pasa a energía o transmisión mecánica.

Mantener las mismas representaciones aguas abajo con declaraciones de dimensión y marco; las operaciones 3D se habilitan únicamente cuando el proveedor entrega esos datos.

## 10. Evaluación opcional: comparar sin producir circularidad

Primero pruebas sintéticas para exactitud; luego gestos reales para exploración. Separar entrenamiento/calibración de evaluación por toma o sesión, con margen temporal mayor que ventanas/lags/horizonte. Al principio estudiamos a una persona: no inferir generalización entre cuerpos.

Evaluar tres objetivos por separado:

- Predicción: error a varios horizontes, cobertura/validez y desempeño por gesto; convertir predicciones al mismo espacio observable cuando sea posible. No comparar directamente errores con unidades distintas.
- Experiencia: correspondencia percibida, legibilidad del Jpsh!, agencia evocada, interés musical, confusión. Orden ciego opcional, niveles controlados y anotaciones con contexto.
- Transferencia: clasificar o recuperar atributos del gesto desde audio o imagen sonora en tomas reservadas. Controles con tiempo desplazado, relaciones barajadas conservando estadísticas marginales y loudness, y sin core. Decodificar algo codificado explícitamente verifica el canal; no demuestra un principio natural independiente.

Un predictor no recibe suavizado con futuro ni normalización ajustada sobre evaluación. La rama retrospectiva está permitida para exploración y marcada de forma visible. No usar DTW para esconder desfases en pruebas causales; si se ofrece para comparar forma, informar también el desfase original.

Explorar muchos presets implica selección: guardar el historial de barridos y congelar candidatos antes del conjunto reservado. No inventar un único score global de consonancia/eficacia.

## 11. Entregas y criterios de salida

| Hito | Construcción | Evidencia para pasar |
|---|---|---|
| 0 — Integración y tiempo | Identificar visualizador polifónico actual, archivo/cámara, timestamps y baseline del stack | Ruta existente comprendida y preservada; una fuente disponible basta para empezar |
| 1 — Instrumento explorable en vivo | Archivo en loop o cámara, controles web en caliente, Shaper continuo, Lissajous polifónico y presets portables | Fuente sigue corriendo al variar controles; guardar y recuperar tras reinicio; mismo preset funciona en otro video/cámara sin historia heredada; ninguna grabación/render previo requerido |
| 2 — Mesa configurable | Registro de nodos, matriz/ruteos en caliente, macros, undo, variantes, segundo cliente y captura opcional video+audio | Cambiar modalidad/ruteo sin código ni detener fuente; transiciones estables; grabación opcional sin interrumpir audio; parámetros soportados accesibles desde web |
| 3 — Comparación relacional | Anni, angular, ejemplos discriminantes, anotaciones Jpsh!, barridos acotados | Misma toma/mismas condiciones; resultados y contraejemplos visibles; ruido/gaps no se convierten en eventos ficticios |
| 4 — Organización colectiva | SVD/Grassmann, modelos con retardos/DMD, core y ablaciones, resonadores excitables | Comparación fuera de ajuste, continuidad de base modal, incertidumbre y errores; no confundir compresión con harmonicidad |
| 5 — Medio y transferencia | Membrana modal, evaluación desde sonido/imagen, protocolo de cuerda y piloto 3D en ramas independientes | Validación del medio con señales conocidas; comparación reservada; límites de cuerda/3D documentados |
| 6 — Captura física | Multivista/IMUs o medio cimático real según hallazgos | Calibración, sincronización y comparación físico/virtual; integración por mismos contratos |

Hitos 1 y 2 definen el laboratorio mínimo realmente utilizable. Hitos posteriores agregan instrumentos de investigación sin rehacer la mesa. Cada entrega incluye UI, preset de ejemplo, caso reproducible, prueba de aceptación y explicación de límites; no entregar algoritmos que solo se puedan usar por CLI.

Objetivos iniciales a medir en este host, no promesas: UI/transportes responsivos durante trabajos; cambio de control a efecto sonoro idealmente menor de 50 ms, sin render previo. Medir por separado latencia movimiento→sonido, control→sonido y sonido→imagen, con p50/p95 y jitter; buscar movimiento→sonido menor de 100 ms y revisar con escucha corporal. Estos son objetivos iniciales, no garantía de sensación satisfactoria. Ante sobrecarga reducir calidad visual o costo de percepción de forma visible; nunca acumular cuadros viejos ni detener el audio por un trabajo de análisis. Modelos que no alcancen el presupuesto no se etiquetan como live. A/V dentro de un frame de la fuente más latencia de dispositivo medida. Exactitud numérica con tolerancias publicadas; identidad bit a bit solo en entorno y semillas controlados. Colas con progreso, cancelación y recuperación; CPU fallback cuando corresponda.

Pruebas de ingeniería esenciales: timestamps VFR y derivados, sin pérdidas offline, seek versus replay desde inicio, restauración de fases, PCM escuchado/exportado/visualizado, cambios atómicos, cache, missingness, fugas de futuro y fixtures geométricos. End-to-end de la UI cubre el recorrido completo. No hacer microtests de cada slider que dupliquen el esquema.

### Captura opcional

Botón Grabar/detener para conservar fuente de video + audio generado y, opcionalmente, composición con Lissajous. Guardar eventos de control y preset inicial junto al clip cuando se requiera reproducción: una sesión con controles cambiantes no queda descrita por el preset final. La escritura/codificación corre separada del audio; informar drops o límites de almacenamiento sin trabar el instrumento. Grabar no requiere pasar a un modo distinto ni es condición para guardar presets. Un buffer de «guardar los últimos segundos» puede agregarse después, activado explícitamente por su costo de memoria/captura.

## 12. Riesgos y decisiones que merecen atención temprana

- Cuerda rápida y oclusión pueden dominar la calidad: ensayar clips antes de elegir modelos.
- Captura monocular limita lo que podemos afirmar; la UI debe mostrar esa incertidumbre sin bloquear exploración.
- Un sonificador puede crear la recurrencia que luego detectamos: separar invariantes presentes en el movimiento de restricciones agregadas por síntesis.
- Un subespacio de baja dimensión puede provenir del filtro o de la tarea; comparar filtros y controles.
- El recorrido Jpsh! puede ser distribuido o comenzar fuera del core: incluir alternativas desde el diseño.
- En OSC actual no hay garantía de control sample-accurate: el replay de referencia debe programar eventos internamente por tiempo, conservando OSC para la integración live.
- Los cambios de código locales y estados adaptativos son parte de la procedencia, no detalles prescindibles.
- No conocemos aún el corpus ni costo local de los modelos nuevos. Hito 0 determina tamaño/tiempos reales y permite presupuestar los siguientes.

## 13. Fuentes que orientan decisiones (consulta 2026-09-29)

Selección de líneas relevantes, no revisión sistemática ni afirmación de un único estado del arte:

- Sonificación por parámetros y por modelos: The Sonification Handbook, capítulos 15–16, https://sonification.de/handbook/ . Ayuda a separar mapeo expresivo de respuesta de un medio virtual.
- Linke, Bader y Mores, 2023, Impulse Pattern Formulation: https://doi.org/10.1007/s12193-023-00423-8 . Referente para sonificación mediante modelos e impulsos; no adoptamos su algoritmo sin comparar.
- Tu et al., DMD: https://arxiv.org/abs/1312.0041 ; Brunton et al., Modern Koopman Theory: https://arxiv.org/abs/2102.12086 . Base para modelos colectivos temporales.
- Grassmanniano y ondas KP: https://arxiv.org/abs/1106.0023 . Puente matemático para investigación; no prueba de dinámica KP corporal.
- Geometrías positivas: https://arxiv.org/abs/1703.04541 . Evita confundir un espacio de subespacios con positividad/amplituedro.
- EMOKINE: https://doi.org/10.3758/s13428-024-02433-0 . Referencia para features transparentes y datasets/anotaciones de movimiento.
- GVHMR: https://zju3dv.github.io/gvhmr/ ; OnlineHMR: https://tsukasane.github.io/Video-OnlineHMR/ . Candidatos de reconstrucción monocular, sujetos a benchmark en rope-flow.
- SAM 2: https://ai.meta.com/research/sam2/ . Candidato de segmentación temporal asistida para cuerda.
- OpenCap: https://www.opencap.ai/ . Referente de captura y validación para futuras decisiones multivista, sin asumir su validación se transfiera a rope-flow.
- Osciloscopía XY: https://www.tek.com/en/support/faqs/how-do-i-utilize-xy-display-feature-dpo-mso-mdo4000-series-oscilloscope . Relación entre señales y Lissajous.
- Modelado de Chladni: https://www.comsol.com/model/chladni-plate-67591 . Referencia del papel del medio/bordes; no requiere adquirir COMSOL.
- HIT, capítulos 8 y 10, manuscrito local; propuesta y nota de Anni en Downloads; docs/CORE_DESIGN.md, docs/KINETIC_CONSONANCE.md y controladores locales revisados. Referencias internas son contexto de hipótesis, no evidencia experimental nueva.

## 14. Próxima decisión

La prioridad de exploración en tiempo real está confirmada. El primer trabajo de implementación será identificar y preservar el Lissajous polifónico existente, conectar archivo/cámara y construir el Hito 1. Antes de expandir algoritmos, Nicolás debe poder dejar correr la fuente, modificar libremente la respuesta, guardar una configuración que se siente bien y recuperarla sobre otro video o cámara. No volver a pedir confirmación sobre esta prioridad; ubicación de videos y detalles de hardware se resuelven al preparar las fuentes.
