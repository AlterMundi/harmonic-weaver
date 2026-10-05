# Laboratorio corporal — especificación de construcción

Estado 2026-10-05: instrumento y bancos implementados en `main`; esta
especificación conserva los requisitos del programa. Consultar
[entregas y pendientes actuales](IMPLEMENTATION_STATUS.md) y [arranque](RUNNING.md).

**Antecedente resuelto (LAB-00):** el baseline local `7aaa8c0` y los cambios
sin commit se preservaron en `2089ed3`, reconciliados con `726f3bf` en `18ddec0`
e integrados mediante PR #29. Se conservaron las correcciones portables de tests.
El [inventario](BASELINE_INVENTORY.json) y la [procedencia](../LABORATORY_BASELINE.md)
describen esa recuperación; no son instrucciones para crear otra instalación.

Esta especificación y [DECISIONS](DECISIONS.md) reemplazan las decisiones
incompatibles del plan exploratorio anterior. La [agenda](../../research/laboratory/AGENDA.md)
preserva la investigación completa. No confundir el backlog con capacidades existentes.

## 1. Experiencia que entregamos

Nicolás deja correr un video de rope-flow o se mueve frente a la cámara.
Desde una web local ajusta cómo se interpreta el movimiento, qué señales
controlan qué parámetros y cómo suena y se dibuja la composición polifónica.
Otra persona puede operar una segunda ventana en la misma máquina.
Cuando algo se siente bien, guarda un preset y puede reaplicarlo sobre otra fuente.

La operación cotidiana no exige recortar, etiquetar, entrenar, registrar ni
exportar. Evaluar y publicar comparaciones será un segundo milestone. Una
configuración puede resultar expresivamente interesante sin mejorar predicción;
son preguntas diferentes y la UI no las combina en un score de «eficiencia».

Primera entrega: seis voces (caderas, hombros, rodillas, codos, tobillos,
muñecas) como preset conocido, con ruteo desacoplado. Ni PCA ni el número de
segmentos limita las voces. La matriz permite que una señal afecte muchas
voces y que muchas señales se combinen sobre un parámetro. Conservar mínimo
seis y soportar hasta 32 voces configurables dentro de la capacidad de Shaper.

## 2. Base real y territorio de implementación

- `research/movement-consonance/consonance/driver.py`: controlador actual,
  seis zonas, continuidad OSC y ciclo de voces. Su UI recibe configuración
  mediante `LiveControls`; sus ajustes locales no están todos publicados.
- `live_controls.py`, `plucks.py` y `web/` de ese directorio contienen trabajo
  local. No sobreescribir ni reconstruir desde HEAD ignorando ese estado.
- HarMoCAP: `src/harmocap/perception.py` entrega COCO-17 `(x/h,y/h,conf)`.
  No es 3D. Su webapp ya procesa videos; reutilizar percepción/identidad, pero
  auditar timestamps y filtrado antes de adoptar su salida como cache cruda.
- Shaper: `src/harmonic_shaper/audio_engine.py` posee fase/envolvente reales
  por voz. `api.py` emite estado de parámetros, que no equivale a estado del
  render. El tap de grabación está antes del limitador. Su `synth_pure.py`
  procesa otra ruta de análisis de voz: no asumir equivalencia live/offline.
- El visualizador de tines suma fasores de todas las voces en
  `beacon_daemon/ui/static/index.html:drawLissajous`. Su apariencia no es
  requisito; su composición polifónica sí. Hoy usa una fundamental visual
  fija y un punto animado por reloj de pared: no conservar esos atajos como
  si fueran medidas de fase del audio.

Repositorio propietario: AlterMundi/harmonic-weaver. Nueva aplicación bajo
`src/harmonic_weaver/lab/`, frontend `web/lab/` y launcher
`scripts/start-laboratory.sh`. HarMoCAP y Shaper cambian solo sus fronteras
cuando sea necesario. Las issues centrales enlazan PRs de repos adyacentes.
No duplicar #4 (Bands) ni #6 (hipótesis de interferencia).

Antes de tocar código, leer AGENTS de cada repo afectado y preservar el estado
local relevante: revisiones, diff y archivos nuevos usados por el baseline.
No incluir grabaciones, paths personales ni pesos en commits.

## 3. Procesos y responsabilidades

Python/FastAPI es autoridad de sesión y presets. React/TypeScript es cliente
de controles; WebGL2/Three.js dibuja. HarMoCAP realiza inferencia en un worker
separado. Shaper es el dueño único del audio/dispositivo. No introducir un
segundo sintetizador del navegador para simular su respuesta.

