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
