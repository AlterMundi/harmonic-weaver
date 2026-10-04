> Actualización 2026-10-04: Nicolás autoriza integrar continuamente el trabajo
> terminado en `main`, sin acumular PRs ni instalaciones separadas. Esta decisión
> reemplaza las indicaciones históricas de «sin merge automático» de este documento.
> Se usa `~/Projects/harmonic-weaver` y el arranque habitual 8765/8085.

# Próxima iteración: instrumento y contraste independiente

2026-09-29. El goal principal se ejecutó en la segunda iteración: consultar
[EVALUATION](EVALUATION.md), [VALIDATION](VALIDATION.md) y [RUNNING](RUNNING.md).
Las secciones siguientes conservan el alcance y los pendientes; no asignan
trabajo automáticamente a otra persona.
Programa #7; continuidad de LAB-08, EVAL #18 y agenda R01–R13.

## Estado que debe preservarse

Base revisada: Weaver feat/laboratory-live, commit 0b9766a (PR #30, sobre #29);
Shaper feat/laboratory-telemetry, 8d6de86 (PR #2); HarMoCAP baseline PR #1.
Verificar los heads al empezar. Main todavía no contiene necesariamente todo.
Worktrees originales con cambios de Nicolás quedan intactos.

Nicolás aceptó la sensación de 01c, armónicos sostenidos con intensidad corporal,
y luego la del contraste temporal. No aceptó compresión que eleva todo el audio.
Realce -1..10: 0 neutral, 1 máximo previo, 10 énfasis diez veces mayor antes del
límite. Articulación 0..1 mezcla sostenido con transientes derivados de subidas;
su escucha específica aún no fue confirmada. Seis voces, afinación/ratios estables,
fases continuas. Priorizar controles existentes y explicar los defaults cambiados.

R24 por JACK; launcher documentado en RUNNING. Video local 60 s de 10:00–11:00,
tracking CPU completo, 1.800 cuadros. Ambas muñecas aún tienen pérdidas (8–10%);
confianza no acredita exactitud. Tramo 20:00–21:00 rechazado por oclusión de planta.
Todos los medios, derivados, cache y anotaciones identificables permanecen locales.
CUDA volvió a fallar también en extracción inicial: #31. Modelos no baseline
necesitan calibración, aviso añadido; aceptación auditiva pendiente: #32.

## Lectura de Sai: integrar con alcance

Revisión dirigida de SairaAsua/movimiento-armonico-investigacion, HEAD
f6b96da041bbe95e35ab865d2a07d082d2adba29. Se leyeron índices/síntesis, contratos Q/C,
causalidad, cobertura, marcos, fase y auditorías de integración relevantes.
No se afirma lectura integral de todas las fuentes primarias ni del repositorio.

Fuentes fijadas:
- [Control factorial y marginales](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/LABAN_HIT_FACTORIAL.md).
- [Predicción sin fugas](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/HIT_PREDICCION_SIN_FUGAS.md).
- [Geometría y tiempo](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/GEOMETRIA_VS_TIEMPO_TRAYECTORIA.md).
- [Cobertura y selección](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/COBERTURA_SELECCION_VIDEO.md).
- [Marcos corporales](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/CMU_MARCOS_C_CONTRASTE.md).
- [Contrato Q](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/CONTRATO_Q_LIVE_V0.md)
  y [contrato C](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/CONTRATO_C_LIVE_V0.md).
- [Auditoría histórica de Weaver](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/WEAVER_DRIVER_PRUEBA_AISLADA.md).

Aportes inmediatos: cobertura por señal y duración de gaps, razones de invalidez,
definición de marco/recorrido, separación entre tiempo fuente y disponibilidad,
controles sintéticos y comparaciones sobre exactamente el mismo soporte temporal.
Held o inválido no significa disonancia; una transición puede no admitir fase.
Parte ya existe en nuestros contratos/reset/lease: ampliar pruebas y diagnóstico,
no reemplazar el runtime por la arquitectura histórica de Beacon.

Aportes para banco: recorridos iguales con ritmos distintos; ritmo común frente a
acople; marginales igualados; observaciones segmentarias independientes; prueba
de prefijo causal y reserva por sesión. Un descriptor determinista de entradas
no agrega información sensorial: puede mejorar representación/modelado.
No confundir el R de concentración de fase de Sai con I/R/A de Anni.

Q resume componentes direccionales ponderadas por arco: no es un plano ni un
subespacio Grassmanniano. Puente propuesto por nosotros: comparar tensor completo
de direcciones, sus subespacios y sus diagonales Q, con casos degenerados y marcos
controlados. Es una línea de investigación, no equivalencia ya demostrada.
C depende del recorrido/marco; Sai documenta incluso inversión de signo.

Diferir: Q/C corporales 3D sobre video monocular, soga inferida desde muñecas,
metabolismo/eficiencia y resultados de paper. Las propuestas de Sai no validan
HIT ni una identidad cuerpo→cimática. No importar sus ganancias de bandas Beacon
como si fueran frecuencias de osciladores Shaper.
La auditoría de Sai usa Weaver a4ca91e3 y HarMoCAP bdeebbf5: reproducir antes de
declarar un bug vigente. En particular, distingue fallo del receptor de ejemplo
HarMoCAP de un driver Weaver que sí superó ese control.

Reproducción local independiente: cinco scripts, todos exit 0, Python estándar:
laban_hit_marginales_igualados.py (R=1 frente a 0.077246, fase de eventos R=1 en ambos);
prediccion_relacional_sintetica.py (ventaja frente a lineal pero no frente a la
base no lineal adecuada; guard de futuro y soporte desigual);
geometria_tiempo_sintetica.py (tiempo 0.5/0.32461, arco ~0.5 en ambos);
proyeccion_2d_ambigua.py (misma imagen, recorridos 3D 2.513266/5.690778);
fase_causal_sintetica.py (error -36 grados en aceleración, warmup/expired).
No se reprodujo el banco CMU completo ni se validaron cámaras/estética.

## Goal CompAII: segunda iteración local

Entregar una segunda iteración usable del laboratorio y un primer comparador
reproducible, manteniendo la exploración libre como operación principal.

1. Preservar estado/presets y una referencia explícita de 01c aceptada. Completar
   aceptación de realce/transientes con pruebas de continuidad y controles A/B
   sobre misma fuente, posición y nivel. Corregir el residual de pitch/fase
   saturado como opción separada, nunca reactivarlo en 01c sin elección humana.
2. Hacer legible por qué un modelo suena o no: falta calibración, calentamiento,
   tracking insuficiente, señal no aplicable, mapeo silenciado o audio desconectado.
   Resolver #32 con recorrido de calibración sencillo y prueba de cada modelo.
   No inventar escala ni reutilizar la de otro cuerpo/fuente silenciosamente.
3. Incorporar diagnóstico temporal de cobertura por articulación/señal, gaps y
   segmentos descartados; conservar el registro de intentos. No seleccionar por
   movimiento visual solamente ni presentar confianza como precisión.
   Robustecer #31 con recuperación explícita y reproducible, identidad de cache
   por backend y preservación de generaciones válidas. No repetir GPU fallida sin
   diagnóstico; CPU es una alternativa utilizable.
4. Primer corte de EVAL #18: presets congelados × segmentos de cache, usando el
   mismo núcleo causal live, reloj determinista, resets/preroll explícitos,
   manifest con hashes/versiones/calibración/semillas y comparación sobre soporte
   común. Exportar inicialmente features/targets/métricas/manifest; separar esta
   entrega de PCM offline, figuras renderizadas y evaluación formal restantes.
   Incluir pruebas de paridad live/replay a tiempos equivalentes y rerun.
5. Revisar la PR de Oliva como consumidor, incorporar casos pertinentes sólo
   después de revisar definiciones y resultados. No bloquear el laboratorio si
   ese aporte todavía no existe.

Actualización 2026-10-03: #36 y su extensión Fourier #97 están incorporadas en
la rama `feat/sai-fourier-integration`, sobre #96, sin merge automático.
Los generadores compartidos/independientes y el banco permanecen en research;
no son filtros live ni cambian el instrumento. Véase
[informe de Oliva](../../research/laboratory/sai_bridge/FOURIER_REPORT.md) y
[evidencia de integración](VALIDATION.md#saioliva-integración-del-banco-fourier--2026-10-03).
El siguiente uso pertinente es un contraste sobre canales corporales regulares
con soporte/missingness declarados, antes de atribuir cambios de I a acoplamiento.
No hace falta otra ronda de revisión ni igualdad de digest entre entornos.

Aceptación: un comando de arranque; mismo preset entre fuentes; explicación
visible de silencios; sesión local de 60 s con seis voces y sin reataques por
actualización; pruebas de resets/cache/audio/UI pertinentes; corrida repetible
de dos presets × dos fuentes sintéticas o locales con manifest y límites.
La escucha humana se informa sólo cuando Nicolás la realiza.
Publicar ramas/PRs y evidencia; no merge automático ni publicar medios privados.

Propiedad de cambios: runtime, UI, routing/presets, store/contracts, percepción/
cache e integración Shaper; comparador bajo src/harmonic_weaver/lab/evaluation/
y tests de integración. Durante trabajo paralelo no editar los directorios
reservados a Oliva abajo. Cambios en contratos se versionan con compatibilidad.
Grabación opcional #17, PCM offline completo, sensores/3D, paper y agenda restante
siguen pendientes explícitos, no se pierden ni bloquean este corte.

## Goal Oliva: banco independiente de contraste

Preparar y publicar un banco reproducible para contrastar organización espacial
y temporal, cruzando Sai con Anni/HIT y nuestros modelos actuales. Entregar código,
fixtures, pruebas y un informe; no sólo otra revisión bibliográfica.

Partir del head de PR #30 en rama/worktree propio. Leer SPEC, DECISIONS, VALIDATION,
AGENDA, propuestas originales de Anni y esta nota. Fijar SHA de Sai y de Weaver.
No necesitar videos privados ni nuevos sensores; usar datos sintéticos. Datos
públicos externos, si se agregan, deben tener procedencia y términos verificados.

1. Reproducir los cinco bancos listados y registrar comandos/resultados/versiones.
   Adaptar mediante implementación atribuida o fixtures con procedencia; revisar
   términos antes de redistribuir código ajeno. No copiar el repo completo.
2. Producir pares controlados: misma geometría/distinto ritmo; mismo movimiento
   marginal/distinta relación; fase compartida artificial; ritmo común sin acople;
   traslación/rotación/marco móvil; ruido/gaps/identidad/seek; plano degenerado.
   Ground truth 3D sintético separado de observación 2D; nunca levantar z=0 y
   presentarlo como reconstrucción corporal. No asumir máximo R = mejor gesto.
3. Emitir MotionFrame 2D compatibles con contratos existentes y un manifest de
   verdad sintética separado. Ejecutar local/relational/angular/collective por
   adaptadores de sólo lectura. Comparar señales y validez antes del audio.
   Distinguir concentración de fase de Sai, I/R/A de Anni, subespacios y Q.
4. Comprobar prefijo causal, soporte idéntico, disponibilidad, unidades, precisión
   numérica declarada y reproducibilidad. Comparar predicción contra persistencia/
   velocidad constante y una base no lineal apropiada cuando se afirme utilidad
   relacional; evitar ventajas producidas por selección o capacidad desigual.
5. Entregar matriz de resultados/contraejemplos: qué distingue cada descriptor,
   qué confunde, qué no puede medir esta captura. Proponer después un puente
   tensor direccional/subespacio/Q, sin imponerlo como nuevo algoritmo live.

Fronteras exclusivas: research/laboratory/sai_bridge/ y
tests/research/test_sai_bridge_*.py. Dentro pueden vivir generadores, fixtures
pequeños, adaptadores, manifest y README con comando único. No editar runtime,
modelos productivos, contratos, presets, UI, cache, launcher, Shaper ni HarMoCAP.
Importar APIs existentes sin cambiarlas; si falta algo, documentar propuesta de
interfaz o bug con reproducción, sin ampliar scope unilateralmente.

Aceptación: un comando genera resultados deterministas; fixtures validadas con
contratos fijados; al menos un control negativo y un contraejemplo informativo;
tests de causalidad/missingness; informe separa esperado, observado, límite y
propuesta. PR revisable contra base declarada, sin datos privados ni afirmación
de validación humana/HIT. No depende del comparador que CompAII aún construirá.

## Siguiente aporte de Oliva: Fourier corporal — 2026-10-03

Nicolás confirmó que le pasó el goal para extender #97 a trayectorias corporales
congeladas: bloques por persona/articulaciones, continuidad y muestreo regular
explícitos; sin rellenar gaps, calibración inventada ni resampling silencioso.
Original/fases compartidas/independientes sobre igual soporte; diagnóstico de
longitudes de segmentos/plausibilidad para separar cambios geométricos de los
descriptores. Fixtures sintéticas y contraejemplos, comando/JSON reproducibles;
datos corporales privados no requeridos para desarrollar.

Reservados para ese aporte: `research/laboratory/sai_bridge/body_fourier.py`,
`BODY_FOURIER_REPORT.md`, nuevas fixtures dentro del bridge y
`tests/research/test_sai_bridge_body_fourier*.py`. Mantener funciones existentes
compatibles. CompAII implementa servicio/UI en `src/` y `laboratory-ui/`, sin
editar esos archivos reservados ni esperar la entrega para avanzar. Encomienda
confirmada por Nicolás; no se infiere que el trabajo esté ejecutándose ni terminado.

### Aporte recibido e incorporado: Fourier corporal (#107)

La PR de Oliva #107, head f424981, fue revisada como consumidor e incorporada
por cherry-pick con autoría preservada sobre la pila actual (#108). No se
modificaron sus cinco archivos reservados; no hay merge automático ni cambios
de runtime. 58 tests del bridge pasan y el comando completo ejecuta contra
los imports actuales. Procedencia efectiva identifica nueve productores del
checkout integrado, separada de la referencia histórica #98.

Retiene 800/910 frames de upper_body y 128/128 del control one_scalar, con
exclusiones explicadas. Original/shared/independent se puntúan sobre la misma
intersección observada por descriptor. No valida poses humanas: todas las
fixtures de esta verificación son sintéticas. Preservar el espectro cruzado
no conserva necesariamente longitudes articuladas ni descriptores no lineales.

Siguiente integración de software: servicio/UI consumidor en src/ y
laboratory-ui/, usando prepare_blocks/control_frames/compare_blocks sobre
MotionFrames congelados. Selección, Hz/tolerancias, unidades/escala/procedencia,
semillas y preset descriptivo deben ser explícitos. Mostrar cobertura, causas
de exclusión, soporte común y diagnóstico geométrico junto a spectra/resultados.
Nunca usar FFT de bloque completo como filtro causal de la operación live.
No inventar calibración ni aplicar controles a tracking/audio en producción.

El contraste sintético de geometría restringida/espacio angular propuesto por
Oliva queda como investigación posterior, midiendo su trade-off espectral; no
se atribuyen cambios de descriptores únicamente a relaciones. Sin nuevo encargo
ni mensajes a personas por esta incorporación.

### Consumidor Fourier corporal de biblioteca — 2026-10-03

Nueva rama implementa worker/API/UI en src/ y laboratory-ui/ sin modificar
archivos reservados del bridge. Usa spatial_segment para congelar una generación
completa en memoria: no reabre/copia el video ni recalcula tracking. Preparación
es rápida y separada del cálculo cancelable. request.json/input.json contienen
selección y MotionFrames privados; result/manifest conservan cobertura, espectros,
longitudes, soporte común por descriptor y productores efectivos. Todo local.

En Investigación → Sai–Oliva · Fourier corporal congelado: Actualizar fuentes,
elegir fuente/persona, intervalo y ajustes JSON. Completar scale y
scale_provenance; declarar sample_hz, canales [COCO-17, x/y], tolerancias, semillas
y preset descriptivo con plucks desactivados. Preparar muestra exclusiones y
bloques; Correr usa su propio snapshot vigente, no una preparación vieja.
Abrir muestra condición/descriptor sobre soporte común, espectros y geometría
al lado. Ausencia de soporte queda como Sin soporte, nunca cero.

Descargar/importar ajustes valida Settings y permite portabilidad de métodos;
importar limpia persona y escala/procedencia, y no inicia el cálculo. Escala/procedencia
son declaraciones explícitas del análisis, no calibración recuperada ni inferida.
No se modifica instrumento, fuente, tracking o síntesis. Hasta 4800 frames y
14400 frames × semillas, con 1–4 semillas; el segmento de biblioteca admite
hasta 120 segundos. PTS irregulares/tolerancias pueden dejar cero bloques: se
explica en preparación sin rellenar datos. 3D se excluye explícitamente.

Persistencia conserva entradas/manifests y descargas verifican integridad sin
recalcular el banco. Cancelación/cierre afectan sólo procesos propios. La fuente
es una generación en memoria; no prueba integridad actual de video/cache en
disco. Backend verificado con tracking corporal real desde cache local, sin
reprocesamiento. Recorrido web de producción con cache real verificado (audio desconectado).
Pendiente: feedback humano, instalación de la pila; contraste geométrico restringido y trabajo científico independiente.


La preparación muestra el bloque descartado más largo para ayudar a distinguir
un mínimo de longitud excesivo de articulaciones sin soporte. Con tracking real,
la selección de canales y un mínimo explícito distinto permitieron obtener
bloques válidos donde el ajuste inicial no los tenía; defaults conservados.
La evidencia local y sus límites están en VALIDATION.md. Datos privados quedan
fuera de GitHub. La investigación geométrica restringida de Oliva puede avanzar
sin cambiar este consumidor ni el instrumento cotidiano.


La UI limpia escala/procedencia al cambiar fuente o persona, conservando método;
una edición JSON incompleta no se pierde al intentar cambiar selección. El
recorrido web real del consumidor está verificado, no la escucha ni la apertura
física de dispositivos. Ver VALIDATION.md y RUNNING.md.


### EVAL #18 · continuación por corridas completas — 2026-10-03

Web/API/CLI permiten presupuesto por tanda y continuación de matriz congelada,
sin repetir corridas completas ni transportar estado de otra corrida. Ver
EVALUATION.md/VALIDATION.md: pruebas y contraste corporal local con PCM pasan.
Presupuesto mide corridas, no tiempo/recursos internos; cambios de método/entradas
requieren corrida nueva. Publicación seleccionada con revisión de privacidad,
sincronía física y feedback humano siguen pendientes concretos. Los datos
corporales permanecen locales; no afecta el bridge reservado ni los defaults.


### EVAL #18 · paquete seleccionable — 2026-10-03

Implementados selector de corridas/contenidos, resumen sin nombres/rutas/identidad,
preferencias portables, preview y writer ZIP propio. Ver EVALUATION/VALIDATION:
pruebas y contraste local con resultados corporales guardados. Conserva soporte
común original; no infiere nueva intersección desde los presets exportados.

La preparación de archivo local está cubierta; publicación externa, corpus con
inputs públicos/consentidos, protocolos/feedback humanos y medición física siguen
pendientes. Un resumen sin IDs sigue pudiendo contener resultados sensibles.
Ningún video/tracking se copia al paquete ni se publica automáticamente.