HTTP sirve biblioteca/importación/presets y snapshots; WebSocket transporta
estado, controles y telemetría. Las vistas reciben el último estado; un cliente
lento no frena el productor. Inferencia, escritura y compilación de grafo nunca
ocurren dentro del callback de audio. Las colas live son acotadas; el análisis
offline puede esperar y no descarta muestras.

Localhost por defecto; control LAN/autenticación remota no pertenece a v1.
El launcher comprueba puertos/dispositivos y no termina procesos ajenos.
Preservar el launcher actual como alternativa hasta validar la nueva mesa.

## 4. Contratos mínimos, unidades y tiempo

Versionar las siguientes estructuras, con fixtures pequeños de JSON y tests
que productores/consumidores puedan compartir. Publicar JSON Schema de los
formatos persistidos; no inventar un contrato OSC paralelo para cada modelo.

| Tipo | Contenido / semántica |
|---|---|
| MotionFrame | fuente/stream/persona, timestamp fuente, secuencia, marco, unidad, joints con posición/confianza/observed-held-missing; dimensión explícita |
| FeatureFrame | timestamp y tiempo de disponibilidad, valores con unidades/validez; historia/lookahead declarado por productor |
| AlgorithmDescriptor | ID/versión, entradas/salidas, controles con tipo/rango/default/unidad/ayuda, warmup, costo y causalidad |
| Preset | versión, algoritmos y parámetros, grafo/ruteos, voces, macros, visualización; sin identidad de toma ni estado dinámico |
| Calibration | referencia corporal y escala, procedencia, fecha y política de adaptación; independiente del preset |
| SessionState | fuente, posición, loop, dispositivos, revisión deseada/aplicada, estado y diagnósticos |
| SessionEvent | reloj/tiempo fuente y evento de edición, preset o marca voluntaria |
| VoiceFrame | sample index/rate, tiempo de generación, voces con IDs, freq, ganancia efectiva, fase integrada, envolvente, validez y etapa de señal |

Separar reloj fuente, inferencia, sesión y audio. Video usa PTS/timebase;
cámara usa timestamp de captura. Si falta PTS, fallback index/FPS se declara,
no se disfraza de timestamp observado. Derivadas usan tiempo fuente. En
fixtures incluir video VFR, huecos y dimensiones que no sean 16:9.

Las señales crudas no se sobrescriben. Elegir 2D cámara, relativo a pelvis,
relativo a torso y referencia fija; mantener movimiento global como canales
separados. Nunca interpretar confianza como Z. Filtros que usan futuro solo
se habilitan en modo retrospectivo y no en predicción causal.

## 5. Archivo, cache y cámara

### Archivo

La primera carga extrae tracking una sola vez y lo persiste; cada loop lee la
cache. Guardar en `<video>.weaver-cache/` cuando el backend abre un path local
escribible. Si no puede escribir allí, usar biblioteca y mostrar ubicación.
Los uploads se copian en la biblioteca con su cache. Directorio de datos
configurable (`--data-dir`; default XDG data de harmonic-weaver/lab).

Clave: hash del contenido, backend/extractor, versión/modelo/pesos, identidad,
configuración que cambia observaciones. Ruido/filtro posterior, ruteo, sonido,
visualización y nombre/path del video no invalidan percepción. La cache
incluye dimensiones, timebase, unidades, identidad y estados de observación.

Escribir nueva generación temporal y publicar manifest atómico al completar.
Checksum/inventario valida integridad. Error/cancelación no destruye una cache
válida anterior. `Reprocesar` fuerza generación nueva conservando la anterior
hasta el intercambio. Copia/rename puede reutilizar cache por hash desde índice
local. La UI distingue cache válida, construyendo, incompatible y corrupta.

La extracción es secuencial, no el capturador de «último frame» live. Permitir
cancelación y exploración de un prefijo completo mientras avanza. Reproducir
el video normal sin sonificación más allá del prefijo disponible; ofrecer
loop sobre prefijo sin llamarlo loop completo. No repetir inferencia por vuelta.

### Cámara y discontinuidades

Elegir dispositivo/persona desde web. Atraso descarta cuadros obsoletos, no
los reproduce tarde. Mostrar FPS y edad de muestra. Cambio de persona/stream,
seek y frontera de loop invalidan historial de derivadas; sonido puede usar
una liberación configurable, sin fingir continuidad del movimiento.
Pausa mantiene video y deja liberar/silenciar voces según opción visible.

