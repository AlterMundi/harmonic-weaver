# R06: banco inicial de activación

Pregunta preservada en #19: comparar perturbaciones racionales, phi, otras
irracionales y aleatorias sobre un medio definido, sin asumir privilegio de phi.
Este corte implementa un banco sintético sobre los resonadores complejos R05.
No es todavía un experimento corporal ni una reproducción del capítulo HIT.

Cuatro calendarios de impulsos reales idénticos: grilla uniforme racional,
partes fraccionarias de k/phi y k*(sqrt(2)-1), y posiciones uniformes con semilla.
Todos incluyen un impulso inicial en cero, igual número, vector, norma de
entrada y ventana de excitación. Medio y estado inicial cero son idénticos.
Los calendarios se cuantizan a muestras y se ordenan; colisiones se rechazan.
Todos los tiempos digitales resultantes son racionales: los nombres designan
la construcción del calendario, no una perturbación exactamente irracional.
La condición racional usa aritmética entera, evitando errores floor de floats.

Controles: medio R05 completo, número de eventos, ventana, cola, intensidad,
semilla, bloque y stride del trace. Métricas sobre TODAS las muestras: RMS/pico
crudo, norma final del estado e integral temporal de norma; RMS de cola separado.
El trace está decimado y conserva además eventos/final. Límite 14400 puntos por
condición; cálculo por bloques sin almacenar PCM completo. La norma interna no
es energía física. Igual norma de entrada no iguala clustering, espectro, pico,
loudness ni dificultad de la tarea; las diferencias dependen del medio elegido.
No hay ranking de calidad, p-values, escucha ni afirmación de eficacia HIT.

Desde harmonic-weaver-dev, con una carpeta de salida nueva:

```bash
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.activation_bank --request research/laboratory/r06_activation/reference.json --output /tmp/r06-new-run
```

Entrega request normalizado, result y manifest con hashes de input/output,
código y Python/NumPy/SciPy. No sobrescribe una corrida existente. Tres tests
cubren calendarios/cantidad/semilla, dosis igual, repetición, particiones,
contratos/colisiones y persistencia idéntica. CLI de referencia ejecutado.

Pendientes explícitos antes de considerarlo laboratorio usable: worker con
lock/cancelación/restauración/commit verificado, API y mesa web con todos estos
controles/preset portable, verificador de artefactos, bancos con múltiples medios,
contrastes temporales más equivalentes, hipótesis/observables HIT definidos y
protocolo físico/humano cuando corresponda. El usuario no debe editar código
para explorar cuando se complete la integración. No sustituye R01, Grassmannianos,
activación corporal ni el instrumento live aceptado.

R06 — worker/verificador/service (2026-10-01): ActivationService conserva el
lifecycle propio compartido (un worker activo por instancia, no lock global).
Valida settings/calendarios antes de congelar request; worker tiene flock,
manifest running, cálculo interno y verificación antes de promover result.
Rehash de input/result después de promoción, destino existente rechazado y
manifest completo atómico. Failed/interrupted no se descargan; cancelación sólo
alcanza procesos propios y restauración no relanza trabajos.

activation_artifacts.verify lee archivos regulares, compara hashes antes/después,
request/settings, clock, calendarios, dosis, inventario/tipos de métricas y
soporte/tiempos del trace. NO rerenderiza métricas ni autentica su autoría: datos
positivos falsificados con hashes reescritos no constituyen evidencia confiable.
El verificador es un contrato de integridad local, no custodia firmada ni prueba
HIT. Descargas verifican además del hash; manifest diagnóstico accesible aunque
la corrida no termine. API/UI/presets y controles ampliados siguen pendientes.

R06 — API/UI portable (2026-10-01): pestaña Investigación integra ActivationPanel.
Todos los campos del medio/calendario/cálculo editables, preset schema1 validado,
import sin ejecución, worker/cancelación, artefactos verificados y tabla/trace.
Default del backend, sin duplicar otro modelo en frontend. worker_active cubre
intervalo entre manifest completo y salida del proceso para no iniciar otro.
16 tests + Chrome configuración/repetición/restauración/tabla/trace y build pasan.
Sustituye pendientes API/UI/preset de entradas anteriores. Quedan ampliación de
bancos/controles, observables HIT definidos y protocolos físicos/humanos.

R06 — medios como control (2026-10-01): medium_controls opcional (hasta4),
damping/coupling/grafo variables con portadoras/clock preservados. Mismos eventos,
dosis y cero inicial; condiciones y diferencias control−base explícitas.
UI/presets/tabla/trace y verificador compatibles; controles desactivados por
defecto y campo omitido preservan formato previo. 21 tests + Chrome real y build
pasan. Control idéntico replica base; diferencias no indican efficacy/HIT.
Referencia anterior verificable. Pendientes controles temporales más comparables,
múltiples semillas como banco, hipótesis/observables y protocolos físicos/humanos.

