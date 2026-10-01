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

Panel R04 disponible en pestaña Investigación: controles de todos los parámetros,
configuración JSON portable, inventario/cancelación/descargas y navegador de
trazas/muestras. Chrome aislado y build pasan; recorrido API real R04 por browser
y replay corporal todavía pendientes.


R04 browser→API→worker verificado por Chrome contra Uvicorn real, sin mocks.
Panel aislado usa fetch same-origin, servidor sin runtime/audio/cámara. Dos
corridas de 30 muestras producen bytes de resultado idénticos; 20 trazas,
request.json descargado con nombre correcto. UI mantiene I/R/A indefinidos
para aceleración compartida; muestra 10 del mismo frenado distal da I=−1
con proximal quieto y +1 con proximal móvil. No errores API visibles. Servidor
propio detenido con shutdown confirmado. No verifica main/WebSocket ni datos
corporales reales; entrada corporal y controles ampliados siguen pendientes.

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r04_harness --outDir /tmp/weaver-r04-network-ui --emptyOutDir
PYTHONPATH=src .venv/bin/python tests/r04_http_fixture.py --root /tmp/weaver-r04-fresh-unique --ui /tmp/weaver-r04-network-ui --port 8879
# Otro terminal, desde laboratory-ui:
LAB_R04_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalNetwork.spec.ts --reporter=line
```

Root debe ser nuevo: fixture nunca pisa inventario previo. Ctrl+C cierra
servicio/workers propios. URL explícita requerida; no usa laboratorio del usuario.


R04 fallos específicos del worker: 8 tests worker/servicio pasan. Requests
mutados en contenido o reemplazados por symlink, resultado alterado y manifest
interno symlink no pueden confirmar output; quedan failed sin result raíz.
Lock ocupado no crea manifest; settings inválidos quedan failed. Child real
produce computed/result, mantiene lock antes del commit externo; inventario
lo conserva running. SIGKILL+wait permite restaurar interrupted con hashes,
idempotente, sin descargar resultado interno ni relanzar. Worker ahora valida
manifest computed regular/no symlink antes de leerlo. No verifica todos los
puntos de crash del filesystem ni hardware; replay corporal sigue pendiente.