## 6. Configuración viva y biblioteca

Descriptores generan controles y documentación; ningún parámetro soportado
relevante requiere editar código. Incluir fundamental, ratios libres, snap,
ganancias, fases, paneo, envelopes/plucks, smoothing, ventanas, horizontes,
modelos, pesos de señales y proyección visual. Un plugin nuevo requiere código;
componer plugins existentes no.

Ediciones llevan revisión base; conflictos entre clientes se muestran y no
pisan silenciosamente el estado. Validar/compilar fuera del tick y aplicar
una generación completa. Un parámetro continuo puede usar rampa declarada;
cambio de modelo resetea/precalienta únicamente el estado incompatible.
Si preparación falla, sigue activa la versión anterior con error visible.

Grafo DAG; feedback interno de resonadores es parte de su plugin, no un ciclo
arbitrario del ruteador. Fuentes con unidades, transformaciones explícitas,
un escritor final por destino; múltiples aportes pasan por nodo de mezcla.
Mute/solo y master son acciones claras, sin destruir los pesos originales.

Presets guardan configuración completa, defaults resueltos y versiones; no
dependen de cambios futuros del default. Guardar como, duplicar, favoritos,
importar/exportar, deshacer y restaurar. Unsupported plugin/version no se
sustituye silenciosamente. Calibración separada: política visible de nueva
calibración o reutilización explícita. Aplicar preset no traslada historia PCA,
fase temporal de la toma, identidad ni muestras antiguas.

Bitácora automática guarda solo cambios, IDs/versiones y marcas. Ningún
tracking ni audio/video live por defecto. Cache de archivo es deliberadamente
persistente porque fue solicitada. Bitácora no es suficiente para reproducir
una cámara que no fue grabada; explicarlo al exportar.

## 7. Algoritmos iniciales y límites interpretativos

Todos emiten señales separadas de su traducción sonora. El preset actual de
seis voces permanece disponible como baseline congelado y reproducible.

### Local, relacional y angular

Controlador actual y baselines posición/velocidad constante. Anni v0 implementa
velocidad relativa por segmento, historial previo, Δu, Δu/Δt, I/R y ángulo
firmado. Los denominadores bajo ruido producen «sin modo»/«sin contribución»,
no cero neutral. Comparar referencia instantánea e histórica explícitamente;
I²+R²=1 en 2D, no tratarlos como predictores independientes.

Ángulos internos y velocidades angulares con unwrap, identidad y missingness;
rotación global separada. Defaults de ventana/horizonte son exploratorios,
editables y documentados; no calibrados a eficacia fisiológica.

### Organización colectiva

Primera versión: SVD/PCA causal sobre velocidades de joints normalizadas,
ventana 2 s y hasta 3 componentes (editables). Número de voces independiente.
Datos inválidos no se convierten en ceros; bloquear estimación o restringir
al conjunto válido estable indicando cambio de soporte. No comparar directamente
subespacios en distintas listas de features sin una transformación explícita.

Calcular base con muestras previas; proyectar la contribución nueva antes de
actualizarla. Comparar subespacios mediante proyectores/ángulos principales.
Conservar amplitudes, residuos y coordenadas; alinear bases y manejar singular
values casi degenerados para no producir notas por signos/permutaciones de SVD.
No llamar armónicos a componentes PCA solo porque son pocos.

### Despliegue y eventos Jpsh!

Candidatos por región a partir de cambios cinemáticos respecto de ruido local;
umbrales, refractory y ventana editables. Marcas humanas independientes.
Permitir cero, uno o varios centros; emitir score/soporte, no un ganador obligado.

Primera estimación de propagación: antecedentes de cada región y modelo lineal
regularizado con retardos para predecir las otras, frente a historia propia.
Seleccionar lags en la ventana de entrenamiento pasada. Una atribución de
propagación basada en respuesta requiere esperar ese retardo: distinguir
evento candidato inmediato de evidencia posterior. «Centro» no significa
origen causal demostrado, intención ni flujo físico de energía.

### Interferencia sobre organización previa

Emitir alineación/oposición con estado predicho, componente paralela al subespacio
y transversal, junto con magnitud y detectabilidad. Definir referencia y
ventana en el descriptor. La componente transversal es novedad geométrica;
compatibilidad solo se estima si conserva relaciones elegidas o mejora
predicción posterior. Puede quedar indeterminada. Una oposición local puede
favorecer una organización global; mostrar nivel local/colectivo.