R06 — permutación temporal con gaps preservados (2026-10-01): interval_shuffle
opcional genera cuatro surrogates seeded, sin alterar el stream random original.
Preserva multiset exacto de gaps, dosis, count, primer/último evento y clock;
no conserva espectro/autocorrelación de orden superior. No condiciona RNG para
forzar diferencias; grilla uniforme puede ser idéntica. UI/preset/tabla/selector
incluyen ocho condiciones y funcionan con medium_controls. Verificador reconstruye
calendarios y soporte. Campo false omitido conserva formato anterior.
Pendientes bancos de múltiples semillas, controles de fase/espectro cuando se
definan observables, hipótesis HIT explícitas y protocolos físicos/humanos.

R06 — banco de semillas explícitas (2026-10-01): replicate_seeds opcional,
1–8 semillas adicionales únicas y distintas de principal, congeladas en request.
Todos los calendarios validados antes de encolar; cap agregado144000 puntos.
Conserva principal y cada réplica con sus medios. Resumen descriptivo por medio/
calendario/métrica (count/mean/min/max/std_population), sin p-values; condiciones
deterministas pueden repetirse. UI checkbox/JSON/preset y selector que cambia
tablas y trace conjuntamente. 29 tests + Chrome real + build pasan. Campo None
omitido conserva formatos anteriores. Pendientes controles fase/espectro con
observable definido, hipótesis HIT y protocolos físicos/humanos.

## R06 · Fases explícitas de excitación — 2026-10-02

`phase_controls` opcional: hasta cuatro vectores, un ángulo en radianes por voz
(−1000..1000). Cada impulso real se rota por exp(i·fase) antes del paso del medio.
Se mantienen magnitudes/dosis L2, calendarios, cero inicial, portadoras y medio.
No equivale a iniciar el medio con energía ni a desplazar tiempos de eventos.
Un vector cero reproduce exactamente la base; el campo omitido mantiene formatos
y comportamiento anteriores. Fases son declaradas, no estimadas del cuerpo.

ActivationPanel ofrece checkbox/lista JSON, import/export portable, selector de
fase por resultado/semilla, tablas de diferencias frente a base cero y trazas
del medio elegido. Se cruza con medios, interval_shuffle y semillas adicionales;
phase_replicate_summary conserva el resumen descriptivo de cada fase/medio.
El límite agregado de144000 puntos incluye estos cruces para evitar bancos enormes.
Importar configuración no ejecuta ni cambia audio live.

En medio aislado la rotación por voz conserva norma de estado pero puede cambiar
RMS/pico de la mezcla; en medio acoplado las fases relativas pueden cambiar también
la respuesta interna. Las métricas distinguen composición audible de norma interna,
que sigue sin ser energía física ni eficacia corporal. No se normaliza output.

El verificador reconstruye inventario/fases/calendarios/dosis/soporte/deltas/resumen,
no rerenderiza cada métrica ni certifica autoría de valores arbitrarios rehasheados.
Controles de software sobre fixtures sintéticos: 48 tests pasan, incluido legado,
workers/API/render y siete tests nuevos; Chrome real repite dos bancos byte-idénticos,
recupera preset y selecciona fase/medio/semilla (1test,5.8s). Build pasa.
Pendientes espectro, observable/hipótesis HIT concreta y protocolos físicos/humanos.
No valida HIT ni modifica fases/ratios del instrumento cotidiano aceptado.

## R06 · Sondas de frecuencia sobre soporte completo — 2026-10-03

`spectral_probe` opcional: `frequencies_hz` (1–32, no negativas, estrictamente
crecientes y bajo Nyquist) y `window` complete/excitation/tail. Ventana rectangular
con start/stop/sample_count explícitos. Acumula todas sus muestras por bloques,
sin almacenar PCM completo ni calcular sobre el trace decimado. Máximo agregado
64000000 productos frecuencia×muestra, incluyendo calendario/medio/fase/semilla.
Cola vacía se rechaza; campo omitido conserva resultado anterior.

Para cada frecuencia: c=(1/N)Σx[n]exp(−i2πft[n]); publica real/imag/|c|².
Input es indicador unitario de eventos a n/sr; salida es mezcla después del paso,
a(n+1)/sr. Es diagnóstico de calendario/respuesta, no fuerzas ni norma/dosis de
excitación, PSD, watts, energía de banda o función de transferencia. Frecuencias
arbitrarias no son necesariamente ortogonales; sus cuadrados no se suman como
energía. Leakage y transientes de ventana permanecen explícitos.

