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
