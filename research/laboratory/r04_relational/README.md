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


R04 entrada de extremos corporal, preparación inicial: EndpointRequest elige
evaluación/run, COCO parent/child distintos y segmento ≤120 s. Lector carga
generación de pose congelada/hash mediante load_source; no copia video ni
recalcula tracking. Exige escala/procedencia de calibración congeladas para
esa persona; Kinematics causal de producción con settings del preset, warmup
desde inicio seleccionado sin preroll inventado. Velocidades T/s, faltantes
explícitos, reloj estricto y límite 14400. Snapshot conserva código de
Kinematics/analysis/contracts, escala/settings/source/cache/preset. Test con
replay sintético real pasa repetición exacta, warmup/gaps/contexto y rechazo
de extremos iguales/fuera de segmento/generación alterada. No medición
corporal nueva ni observación humana; worker/API/UI corporal aún pendientes.


R04 extremos congelados→contrastes→worker/API: start_body congela request e
input.json del lector verificado. Worker incluye ambos hashes y verifica
cambios antes de commit. probe_endpoints usa RelativeMode real en original,
rotación uniforme, inversión de ambos y velocidad común, con relojes/validez/
vectores/unidad/segmento validados. Faltantes reinician historia sin relleno.
Samples/hz sintéticos se declaran unused; no resampling. Resultado conserva
scale/settings/provenance/code y límites. POST /api/research/r04/trace recibe
{settings,selection}; descarga input verificada. Nueve tests integración/
worker/servicio pasan: replay sintético real, dos children con SHA idéntico
y mismo resultado directo, invariancia numérica, HTTP con lector real.
Panel corporal R04 y recorrido browser siguen pendientes. No ejecución corporal
humana nueva ni calibración transferida/audio cambiado.


R04 selección corporal web: comparación/run, COCO proximal/distal, segmento
configurables con persona/escala/procedencia congeladas visibles. Usa settings
relacionales de panel principal, samples/hz no aplican a pose. Bloquea ausencia
de calibración explícita, extremos idénticos y límites fuera de segmento.
No transfiere calibración ni ejecuta al editar. Chrome dos tests panel/panel
corporal pasan payload seleccionado, bloqueos e import/export existentes;
build TS/Vite pasa. Test UI con API simulada; backend lector real/child probado
separado, recorrido corporal browser→API real todavía pendiente. Endpoints
no se incorporan aún al JSON portable; fuente/calibración no se transfieren.
No defaults de audio modificados. Vite propio cerrado.


R04 recorrido de entrada corporal browser→HTTP→lector pose→worker pasa con
fixture de pose sintética real en cache. Chrome elige COCO 7/9, segmento .2–2,
efectúa dos corridas con bytes idénticos; cuatro contrastes, faltantes y
relaciones observadas. Snapshot input.json descargado realmente; UI muestra
persona one/escala/unidad del resultado congelado, no de fuente actual.
API/lector no mockeados, sin dispositivos ni datos corporales privados.
Servidor propio cerrado. No evidencia humana ni main/WebSocket completo.

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r04_harness --outDir /tmp/weaver-r04-body-network-ui --emptyOutDir
PYTHONPATH=src:tests:../harmonic-shaper-dev/src .venv/bin/python tests/r03_http_fixture.py --root /tmp/weaver-r04-body-fresh-unique --ui /tmp/weaver-r04-body-network-ui --port 8879
# Otro terminal, desde laboratory-ui:
LAB_R04_BODY_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalBodyNetwork.spec.ts --reporter=line
```

Reusa fixture R03 de evaluación/pose, no inputs privados. Root nuevo requerido.
Extremos portables y controles ampliados de oposición/ruido siguen pendientes.


R04 configuración corporal portable v1: export/import JSON con schema_version,
settings y endpoints COCO. Valida versión/keys/índices/distinción y parámetros
antes de aplicar; no incluye fuente/persona/escala/calibración/segmento.
Importar no corre worker ni cambia selección fuente/segmento. Dos tests Chrome
panel/body pasan recuperación de extremos/settings, segmento preservado y
cero llamadas al editar/importar; build pasa. No aceptación humana ni nuevos
experimentos corporales; controles ampliados y evidencia siguen pendientes.
No cambian defaults de síntesis; Vite propio cerrado.


R04 perturbación local proximal: proximal_multiplier configurable ±4
(default −1 sólo banco investigación; audio intacto). Nueva condición
proximal_scaled transforma únicamente velocidad proximal antes de RelativeMode: 
−1 invierte, 0 detiene, 1 conserva original. Sintético ahora 25 trazas, pose
5 condiciones. No supone pose físicamente posible ni oposición beneficiosa.
Tres tests banco, dos servicio y uno lector real/worker pasan (6 total);
identity multiplier=1 da mismas traces que original, inversión local en
shared_acceleration cambia missing a relación reforzada construida. Controles
globales conservan invariancia; no se exige invariancia local. Dos Chrome
panel/body pasan edición/payload/JSON y build pasa. Network tests actualizados
a nuevos conteos pero no reejecutados en este incremento. Control de tarea/
valor global, ruido/emparejamiento y anotación humana siguen pendientes.


R04 requisito de calibración auditado: evaluación local existente del fragmento
de dos personas/cuerpo indicado está complete pero baseline sin escala ni
procedencia. No se ejecutó R04 real inventando normalización ni se alteró
inventario/calibraciones privadas. Próxima corrida corporal exige calibración
explícita para esa fuente/persona y una evaluación nueva que la congele.
Test de integración nuevo con replay baseline sin escala confirma endpoint
reader y POST /trace rechazan antes de worker; inventario R04 vacío y tabla
de calibraciones idéntica. Dos tests integración pasan, incluido positivo
con escala explícita. Esto no bloquea bancos independientes ni cierra R04.
No publicar IDs/rutas/hashes/medios privados.


R04 ruido reproducible: perturbation_std (0–2, default 0) y
perturbation_seed (0–2147483647, default 0) en API/UI/JSON. Nueva condición
noisy_endpoints añade ruido gaussiano independiente a velocidades preparadas,
no a pose cruda. Sintético usa streams por escenario para conservar prefijos;
pose consume ruido por observación y no vuelve válido ningún faltante.
Ahora 30 trazas sintéticas/6 condiciones pose. Ocho tests banco/servicio/
entrada pasan; añadido test sintético semilla distinta sólo cambia ruido,
misma repite, cero exacto y prefijo causal. Test pose real sintética verifica
ruido repetible, prefijo y faltantes todavía missing; dos tests entrada pasan.
Dos Chrome panel/body y build pasan. Network conteos actualizados pero no
reejecutados aquí. No ruido calibrado de cámara ni estimación de robustez
corporal todavía, ni cambio de audio. Vite propio cerrado.