Checkbox/config JSON/preset portable y tabla web siguen fase/medio/semilla elegidos,
con ventana/cantidad de muestras. No afectan eventos/estado/voz ni normalizan output.
Verificador reconstruye soporte/frecuencias/coeficiente del indicador y coherencia
real/imag/cuadrado; no rerenderiza el coeficiente de salida desde PCM. No confundir
integridad/contrato con resultado experimental autenticado.

Referencia pequeña, en carpeta nueva:

```bash
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.activation_bank --request research/laboratory/r06_activation/reference_spectral.json --output /tmp/r06-spectrum-new-run
```

Corrida local real de esa referencia: indicador uniforme a80Hz da|c|²=0.0001;
phi4.9176380461e-5, sqrt2 2.4513003172e-6 y random5.7079894602e-7. El indicador
uniforme a40Hz es~0, pero la mezcla de salida tiene|c|²=0.0197260309. No se
estima transferencia dividiendo esos valores: la respuesta y ventana finitas
no representan por sí solas una respuesta estacionaria aislada. No resultado HIT.

58 tests pasan, incluidos diez nuevos con señal/DC analíticos, ventanas,
particiones, ausencia de cambio de audio, cruces, corrupción, budgets y gaps de
bloques. Chrome UI/API/workers reales repite bancos byte-idénticos, importa preset
y compara tabla por fase/medio/semilla (1test,5.9s); build y CLI/verify pasan.
Pendiente: surrogates que preserven un espectro declarado, hipótesis/observable
HIT y protocolos físicos/humanos. Estas sondas no igualan espectros entre controles.

## R06 · Desplazamientos circulares por puerto — 2026-10-03

`circular_shift_controls` opcional: hasta cuatro vectores de enteros, uno por voz,
entre 0 y excitation_frames−1. Cada calendario de impulsos positivos se desplaza
por puerto módulo el bloque de excitación. Conserva número/amplitud por puerto,
dosis L2 total y periodograma completo individual. Un desplazamiento común
conserva además el espectro cruzado complejo; desplazamientos distintos pueden
alterarlo, pero no obligan a distinguir todos los calendarios periódicos.
No conserva necesariamente el espectro de la suma de puertos ni la distribución
de norma instantánea: ya no son todos impulsos simultáneos de igual norma vectorial.

Es una familia particular de fases Fourier lineales en frecuencia, no un
surrogate de fases arbitrarias. Requiere el bloque completo y envoltura: offline,
no causal. Tampoco equivale a `phase_controls` (rotación compleja constante de
cada excitación). Portadoras/ratios/medio/fases elegidas permanecen constantes;
cada control arranca desde cero, renderiza todas las muestras y conserva cola.
La salida finita puede variar por transientes y truncamiento aun cuando entrada
tenga el mismo espectro; esto no implica eficacia ni superior organización.

Checkbox Desplazamientos circulares por voz R06 añade cero/común/diferenciado;
editar vectores en JSON, guardar/importar preset y correr. Tabla distingue
error de potencia por puerto, cambio cruzado y RMS/delta de salida. Selector
Desplazamiento de traza permite inspeccionar la traza real del control, con el
medio/fase/semilla seleccionados. Se cruza con medios, fases e interval_shuffle;
retiene cada semilla. No modifica el instrumento ni sus defaults.

El verificador reconstruye calendarios/dosis/soporte y checks FFT de entrada,
con tolerancia 1e-12 para checks; no vuelve a renderizar métricas de salida.
Presupuestos agregados de trace y 64000000 bin-pair products evitan cruces enormes.
Checks usan DFT rectangular del bloque de excitación real por puerto, antes de
rotar su fase compleja; no son sondas del trace decimado ni espectros del audio.

Referencia pequeña:

```bash
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.activation_bank --request research/laboratory/r06_activation/reference_circular_shifts.json --output /tmp/r06-shifts-new-run
```

Corrida local: 400 muestras de excitación. Desplazar 100 muestras la grilla de
cuatro eventos deja entrada/salida idénticas (contraejemplo). En random, ese
desplazamiento común mantiene potencia/espectro cruzado (errores <5e-16), pero
Δ RMS salida=.0784458. Desplazamientos distintos preservan potencias (<7e-16),
cambian espectro cruzado random≈1.909 y dan Δ RMS≈.0798172. Cambios normalizados
de espectro pueden superar 1; no son scores de acoplamiento. Observaciones de
este modelo/bloque, no evidencia corporal o HIT. Esta familia satisface el
control espectral pendiente para shifts periódicos; surrogates más amplios,
hipótesis/observable y experimentos físicos/humanos siguen abiertos.
