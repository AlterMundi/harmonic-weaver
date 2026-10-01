# Arranque y primer recorrido local

Estado: segunda iteración local disponible; ver IMPLEMENTATION_STATUS. La escucha y
aceptación de Nicolás no se infieren de las pruebas automatizadas.

[Evidencia, mediciones y límites conocidos](VALIDATION.md).

## Dependencias

En Legion, el comando corto prepara la web e inicia la sesión:

```sh
cd /home/nicolas/Projects/harmonic-weaver-lab
./scripts/start-laboratory.sh --audio-backend jack --device "R24 Analog Stereo" --tracking-device cpu
```

El modo `auto` prefiere JACK sobre PipeWire si está disponible y selecciona una salida estéreo JACK. En Legion, el camino ALSA `pipewire` puede reportar callbacks activos sin salida útil; se usa JACK. `--audio-backend native` y `--device` permiten elegir otra ruta.

El wrapper acepta `WEAVER_PYTHON`, `SHAPER_DIR`, `SHAPER_PYTHON`, `HARMOCAP_DIR`,
`HARMOCAP_VENV` y `HARMOCAP_CHECKPOINT` para otros checkouts/entornos. Los flags
posteriores se pasan al launcher Python.

Weaver `feat/laboratory-live` (PR #30), HarMoCAP
`feat/laboratory-capture-baseline` (PR #1), Shaper
`feat/laboratory-telemetry` (PR #2). Los tres checkouts están separados de los
workspaces originales preservados. No requiere fusionar las PRs para probar.

Entorno Weaver: dependencias del proyecto y extra `lab`. Entorno HarMoCAP:
dependencias propias + `av>=12,<17` y modelo pose local. Entorno Shaper:
dependencias propias, dispositivo de audio disponible. Frontend: Node 22.

```sh
cd laboratory-ui
npm ci
npm run build
```

Desde el checkout Weaver, un arranque genérico:

```sh
PYTHONPATH=src HARMOCAP_DIR=/ruta/HarMoCAP HARMOCAP_VENV=/ruta/HarMoCAP/.venv \
python -m harmonic_weaver.lab \
  --shaper-dir /ruta/harmonic-shaper \
  --shaper-python /ruta/harmonic-shaper/.venv/bin/python \
  --checkpoint /ruta/modelo-pose.pt
```

En Legion, los checkouts y entornos ya preparados permiten:

```sh
cd /home/nicolas/Projects/harmonic-weaver-lab
PYTHONPATH=src \
HARMOCAP_DIR=/home/nicolas/Projects/HarMoCAP-lab \
HARMOCAP_VENV=/home/nicolas/Projects/HarMoCAP/.venv \
/home/nicolas/Projects/harmonic-weaver/.venv/bin/python -m harmonic_weaver.lab \
  --shaper-dir /home/nicolas/Projects/harmonic-shaper-lab \
  --shaper-python /home/nicolas/Projects/harmonic-shaper/.venv/bin/python \
  --checkpoint /home/nicolas/Projects/HarMoCAP/harmocap-m-pose-ft2.pt \
  --audio-backend jack --device "R24 Analog Stereo"
```

Abrir **http://127.0.0.1:8765**. Shaper propio usa localhost:8085, sin MIDI ni OSC.
Si un puerto está ocupado, el launcher informa el conflicto; no mata ese proceso.
Usar `--port` / `--shaper-port` para otra sesión, o `--external-shaper` para conectar
explícitamente un motor ya iniciado que tenga la API de laboratorio.
Ctrl+C termina esta sesión y solo su proceso Shaper propio.

`--no-audio` es diagnóstico: no representa un laboratorio sonoro funcionando.
Los presets/bitácora van a `~/.local/share/harmonic-weaver/laboratory` (cambiable
con `--data-dir`). El tracking vive junto al video o en el fallback documentado
en SOURCES. La cámara y el audio live no se graban automáticamente.

## Recorrido breve

1. Fuente: ingresar la ruta de un video y abrirlo; esperar el tracking o explorar
   el prefijo procesado. Reproducir y activar Loop. Reabrir el mismo archivo debe
   mostrar «cache reutilizado»; «Forzar tracking» genera una extracción nueva.
   En esta máquina ya hay cuatro fragmentos en `~/Videos/weaver-lab/` y en la
   biblioteca. No hace falta abrir/procesar el original de 15 GB para empezar.
2. Presets: elegir «Instrumento original» para el baseline de seis voces.
   Cambiar master, sensibilidades y ruteos mientras la fuente sigue corriendo.
3. Para modelos nuevos, elegir la persona y **Calibrar escala con este cuerpo**.
   Aplicar un preset local, relacional, angular o colectivo. Si no hay datos
   suficientes para una señal, se muestra missing; no se fabrica movimiento.
4. Figura: ver la suma de todos los armónicos activos y habilitar componentes.
   Las fases/ganancias vienen de Shaper. Shape y limiter pueden agregar contenido
   al audio que esta figura preprocesamiento no representa.
5. Guardar como nuevo y exportar JSON. Reaplicar al mismo video u otro; la
   calibración y la historia no viajan en el preset. Una marca guarda un comentario
   y contexto de sesión, no un fragmento audiovisual.

La aceptación humana evalúa lo que se siente al moverse/observar/escuchar.
Los tests verifican contratos, continuidad y comportamiento técnico; no esa sensación.

Al reiniciar se recupera el último video abierto, pausado desde el inicio, usando
sus parámetros de percepción y la caché válida. Esta preferencia es local y no
viaja en los presets. Cerrar explícitamente la fuente o elegir cámara borra esa
preferencia; la cámara no se enciende automáticamente al arrancar.

**Realce expresivo** (Instrumento): slider −1..+10, neutral en 0. Cambia la curva
de intensidad corporal, no frecuencias, ratios, fases ni forma de onda. Positivo
acentúa subidas y bajadas respecto de una media causal por voz, sin elevar
el sostenido; negativo atenúa valores bajos como en la primera prueba.
Duración del contraste controla la constante de tiempo (default 0.12 s):
menor = gestos más breves, mayor = énfasis más prolongado. El master sigue controlando el nivel final. Se guarda en presets.
La figura recibe las ganancias efectivas y refleja ese realce; su autoescala
puede disimular cambios de tamaño global (desactivarla para comparar amplitud).

Los modelos distintos de baseline requieren calibración: el inspector muestra
un aviso y botón cuando falta. Calibrar con hombros y caderas visibles antes de
evaluarlos; permitir que acumulen historia tras arrancar.


Para aprender los controles: en Ruteos, exponente > 1 reduce valores pequeños
más que grandes (contraste estático); exponente < 1 levanta valores pequeños
(compresión). Suavizado reduce variaciones rápidas. Realce positivo, en cambio,
distingue una subida de un nivel sostenido mediante historia temporal.

Realce positivo ahora llega a **10**: 1 conserva el máximo anterior, 10 multiplica
por diez el énfasis de cambios (no la ganancia general). Los picos se acotan a 1:
puede recortar más el contraste extremo sin aumentar indefinidamente el volumen.

**Articulación** mezcla sostenido (0%) e impulsos de subida (100%).
Los impulsos salen del aumento de intensidad respecto de su media causal, no de
un reloj ni de reiniciar voces. **Cola de transientes**, default 0.15 s, controla
su caída exponencial. Primero probar una mezcla intermedia; a 100% un nivel
constante termina en silencio. Ambos controles se guardan en presets.

## Segunda iteración: probar sin perder la sesión

En Legion con R24:

```sh
cd /home/nicolas/Projects/harmonic-weaver-lab
./scripts/start-laboratory.sh --audio-backend jack --device "R24 Analog Stereo"
```

Si Shaper de esta sesión ya está funcionando en 8085, agregar
`--external-shaper`: se conecta al motor existente y no lo detiene al salir.
Un puerto ocupado no autoriza a matar un motor ajeno. La cámara sigue siendo una
selección explícita; no se abre automáticamente al reiniciar.

1. Reproducir el video cacheado. La configuración actual y los presets guardados
   se conservan; las ediciones compatibles de realce/articulación ya no pierden
   la historia temporal del ruteo al mover el control.
2. **06 · Referencia 01c** recupera los valores iniciales sostenidos y afinados;
   **07 · Exploración** propone realce 10 y articulación 30%, para escuchar.
   Son nuevos IDs: no sobrescriben el antiguo 01c ni se aplican solos. Tampoco
   significan que Nicolás haya aceptado esas nuevas combinaciones.
3. Para local/relacional/angular/colectivo, calibrar con hombros y caderas
   observados. El inspector distingue fuente, calibración, historia/faltantes,
   ruteo sin actividad y estado del audio. Expandir las razones por señal.
4. En Fuente, abrir **Cobertura de tracking y huecos**. Muestra proporciones
   observadas y duración máxima de gaps por joint. Una pose puede estar equivocada
   aunque el detector la considere observada. No elegir fragmentos sólo por energía.
5. Ante un fallo de tracking, **Reintentar con CPU** conserva el diagnóstico y
   reutiliza una caché CPU válida si existe. No cambia de backend silenciosamente.
   `auto` ahora resuelve el dispositivo antes de identificar el cache; cachés
   históricas etiquetadas `auto` pueden requerir una extracción nueva una vez.
6. Guardar configuraciones interesantes y usar **Comparar** cuando quieras;
   seleccionar presets, segmentos y calibración explícita si corresponde.
   [Contrato, resultados y repetición](EVALUATION.md). No hace falta comparar para tocar.

Defaults sonoros existentes intactos: realce 0, articulación 0, contraste 0.12 s,
cola 0.15 s, suavizado de ganancia 01c 0.03 s. Pitch/fase siguen siendo ruteos
separados; las referencias afinadas los mantienen deshabilitados. Los controles
extremos necesitan escucha: las pruebas automáticas no juzgan empaste o musicalidad.

## Fragmentos con varios cuerpos

Al abrir un video se elige automáticamente el cuerpo con mayor cobertura
de articulaciones observadas (no una estimación de precisión). En Fuente se
puede elegir como alternativa el primero de la lista y desactivar la reproducción
automática al terminar el tracking. Después podés cambiar **Persona** libremente. La lista incluye las personas de la generación completa para
poder conservar una selección aunque el cuerpo esté momentáneamente fuera de
cuadro. La figura atenúa los esqueletos no seleccionados; esto ayuda a verificar
la elección. Los números de slot no son nombres ni identidades humanas.

La elección queda guardada localmente para ese archivo, clave de cache y generación.
Reabrir el mismo tracking recupera el cuerpo elegido; reprocesarlo elige un
nuevo valor por defecto y lo informa para que verifiques la selección. Nunca transfiere calibración: sigue siendo una acción explícita.
Mientras se construye un prefijo, se puede seleccionar; se guarda al terminar
la generación válida. Si la extracción falla, esa elección parcial no reemplaza
la preferencia de la generación anterior. Si el cuerpo elegido deja de verse,
el instrumento espera sus datos y no cambia a otro cuerpo automáticamente.

El modo `--no-audio` devuelve 503 en la telemetría de voces: es un arranque de
percepción/UI sin audio. Conectar la R24 después no habilita ese proceso.
Detenerlo con Ctrl+C y volver a iniciar con el comando R24 de arriba, sin
`--no-audio`. Recargar la web después del reinicio.

## Arranque explícito de desarrollo

Los avances posteriores al laboratorio habitual están en
`~/Projects/harmonic-weaver-dev` y requieren el Shaper compatible de
`~/Projects/harmonic-shaper-dev`. No reemplazan `harmonic-weaver-lab`.
Cada checkout usa su propio `.venv`; para preparar una instalación nueva:

```bash
cd ~/Projects/harmonic-weaver-dev
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[lab,test]'
cd ~/Projects/harmonic-shaper-dev
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -e '.[test]'
```

Las versiones instaladas forman parte de la identidad de los experimentos;
instalar sin constraints puede resolver versiones distintas y exige producir
un nuevo manifest, no reutilizar una identidad antigua.

```bash
cd ~/Projects/harmonic-weaver-dev
./scripts/start-laboratory-dev.sh --check
./scripts/start-laboratory-dev.sh --audio-backend jack --device "R24 Analog Stereo" --tracking-device cpu
```

La web de desarrollo es `http://127.0.0.1:8875`, Shaper usa `8185` y el estado
se guarda en `~/.local/share/harmonic-weaver/laboratory-dev`. `--check` sólo
comprueba imports y muestra destinos; no abre cámara ni audio, ni verifica la
conexión física de la R24. Ctrl+C detiene los procesos de esa sesión.

La primera apertura tiene estado independiente: importar los presets portables
que quieras probar desde la web. No se copian selecciones corporales,
calibraciones, fuentes ni videos del laboratorio habitual. Abrir un fragmento
existente lo usa desde su ruta; no hace falta copiar el original grande.
El nuevo estado puede necesitar su propio tracking. No iniciar ambos Shapers
sobre la R24 simultáneamente. Para cambiar puertos o datos, pasar `--port`,
`--shaper-port` o `--data-dir`; los argumentos explícitos prevalecen.
`WEAVER_PYTHON`, `SHAPER_DIR`, `SHAPER_PYTHON` y `LAB_DEV_DATA_DIR` permiten
seleccionar otras instalaciones deliberadamente; el wrapper no usa un venv
original como alternativa silenciosa para Weaver o Shaper.


### Recorrido R05 experimental (rama de desarrollo, PR #72)

En Investigación, elegir comparación terminada, corrida y señal; confirmar
persona/unidad congeladas. Ajustar resonadores/excitación y, opcionalmente,
activar «Comparar con mapeo de amplitud R05». Correr y revisar métricas: soporte
común y cola están separados; undefined significa ausencia de soporte, no cero.

«Explorar figura R05» abre el estado de todas las voces. Elegir brazo y usar
«Leer ventana» para inspección manual, o «Cargar audio R05» y los controles del
reproductor para escucha explícita. El seguimiento (default10Hz, loop apagado)
usa ventanas ya reproducidas; se pueden ajustar points/stride/pesos/fases/escala.
Ganancia de escucha es una vista float32 del WAV DOUBLE crudo, sin normalización
ni limitador. Revisión de niveles previa a escuchar; sin equivalencia perceptual
ni fase corporal/medio cimático físico inferidos. Video de origen aún no aparece
en este recorrido experimental; no cambia el reproductor de exploración live.

Preset R05 y preset de proyección se exportan/importan como JSON separados;
no transportan persona/calibración/fuente/segmento/muestra. Importar proyección
detiene audio y no lo reinicia. Se descarga PCM DOUBLE/verificador para evidencia;
la vista float32 sirve para escuchar en Chrome. Escucha/aceptación humanas pendientes.

### Video de origen en la exploración R05

En una corrida terminada, abrir «Explorar figura» y «Mostrar video de origen R05».
La fuente se resuelve desde la evaluación congelada y se verifican su medio,
tracking y procedencia; no se copia el video ni se ejecuta tracking nuevo. Cargar
el audio R05 y reproducirlo desde sus controles. El video está silenciado y sigue
el reloj del audio: cero corresponde al inicio del segmento seleccionado; al
llegar a su final se pausa mientras continúa la cola del instrumento. Pausas,
seeks y loops del audio se propagan al video. «Ocultar video» detiene ese elemento.
Se muestra la persona registrada en el experimento, sin afirmar identidad ni
transferir calibración. Una fuente ausente/alterada o no decodificable deja un
error visible. El video no contiene aún overlay de pose ni offset ajustable.

R05 ahora ofrece «Desfase video/audio R05 (s)», entre −10 y +10 s; default cero.
Positivo adelanta la fuente, negativo la retrasa. Se aplica sólo al video y se
conserva al exportar/importar el preset de proyección. La posición se limita al
crop; al empezar antes del crop o terminar después, la imagen queda retenida.
Durante la cola se congela la posición desplazada del final del segmento, también
con offsets negativos. No corrige ni modifica timestamps, features o PCM; es una
hipótesis visual explícita, no una latencia medida. Importar detiene la escucha.