Preset exploratorio: oposición→desvío, refuerzo→recuperación de afinación,
variación compatible→fase/gain/timbre sin desafinación obligatoria. El usuario
puede invertir y recombinar toda esta relación. Continuar issue #6, sin presentarla
como resuelta por implementar un proxy.

## 8. Sonido y visualizador

Shaper renderiza; entrada causal de control y generación continua de fase.
Telemetría se captura al borde del bloque y se publica fuera del callback.
Incluir liberaciones de voz y amplitud efectiva de envolvente/normalización,
no solo target de gain. Si waveshaping/limitador añade componentes, distinguir
fasores de osciladores de visualización de PCM; no prometer identidad matemática.

Figura base `z(τ)=Σ a_i exp(j(2π f_i τ + φ_i))`. f_i real (con detune),
φ_i anclada al reloj sonoro; ventana configurable en segundos/períodos de f1.
No forzar cierre con frecuencias inconmensurables. Muestreo de curva adaptado
a frecuencia/ventana, con techo de puntos y diagnóstico de calidad.

Presentaciones: curva conjunta; componentes/fasores opcionales; historia de
figuras. Antialias, luminancia controlada, persistencia y paleta configurables.
Vista completa sobria sin ejes; inspector con escalas/tiempo. Autoencuadre no
oculta el valor de amplitud. Congelar persistencia o limpiar al perder la fuente
según setting explícito. No fingir movimiento sonoro mediante un punto movido
con reloj de pared. 3D decorativo no se presenta como reconstrucción corporal.

Dos modos de sonificación: mapeo de parámetros y, en expansión, resonadores
acoplados excitados por eventos. Reservar interfaz de plugin y registrar en
agenda; la física del resonador no se atribuye automáticamente al cuerpo.

## 9. Grabación, evaluación y sensores futuros

Captura opcional video+audio final y eventos de control; exportar composición
visual como alternativa. Escritor/codificador separado, límites y drops visibles.
No reconstruir una performance cambiante usando solamente su preset final.

Segundo milestone: presets congelados × fuentes congeladas, estados/calibración
conocidos, renderer común y manifest de hashes/versiones. Métricas por dominio,
controles temporales/relacionales, tomas reservadas y reporte de incertidumbre.
Errores en unidades diferentes no se comparan como si fueran el mismo score.

Proveedores futuros pueden añadir canales con timestamp original, mapeo de
relojes, unidad, calidad, sujeto y rol practicante/observador. No incorporar
ahora OpenBCI, IMUs ni estimación de calorías. Agenda R01–R13 los conserva con
requisitos de medición y validación; video/sonido/combinación son condiciones
futuras explícitas. El SNR depende de la señal de interés, no de borrar toda
variación inesperada.

## 10. Aceptación e integración

Objetivos iniciales medidos en el host: control→audio p95 <50 ms; movimiento→audio
p95 <100 ms como aspiración a validar con captura real. Registrar p50/p95 y
jitter por tramo; no anunciar latencia total desde FPS de inferencia. Si el
hardware no alcanza, exponer límite y priorizar el gesto reciente sobre colas.

Validaciones: cache hit/invalidación/fuerza/corrupción; timestamps VFR;
presets fuente-independientes; cambios atómicos; seek/loop/persona sin impulsos;
all voices en figura; continuidad de fase/bases; múltiples eventos; tracking
perdido; carga/cancelación sin bloquear audio; recorrido web end-to-end.

Aceptación humana: reproducir y usar cámara, cambiar parámetros y algoritmos,
guardar un hallazgo y recuperarlo en otra fuente. Marcar lo que se siente bien
y lo confuso. Las primeras pruebas humanas son parte del desarrollo, no una
validación de HIT. No exigir éxito científico para entregar el laboratorio.

## Entrega incremental posterior: comparador local v1

El primer corte de EVAL-01 se implementa como módulo de la web y CLI descrito en
[EVALUATION](EVALUATION.md): presets congelados × segmentos, runtime live compartido,
reloj lógico, reset/preroll y exportación de features/targets/métricas con soporte
común. Es opcional para operar el instrumento. No adelanta PCM offline, nuevos
sensores/3D ni evaluación científica formal. Las decisiones posteriores están en
[DECISIONS](DECISIONS.md) y la evidencia separada de escucha en [VALIDATION](VALIDATION.md).
