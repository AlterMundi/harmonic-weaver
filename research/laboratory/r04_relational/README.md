# R04 — primer banco relacional sintético

Usa `RelativeMode` de producción sobre velocidades 2D sintéticas de extremos
proximal/distal. No estima fuerza ni activa sonido. Los cinco escenarios vienen
de la nota de Anni: aceleración compartida, reducción relativa, giro y frenado
distal con padre quieto/móvil. Son construcciones, no ground truth humano.

Cada escenario tiene original, rotación uniforme, inversión de ambos extremos
y adición de velocidad común. Estas tres transformaciones deberían conservar
I/R/A; no prueban oposición local favorable al conjunto. No se usa el código ni
los directorios reservados a Oliva.

```bash
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.relational_bank --request /ruta/request.json --output /ruta/nueva-corrida
```

Request JSON puede ser `{}`. Parámetros: samples (10–600, default 120), hz
(10–120, 30), history_s (.05–5, .25), noise_velocity (.0001–2, .02), noise_delta
(.0001–2, .015), max_gap_s (.05–2, .25), relation_reference (history por defecto,
o instantaneous), rotation_deg (±360, 73), common_velocity_x/y (±10, 2/−1).
No umbral calibrado se deduce de estos defaults sintéticos.

La carpeta de salida debe ser nueva. request/result/manifest conservan parámetros,
trazas, hashes de entrada/salida/código y Python/NumPy. No fingerprint completo
de CPU/BLAS ni protección ante interrupción a mitad de escritura: worker
administrado/API/UI son siguientes entregables.

Dos tests verifican invariancia numérica, cambio contextual de frenado, prefijo
causal, resultados de disco idénticos al repetir y rechazo a sobrescritura.
Corrida CLI real (30 muestras/30 Hz), muestra 10: compartida missing/A=0;
reducción I=−1/A=1.777778; giro I=−.116402/R=.993202/A=2.222119;
frenado padre quieto I=−1 y móvil I=+1, ambos A=1.111111.
El giro usa incrementos finitos y modo pasado, no se impone I=0.

Pendientes: backend/UI configurable, entrada de tracking/replay verificada,
controles de oposición local y emparejamientos incorrectos, ruido/ángulos,
anotaciones independientes y condiciones reservadas. No demuestra HIT ni
consonancia percibida. No cambia pitch/fases/ratios del instrumento aceptado.

Servicio R04 disponible por /api/research/r04: POST settings, GET inventario,
POST {id}/cancel, GET {id}/artifacts/{request.json,result.json,manifest.json}.
El worker usa writer lock y manifest independiente; al restaurar no relanza.
API es parte de create_app, sin requerir runtime/audio para banco sintético.
Panel web y evidencia específica de interrupción R04 siguen pendientes.
