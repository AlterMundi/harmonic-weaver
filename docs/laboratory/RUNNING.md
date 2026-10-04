# Arranque y primer recorrido local

Estado: segunda iteración local disponible; ver IMPLEMENTATION_STATUS. La escucha y
aceptación de Nicolás no se infieren de las pruebas automatizadas.

[Evidencia, mediciones y límites conocidos](VALIDATION.md).

## Dependencias

En Legion, el comando corto prepara la web e inicia la sesión:

```sh
cd /home/nicolas/Projects/harmonic-weaver
./scripts/start-laboratory.sh --audio-backend jack --device "R24 Analog Stereo" --tracking-device cpu
```

El modo `auto` prefiere JACK sobre PipeWire si está disponible y selecciona una salida estéreo JACK. En Legion, el camino ALSA `pipewire` puede reportar callbacks activos sin salida útil; se usa JACK. `--audio-backend native` y `--device` permiten elegir otra ruta.

El wrapper acepta `WEAVER_PYTHON`, `SHAPER_DIR`, `SHAPER_PYTHON`, `HARMOCAP_DIR`,
`HARMOCAP_VENV` y `HARMOCAP_CHECKPOINT` para otros checkouts/entornos. Los flags
posteriores se pasan al launcher Python.

Desde el 2026-10-04 el laboratorio avanza integrado en `main`, incluyendo
Weaver #152 y sus antecedentes (aportes #36/#97/#107), Shaper #7 y HarMoCAP #1.
En Legion se desarrolla y prueba desde `~/Projects/harmonic-weaver`, con
`~/Projects/harmonic-shaper` y `~/Projects/HarMoCAP`. Hay una sola instalación,
los puertos habituales 8765/8085 y los datos existentes de `laboratory`.
Los nombres antiguos de carpetas y scripts quedan como alias de compatibilidad.
No constituyen versiones ni instalaciones separadas.

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
cd /home/nicolas/Projects/harmonic-weaver
PYTHONPATH=src \
HARMOCAP_DIR=/home/nicolas/Projects/HarMoCAP \
HARMOCAP_VENV=/home/nicolas/Projects/HarMoCAP/.venv \
/home/nicolas/Projects/harmonic-weaver/.venv/bin/python -m harmonic_weaver.lab \
  --shaper-dir /home/nicolas/Projects/harmonic-shaper \
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

Si llega tarde la respuesta de aplicar un preset, la web conserva las ediciones
posteriores y las revisiones más nuevas ya confirmadas. Esto permite seguir
explorando mientras llega la respuesta sin que vuelva un valor anterior por HTTP.
Si elegís varios presets antes de que llegue la confirmación, se termina la
aplicación en curso y se aplica sólo la última elección pendiente. La web muestra
qué elección espera confirmación. Una edición posterior de controles descarta esa
elección pendiente; el video continúa. No se acumula una lista de presets intermedios.
Los conflictos de revisión continúan visibles; recuperar estado aplicado toma el
estado vigente en vez de reintentar una escritura sobre otra ventana silenciosamente.

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
cd /home/nicolas/Projects/harmonic-weaver
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

Si al finalizar tracking la elección automática cambia respecto del cuerpo visto
en el prefijo, descarta la calibración de ese cuerpo y reinicia historia/ruteo.
Los modelos que requieren escala muestran «Calibrá» para el nuevo cuerpo; no
heredan la escala anterior. Si sigue el cuerpo elegido explícitamente, conserva
su calibración/historia. La medición anterior permanece en el inventario local.
Cuando había una escala activa, la web explica que se descartó por ese cambio
automático. El aviso se limpia al calibrar correctamente, elegir manualmente otra
persona, abrir otra fuente o cerrarla. No obliga a calibrar para usar baseline.

El modo `--no-audio` muestra «Modo diagnóstico sin audio» en la web: los controles
pueden ser aceptados, pero no hay telemetría/figura de voces efectivas ni sonido.
La API de Shaper devuelve 503 para esa telemetría; Weaver no la consulta en este
modo. Los errores reales del servicio de control siguen visibles. No se permite
combinarlo con `--external-shaper`: no puede apagar un motor externo.
Conectar la R24 después no habilita ese proceso.
Detenerlo con Ctrl+C y volver a iniciar con el comando R24 de arriba, sin
`--no-audio`. Recargar la web después del reinicio.

## Desarrollo integrado

```bash
cd ~/Projects/harmonic-weaver
./scripts/start-laboratory.sh --check
./scripts/start-laboratory.sh --audio-backend jack --device "R24 Analog Stereo" --tracking-device cpu
```

Abrir http://127.0.0.1:8765. `--check` verifica imports sin iniciar servicios.
Desarrollamos e integramos continuamente en `main`; una separación de producción
se decide cuando Nicolás la pida. Las pruebas pueden usar datos temporales y
puertos explícitos sin crear otra instalación cotidiana.

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
ni fase corporal/medio cimático físico inferidos. Video de origen y pose se cargan
explícitamente como se describe abajo; no cambia el reproductor de exploración live.

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
error visible. El offset y overlay de pose se habilitan explícitamente abajo.

R05 ahora ofrece «Desfase video/audio R05 (s)», entre −10 y +10 s; default cero.
Positivo adelanta la fuente, negativo la retrasa. Se aplica sólo al video y se
conserva al exportar/importar el preset de proyección. La posición se limita al
crop; al empezar antes del crop o terminar después, la imagen queda retenida.
Durante la cola se congela la posición desplazada del final del segmento, también
con offsets negativos. No corrige ni modifica timestamps, features o PCM; es una
hipótesis visual explícita, no una latencia medida. Importar detiene la escucha.

R05: después de mostrar el video, «Cargar pose congelada R05» recupera el tracking
verificado de la persona registrada. «Mostrar pose R05» oculta/muestra el dibujo;
«Antigüedad máxima pose R05 (s)» controla cuánto puede durar una observación,
default 0.1 s (rango >0 hasta 5 s). Ambos controles se guardan en el preset.
Sólo se dibujan joints observados y conexiones entre dos joints observados,
en coordenadas de cámara 2D/frame_height. La observación elegida nunca es futura
respecto del video; no se interpola. Gap, cuerpo ausente, seek en curso o
coordenadas no proyectables dejan la figura vacía y un diagnóstico visible.
El offset audiovisual también desplaza la pose: sigue el tiempo real del video,
no la muestra de audio. No convierte coordenadas world/3D a imagen.

### R05: modulación experimental de frecuencia y serie f1/2

Activar «Comparar con mapeo de amplitud R05» y, opcionalmente, «Modular frecuencia
del mapeo R05». Depth (default de la opción .25, rango 0..<1) controla la excursión;
smoothing_s (.1 s, rango 0..10 s) suaviza el control. La señal dividida por
mapping.reference_scale se recorta a [-1,1]; un factor común
`1 + depth × señal suavizada` multiplica todas las portadoras, conservando ratios
instantáneos. Missing o vencimiento max_hold_s lleva el control hacia cero.
La fase se integra por muestra y continúa durante silencios: no reataques.
Configuraciones que podrían alcanzar Nyquist se rechazan antes de correr.
La amplitud sigue su mapeo existente; los valores negativos no la activan.

La modulación está desactivada por defecto; no cambia Shaper ni presets live.
«Serie f1/2 R05» establece ratios 0.5,1,1.5… sin reducir la cantidad de voces;
«Serie armónica R05» restaura ratios 1,2,3… Ambos sobrescriben explícitamente la
lista de ratios del experimento, no la afinación del instrumento cotidiano.
Exportar/importar conserva opciones y valores. Renderizar, escuchar mapped y
observar su figura usa cuadratura real del modelo modulado. No es audificación,
fase corporal medida ni evidencia de coordinación fisiológica.

### R06 en la mesa web

En harmonic-weaver, pestaña «Investigación» → «R06 · Banco de activación».
La web carga defaults validados del servidor. Modificar medio (f1, ratios,
damping, acoplamiento, topología/matriz y sample rate) y todos los parámetros de
calendario/cálculo. «Exportar configuración R06» guarda JSON portable;
«Importar configuración R06» lo valida/restaura sin ejecutar ni elegir cuerpo.
«Correr banco R06» congela esa configuración y calcula en worker propio.
Cancelar sólo afecta esa corrida. No requiere video, calibración ni audio.

«Ver resultado R06» muestra cuatro calendarios, dosis/RMS/pico/integral de norma
y RMS de cola. Selector/slider inspeccionan trace y distinguen cola de excitación.
Descargar request/result/manifest usa verificación de integridad. Cambiar los
controles no cambia un resultado ya calculado; su configuración está congelada.
RMS/loudness, clustering/espectro y eficacia no son equivalentes. No hay ganador
ni prueba de privilegio phi. Esperar finalización del proceso antes de otra
corrida: UI también observa worker_active al terminar el manifest.

R06: «Comparar medios R06» crea una copia explícita del medio base. Editar la
lista JSON medium_controls (hasta cuatro medios) para variar amortiguamiento,
acoplamiento y topología/matriz. f1, ratios y sample_rate deben ser idénticos al
base; cambios incompatibles se rechazan antes de correr. La copia conserva su
configuración al cambiar después el medio base; no sigue silenciosamente esos
cambios. Una copia idéntica devuelve diferencias cero y sirve como control.

Preset export/import conserva la lista. El resultado muestra «Contraste de
medios R06»: valores raw y diferencias control menos base para cada calendario.
«Medio de traza R06» permite inspeccionar base o cada control, con el mismo reloj,
eventos y dosis. Los resultados siguen congelados aunque se editen controles.
No son un ranking de eficacia; cambiar el medio modifica su respuesta esperable.

R06: «Permutar intervalos R06» agrega un surrogate por cada calendario: reordena
los intervalos entre impulsos mediante una permutación seeded. Conserva exactamente
su multiset digital, cantidad/dosis y primer/último evento. Hay ocho condiciones
cuando se activa; medio y clock se mantienen. La grilla uniforme puede quedar
idéntica y no se fuerza otra permutación. No conserva espectro ni correlaciones
de orden superior. El checkbox se exporta/importa y aplica también a medios de
control; selector de calendario permite inspeccionar *_interval_shuffle.
Default apagado y campo omitido conservan presets anteriores. Una sola semilla
no constituye una distribución nula ni un contraste estadístico de significancia.

R06: «Banco de semillas R06» agrega una lista JSON de hasta ocho semillas
adicionales, únicas y distintas de la principal. El preset congela la lista.
Validación comprueba todos los calendarios antes de encolar y limita el trace
agregado a 144000 puntos; aumentar trace_stride si se excede. La corrida retiene
el resultado principal y cada repetición, incluidos sus medios de control.
«Semilla de resultado R06» cambia juntas las tablas/trazas visibles; el resultado
permanece congelado y no aplica cambios del draft actual.

«Resumen descriptivo del banco R06» muestra count/media/min/max/desvío poblacional
por medio, calendario y métrica. Incluye principal y adicionales. Calendarios
racional/phi/sqrt2 pueden ser idénticos entre semillas; random y permutations
cambian según su stream. No asumir ensayos humanos independientes, distribución
nula, significancia, un ganador ni eficacia HIT. Opción apagada por defecto;
campo omitido mantiene formato previo.

Si una semilla del banco produce eventos en la misma muestra, R06 rechaza toda
la configuración antes de crear el job y muestra calendario/semilla/muestras.
No fusiona eventos ni reemplaza la semilla. Revisar span/count/seed explícitamente
conservando el criterio del experimento; no interpretar el rechazo como resultado
favorable/desfavorable de la hipótesis.
# Recorrido R07 experimental · PR #74

En el workspace de desarrollo, iniciar con el comando habitual documentado
en este archivo. Abrir **Investigación → R07 · Membrana virtual**. Primero
necesitás una corrida R05 completa; seleccionarla y elegir `single` o, para
comparación de mecanismos, `excited`/`mapped`. Ajustar `sample_rate` al reloj
de ese PCM (no hay remuestreo silencioso) y stop al soporte disponible.

Para empezar: activar **Secuencia causal R07**, ventana/paso de 0.1 segundos
en muestras, calcular y abrir **Ver figura R07**. Reproducir su audio y activar
**Seguir audio R07**: sólo se muestra el último frame ya ocurrido. Antes del
primero se indica ausencia; pause/seek/loop usan el reloj del audio. Desactivar
seguimiento permite elegir frames manualmente o RMS global. Cambiar escala
visual no modifica datos RMS. Exportar/importar configuración conserva geometría,
ventanas, seguimiento, loop y escala, sin copiar fuente ni iniciar reproducción.

Esta membrana es un modelo sound-only, sin presión/material calibrados ni
dinámica de arena/agua. No altera el instrumento live. Software/backend y
recorrido Chrome con señales sintéticas verificados; escucha humana, latencia
física, convergencia modal y recuperación científica de atributos pendientes.


## Recorrido R10 experimental · PR #78

En harmonic-weaver, con el arranque integrado documentado arriba, abrir
Investigación → R10. Este recorrido es opcional: el instrumento cotidiano sigue
funcionando sin completar ensayos ni responder preguntas.

1. Desde una corrida R05 completa, seleccionar estímulo/arm y editar condiciones,
   preguntas, escala, slot declarado y rol. Preparar estímulos resueltos R10, revisar
   fuentes y guardar protocolo R05 R10. Guardar no reproduce automáticamente.
2. Abrir protocolo congelado R10. Elegir ensayo y preparar reproducción; reproducir,
   pausar o mover tiempo nominal en pausa. Video original siempre silenciado;
   el audio viene de R05. Offset positivo adelanta audio; fuera de soporte se pausa.
3. Guardar transporte R10 en pausa si interesa conservar ese snapshot. Preparar
   otro ensayo reemplaza la memoria local; guardar/exportar antes. Registros de
   transporte permiten recuperar envíos pendientes o descargar tres artefactos.
4. Editar Respuesta JSON R10: trial correcto, todos los items y null para faltantes.
   Guardar respuesta R10, con ID de transporte opcional del mismo ensayo. Una
   corrección crea registro nuevo; no reemplaza automáticamente la anterior.
5. Actualizar selección de respuestas R10, seleccionar una versión por ensayo y
   analizar. Tablas separan escala/preguntas/rol/condición; exportar o guardar
   análisis congelado. Pares requieren referencia/destino del mismo protocolo,
   estímulo/repetición y condiciones distintas: diferencia destino menos referencia.
6. Listados permiten reabrir y exportar análisis/pares. Tras respuesta de red perdida,
   recargar y usar Recuperar envío explícitamente: conserva selección/hash original.
   Exportar/descartar pendiente afecta sólo esa pestaña, no registros del servidor.

Los conteos son registros/pares declarados, no participantes independientes. Fin
nominal no demuestra exposición completa; volumen/mute no mide nivel físico.
Preguntas no son escalas validadas. sessionStorage conserva pendientes sólo durante
la sesión de esa pestaña; exportaciones/manifests son la copia durable elegida.
Escucha y aceptación humanas de este recorrido siguen pendientes.

Diseños portables de contrastes R10: editar condiciones/dirección en Diseño JSON,
guardar o importar/exportar sin IDs. Seleccionar respuestas explícitamente, preparar
y revisar pares disponibles y faltantes. Usar pares del diseño sólo escribe Pares
JSON; Calcular pares y Guardar pares congelados siguen siendo acciones separadas.
Importar/aplicar preset conserva respuestas seleccionadas y descarta preview viejo.

El último transporte conserva un borrador en la sesión de pestaña, incluyendo
closed cuando se desmonta el player. Registros de transporte permite guardarlo o
exportarlo después de cerrar player/recargar, sin reproducir. Preparar otro ensayo
lo reemplaza. Cerrar pestaña/crash no garantiza conservación ni evento closed: para
copia durable guardar en servidor local o exportar antes.


## R11 · Inspección cruda experimental (PR #79)

Para tablas: Investigación → R11 → Importar tabla CSV; declarar metadatos y
mapeo, Convertir y **Guardar importación CSV R11**. Al volver, Actualizar/Abrir
importación recupera original, configuración y resultado. `source.csv` se descarga
con sus bytes UTF-8 originales. Recalcular es explícito; no cambia la grabación.
Guardar observaciones conserva sólo el Stream: usar Guardar importación para
conservar también CSV y mapeo. [Detalles](../../research/laboratory/r11_neuro/README.md#archivo-local-de-importaciones-csv--2026-10-03).

En Investigación → R11, importar un JSON Stream de neuro_observations con
unidades/referencia/clock y samples explícitos, o editar Observaciones JSON R11.
Inspeccionar contrato muestra cobertura/gaps y permite exportar inventario+raw.
No conecta hardware ni interpreta exports Cyton automáticamente: deben adaptarse
con procedencia explícita. No calcula SNR ni filtra.

Después de inspeccionar, usar Guardar observaciones R11. Actualizar registros
muestra el estado de verificación; Abrir observaciones guardadas recupera raw y
cobertura. Descargar request.json/result.json/manifest.json conserva el registro
fuera de la sesión. Un registro completo significa artefactos publicados, no una
adquisición física validada.

Si se interrumpe el envío, recargar y elegir Recuperar envío de observaciones R11:
se reintenta el contenido congelado, sin duplicarlo. También puede exportarse o
descartarse el pendiente local. No se reenvía automáticamente ni se adquieren datos.
El pendiente usa sessionStorage: no confiar en cerrar la pestaña para conservarlo;
exportarlo o completar el guardado del servidor. Si el almacenamiento local falla,
no se envía. Importación nativa limitada a 16 MiB; rendimiento de sesiones grandes
pendiente. Fixture Chrome sintética verificada; adquisición humana pendiente.


### Control sintético SNR R11

En Investigación → Control de señal/ruido conocido, ajustar cada tono (amplitud,
frecuencia, fase y DC), rate/count, ventana [inicio,fin), índices faltantes/excluidos
como arrays JSON y retiro de media. Calcular control SNR muestra potencias sobre
soporte común y dB/status. El ejemplo inicial amplitudes2:1 da aproximadamente
6,02dB; poner amplitud de ruido en0 muestra noise_zero y dB no definido. Un offset
DC cuenta como potencia salvo que se elija retirar media. No es un estimador EEG.

Exportar configuración SNR permite reimportar el control sin depender de un video,
cuerpo o calibración. Exportar resultado conserva config, componentes originales,
soporte y métricas. Descarga local solamente; manifest/verificador de servidor
pendiente. Importación config ≤1MiB, máximo20000 muestras por corrida; no ventana
continua ni adquisición física. Config inválida se rechaza al calcular.


### Comparar el mismo gesto con distintas configuraciones

En Comparar, seleccionar ≥2 presets guardados y un mismo segmento/persona, activar
Generar WAV y estado de osciladores y correr Comparar presets. Al terminar, Ver
comparación → Ver video, sonido y figura. Mover el WAV al gesto que interesa y
alternar **Preset del mismo segmento**: mantiene instante y pausa/reproducción.
**Pausar comparación** también funciona mientras carga otra versión. No cambia
los presets live ni el tracking; el cambio de archivo no es un crossfade.

En Legion hay una comparación local de60s y tres variantes para probar este
recorrido. Su ID y variantes están en
~/.local/share/harmonic-weaver/laboratory-dev/ab-playback-validation.json;
abrir la comparación con ese directorio. Sólo es evidencia de software, no
aceptación auditiva. Arrancar el desarrollo como se documenta arriba:

```sh
cd ~/Projects/harmonic-weaver
./scripts/start-laboratory-dev.sh --audio-backend jack --device "R24 Analog Stereo" --tracking-device cpu
```

Web integrada http://127.0.0.1:8765. Los archivos de validación anteriores
siguen conservados localmente en su directorio histórico.


### Hacer audible cada modelo conservando la afinación

En Presets, elegir08–11. Calibrar torso con hombros/caderas visibles para la
fuente/persona actual. Estos presets sólo rutean intensidad: local escucha error
de predicción, relacional oposición relativa ponderada por movimiento, angular
rapidez sin cancelación bilateral, colectivo tres modos más residuo/cambio/
velocidad en seis voces. Todos los parámetros siguen editables en Modelos/Ruteos.
Se agregan sin sobrescribir presets existentes ni cambiar configuración activa.

Valores iniciales: realce0, articulación0, smoothing0.03s, techo gain0.45. Local
usa peso5T⁻¹; angular0.45/180 por deg/s; relacional gain×(1−I)/2. Colectivo normaliza
amplitudes con0.75porT/s y cambio con1/30porgrado. Son puntos de exploración,
no escalas físicas ni resultados sobre calidad del movimiento. Las rutas antiguas
siguen disponibles. T es torso aparente calibrado de esa toma/cuerpo.

También está preparada una comparación local con referencia y los cuatro modelos
para el mismo minuto. Consultar su ID en
~/.local/share/harmonic-weaver/laboratory-dev/model-playback-validation.json;
Comparar → Ver comparación → Ver video, sonido y figura → Preset del mismo segmento.
La calibración de esa corrida está congelada en su solicitud; no queda aplicada a
la sesión live. El render/recorrido software pasó; escuchar y dar feedback está
pendiente. No se publicó ningún video, tracking o resultado corporal.


### Prueba de UI completa sin dispositivos

Para verificar el recorrido de video/cache/persona/calibración/presets/loop sin
abrir salida de audio ni cámara, construir la UI y arrancar la fixture en un
**directorio nuevo**, separado de la sesión cotidiana:

```sh
npm --prefix laboratory-ui run build
HARMOCAP_DIR=../HarMoCAP-lab HARMOCAP_VENV=../HarMoCAP/.venv PYTHONPATH=src \
  .venv/bin/python tests/laboratory_ui_fixture.py \
  --root /tmp/weaver-ui-nuevo --ui laboratory-ui/dist \
  --checkpoint ../HarMoCAP/harmocap-m-pose-ft2.pt --port 8879
```

Fixture confirma explícitamente audio no disponible; registra targets de control,
no VoiceFrames ni escucha ficticias. Otro terminal, desde laboratory-ui:

```sh
LAB_FULL_UI_URL=http://127.0.0.1:8879 LAB_FULL_VIDEO=/ruta/local/clip-con-cache.mp4 \
  LAB_FULL_PERSON=slot-elegido PLAYWRIGHT_CHANNEL=chrome \
  npx playwright test tests/fullLaboratoryNetwork.spec.ts --workers=1
```

Usar clip multipersona de más de7s con cacheCPU compatible; LAB_FULL_PERSON es
opcional. El test abre desde ruta y exige cache_hit; no upload ni copia del medio.
Detener fixture con Ctrl+C. Su root contiene estado/datos privados de la prueba:
no publicarlo. La biblioteca real de desarrollo ya tiene registrado el minuto dúo;
para jugar usar el launcher de desarrollo y elegirlo en Videos de la biblioteca.

### Exportación opcional de una comparación: video + audio + figura

En desarrollo, abrir una comparación terminada con PCM y elegir **Reproducir**.
Dentro del reproductor, **Exportar video, audio y figura** exporta el preset y
segmento elegidos. FPS, tamaño total, CRF, formato y bitrate AAC son editables.
La figura hereda el preset congelado; **Personalizar figura** permite cambiar
períodos, puntos, persistencia, grosor, brillo, escala, componentes, color y espejo.
Guardar/importar configuración sólo transporta esos ajustes, sin fuente/persona/
calibración/IDs de corrida. El servidor valida límites al exportar.

El trabajo es opcional y separado del transporte: muestra progreso, admite
cancelación y permite descargar video, manifest y timeline cuando termina.
La lista persiste tras reiniciar. Un trabajo sin confirmación final queda
interrumpido; no se presenta su archivo parcial como exportación completa.
Destino: `$DATA_DIR/comparison-exports/<id>/result/` (desarrollo:
`~/.local/share/harmonic-weaver/laboratory-dev/comparison-exports/`). No hay subida
automática. No copia el original ni recalcula tracking.

MKV conserva paquetes PCM del WAV. MP4 usa AAC con pérdida, apto para navegador;
el WAV original sigue siendo la referencia. Máximo 120s de PCM incluida cola.
Exportación siempre a 1×, sin offset manual del reproductor. Video a la izquierda,
suma de todos los osciladores a la derecha, con fase/gain interpolados del archivo
voice-frames. La cola sostiene el último frame de video. Se excluye audio original.
No hay esqueletos. La figura está antes del timbre/limitador y no representa una
membrana física. La persistencia raster depende de FPS; el estilo no es idéntico
a WebGL. El reloj compartido es digital, no una medición de sincronía física.

Requiere FFmpeg/ffprobe con libx264 y AAC, OpenCV, NumPy y SoundFile (entorno del
laboratorio). El render compite por CPU si se exporta durante uso live; para probar
fluidez, empezar con 640×360/10FPS. No se cambian defaults del instrumento, audio,
R24, ni presets. Inputs se verifican antes/después; outputs y manifest se verifican
al descargar. El manifest registra ajustes, hashes, versiones, streams y límites.

### R12 · Importar mediciones y comparar intentos

En investigación, abrir **R12 · Mediciones, tarea y cobertura**. La plantilla es
un control sintético explícito. **Analizar mediciones R12** obtiene HR media85bpm
(sintética), potencia2W y10J para5s; al bajar gap máximo a0.5s no hay soporte,
porque las muestras están a1s. Esto verifica software, no mide a una persona.

Importar JSON R12 real con task/constraints, slot, proveedor, reloj y mediciones.
Canales disponibles: heart_rate/bpm, mechanical_power/W, metabolic_power/W,
reported_effort/dimensionless y task_error/dimensionless. Watts requieren método,
incertidumbre y evidencia de medición/calibración declaradas; no derivar de pose.
Cada null/exclusión lleva causa. El protocolo íntegro y timestamps originales
quedan en el JSON editable; la UI controla gap, canales comunes, relojes e intentos.
Guardar/importar configuración portable sólo transporta gap y selección de canales.
No mueve datos, cuerpos, calibración, reloj o ventanas a una fuente nueva.

**Vincular explícitamente una evaluación local** pide ID e índice de corrida0-based.
Rechaza slots diferentes, verifica SHA del manifest y fija el nombre del reloj
común source_time_s; no modifica la transformación ni los timestamps ni inventa
mediciones. Ajustar/revisar la correspondencia del reloj con evidencia antes de
analizar. El servidor comprueba límites de trials dentro del segmento/hash/slot
al inspeccionar y guardar. Un archivo archivado no revalida video físico al abrir.

El resultado muestra cobertura/media/soporte común y energía/trabajo parcial sólo
paraW. No calcula calorías, ratios de eficiencia, fatiga o correlaciones causales.
R12: si cambiás el protocolo mientras llega una inspección o una carga archivada,
la respuesta anterior no se aplica y aparece un aviso para repetir la operación.
Esto también protege la reapertura CSV y el vínculo de manifest EVAL. Guardados
ya publicados permanecen en la lista; no se cambia su contenido por editar la web.

Investigación → R12 → **Sensibilidad del reloj R12**: configurar deltas JSON que
incluyan cero, comparar cobertura original y pareada, guardar/reabrir archivos y
exportar/importar sólo offsets. Conserva rate, muestras, exclusiones e intentos;
no elige sincronización automáticamente. Ver [receta/semántica y controles](../../research/laboratory/r12_clock/README.md).

R12 JSON: una lectura raw negativa de frecuencia cardíaca o potencia metabólica
requiere `excluded_causes` en la misma muestra y canal para poder conservarse.
Ejemplo: `"values":{"hr":-999},"excluded_causes":{"hr":"sensor_error_code"}`
dentro de una muestra con inventario completo de canales. No cuenta como medición
válida: excluye ambos intervalos adyacentes. Sin causa se rechaza; NaN/Infinity
siempre se rechazan. CSV no incorpora exclusiones por fila; usar JSON para ese caso.

**Guardar corrida R12** congela request/result/manifest bajo
`$DATA_DIR/research/r12-measurements/<content-id>/`. Código actual recomputa;
histórico queda identificado como integridad solamente. Descargas locales, sin
upload. Envío pendiente se conserva en sessionStorage antes del POST; recuperar,
exportar o descartar explícitamente tras recargar. Fallos de escritura conservan
staging `.pending-*` diagnóstico; reintento no lo declara completo ni lo sobrescribe.

Ver tabla variable→instrumentación→incertidumbre y experimento vinculado a EVAL en
`research/laboratory/R12_MEASUREMENT_PROTOCOL.md`. Faltan mediciones/participantes,
hardware/adapters y evidencia de sincronización; no se inventaron datos para el
video corporal disponible. No cambia presets/defaults del instrumento ni R24.

### R13 · Predicción en tomas/personas/tareas reservadas

Investigación → **R13 · Predicción en fuentes reservadas**. **Cargar control
sintético R13** permite correr y comparar baselines sobre dos secuencias conocidas.
Editar historia, horizonte, componentes, ridge, centrado/z-score train, gap,
embargo y reserva. Shuffle de objetivos train y prefijo de adaptación opcionales.
Train+prefijo y sólo prefijo conservan modelos originales y excluyen el prefijo
para puntuación de todos los modelos. Ningún control cambia las voces/audio live.

Guardar/importar settings portable transporta sólo opciones de análisis/reserva;
el experimento completo (datos/roles/grupos/tarea/equivalencias) es JSON aparte.
Import nativo hasta16MiB/20000observaciones. Para features corporales: cargar un
control, quitar ambas secuencias, **Añadir secuencia desde EVAL verificado**, ID /
corrida / segmento / señales 2..16 con misma unidad, y grupo/tarea declarados.
Congelar una secuencia train y otra test, con mismos IDs ordenados y unidades.
No inventar identidad a partir del person_slot. La equivalencia de tarea se declara
antes de correr. Dentro de la misma toma, train debe preceder test con embargo;
dos presets superpuestos no son reserva. Para otras reservas recordings deben
ser distintos; subject/task requieren también grupos/tareas declarados diferentes.

**Correr transferencia R13** lanza worker separado, muestra estado/métricas/soporte.
Cancelar, abrir request y descargar outputs o **Repetir corrida R13** (código actual).
Los artefactos quedan en `$DATA_DIR/research/r13-heldout/<id>/`. Comparar hashes de
outputs repetidos; integridad al descargar no es recomputación científica. Fixtures
no son mediciones humanas. Modelos y MSE están en las unidades de features, sin
ranking de cuerpos, intención, eficacia, aprendizaje, beneficio o prótesis inferidos.
Histórico indica code_matches_current; no se promueve silenciosamente.

Protocolo completo/controles/dependencias: `research/laboratory/R13_TRANSFER_PROTOCOL.md`.

El checkbox **Control no lineal: ridge cuadrático R13** añade productos/cuadrados
de la historia, ajustados únicamente con train, también para prefijo/shuffle si están
elegidos. Default apagado; export/import de configuración conserva la opción.
Máximo features × historia de24, sin truncar silenciosamente. **Cargar recurrencia
cuadrática R13** ofrece un control positivo sintético conocido; no abre video ni
demuestra transferencia corporal. Los resultados añaden columnas cuadráticas sobre
los mismos objetivos. Elegir parámetros mirando test es exploración; reservar otra
toma antes de conclusiones. Mismo ridge no significa misma complejidad de modelos.

### Reutilizar ajustes del comparador

En **Comparar**, guardar un perfil de procesamiento con nombre; cargarlo recupera
reloj de control, historia previa, presupuesto por tanda y opciones PCM. Queda en
estado local y se puede descargar como JSON, pegar y aplicar sobre otras fuentes.
No incorpora selección de presets, cuerpos, segmentos/calibración ni identidad
del renderer. No inicia cálculos ni cambia una corrida congelada: repetir/continuar
conserva su request. Preparar JSON toma controles actuales; aplicar modifica sólo
esos controles. Si los editás durante una carga demorada, se conserva tu edición.
La UI carga los bancos de investigación al abrir la pestaña: el bundle cotidiano
queda separado. No cambia presets/defaults/R24 ni workspaces cotidianos.

### R07 · Recuperar atributos desde figuras sonoras

En la rama de desarrollo: Investigación → **R07 · Recuperación de atributos
reservados**. Validar el preset sin fuentes; agregar figuras R07 ya calculadas,
roles train/test, IDs de grabación/grupo y atributos/unidades declarados. Calcular
compara RMS completo, forma y magnitud sobre los mismos casos reservados. Se
guardan snapshots/resultados en `$DATA_DIR/research/r07-readout/<id>/`; pueden
reabrirse y recalcularse sin los PCM originales. No aplica cambios a live.

[Recorrido, contratos y control sintético](../../research/laboratory/r07_membrane/README.md#recuperación-de-atributos-en-casos-reservados).
Los IDs y atributos son declaraciones; falta validación con tomas independientes
y mediciones humanas. No se modificaron el launcher ni los defaults de R24.

Si la figura está ligada a EVAL, **Cargar señales para etiquetas R07** ofrece
la corrida/ventana exactas. Agregar señales, editar el perfil de mean/rms/std/
peak_abs y límites de cobertura/gap, y **Calcular atributos desde EVAL R07**.
El preset conserva `label_settings`; **Cargar perfil de etiquetas desde preset
R07** lo restaura. Agregar casos recalcula/verifica sus etiquetas al congelar el
dataset; editar targets manualmente retira la etiqueta de procedencia calculada.
Una cola de audio no se convierte en datos corporales. Esta operación es opcional
y conserva el juego live; no cambia selección corporal ni calibración.

## Sai–Oliva · Controles Fourier offline

Investigación → Controles Fourier Sai: ajustar muestras, Hz y semillas; Correr
banco ejecuta un worker separado del instrumento. Abrir banco recupera su
configuración y tablas; elegir escenario, semilla y descriptor. Exportar/importar
configuración guarda un preset JSON portable y no inicia una corrida al importarlo.
Cancelar detiene sólo el worker propio. Tres artefactos por corrida se descargan
y se conservan bajo `research/sai-fourier/` del data root.

Este corte usa los tres escenarios sintéticos de #97, escala torso .26 y defaults
del facade actual; no usa videos ni filtra movimiento live. Variar Hz/muestras
cambia frecuencias físicas (los tonos tienen 3/7/10 ciclos por bloque). Fases
compartidas conservan espectro cruzado global, pero no necesariamente I local.
Las tablas comparan medias/MAE sobre la intersección observada de tres condiciones;
sin soporte se muestra faltante. No usar MAE como pérdida monotónica de organización.

Requiere checkout del repositorio con `research/laboratory/sai_bridge/` disponible.
El instrumento puede arrancar sin ese bridge; intentar correr el banco informa la
ausencia. El loader usa namespace propio y no modifica sys.path ni los módulos
de tests. El verificador comprueba integridad/configuración/inventario/soporte;
no vuelve a ejecutar el banco ni autentica resultados rehasheados arbitrariamente.
Fuentes efectivamente importadas y versiones quedan en el manifest, sin exigir
igualdad de hashes entre entornos. El consumidor de Fourier corporal se describe abajo.

## R06 · Activación con espectros conservados

Investigación → Banco de activación → Desplazamientos circulares por voz R06.
Checkbox agrega tres vectores; editar `circular_shift_controls` JSON con un offset
de muestra por voz dentro del bloque de excitación. Exportar/importar configuración
conserva vectores sin correr. Tabla de desplazamientos compara espectros de entrada
y respuesta; selector Desplazamiento de traza muestra la traza del control elegido.
Esto rota tiempos dentro de un bloque offline, no pitch ni fases del audio live.
[Referencia y límites](../../research/laboratory/r06_activation/README.md#r06--desplazamientos-circulares-por-puerto--2026-10-03).


## Fourier corporal · tracking congelado de biblioteca

En Investigación → Sai–Oliva · Fourier corporal congelado, actualizar fuentes y
seleccionar una generación de tracking terminada y una persona. La identidad del
slot debe verificarse en el video; el selector no identifica quién es cada cuerpo.
Definir intervalo y ajustes JSON: canales [COCO-17, x/y], sample_hz, mínimo de
muestras, tolerancias, confianza, semillas y preset descriptivo sin plucks.
Declarar scale, scale_unit y scale_provenance para esa selección. Una escala de
torso aparente en frame_height no es una medida física en metros.

Preparar informa cobertura, exclusiones, bloques válidos y el bloque corto
descartado más largo. Si no hay bloques, revisar causas y elegir explícitamente
canales/intervalo/mínimo; no se rellenan gaps. Correr congela sus propias entradas
y ejecuta un worker cancelable separado del instrumento. Abrir la corrida muestra
bloque/semilla/descriptor, medias de las tres condiciones sobre soporte común,
espectros y cambios de longitudes. Sin soporte significa ausencia, no valor cero.

Descargar/importar conserva parámetros del método y no inicia un cálculo.
Cambiar fuente/persona limpia scale y scale_provenance; importar también los
limpia y exige volver a elegir persona. Completar esos dos campos para la
selección actual antes de preparar/correr. Si el JSON está incompleto, el cambio
de selección informa el error y conserva las ediciones, sin descartarlas.

Los artefactos bajo research/sai-body-fourier/ del data root incluyen tracking y
resultados privados; mantenerlos locales. El banco es offline y no modifica
tracking, transporte ni síntesis. Requiere el bridge integrado del checkout.
Ver VALIDATION.md para el recorrido automático con cache corporal real y sus
límites: salida de audio desconectada en esa instancia, sin aceptación humana.


## Comparador · continuar por tandas

En Comparación, Máximo de corridas por tanda permite repartir presets × segmentos
sin repetir lo ya terminado. Default 1024 conserva la matriz completa habitual.
Elegir 1 para una primera tanda corta; cuando aparezca partial, ajustar el límite
y pulsar Continuar comparación congelada. Se conserva el ID y la configuración
original, aunque se hayan editado los presets guardados después. El nuevo límite
aplica a las corridas que faltan y queda registrado como presupuesto de ejecución.

Tras cancelación o reinicio, el botón aparece sólo si existe manifest incompleto
con contrato de continuación. La corrida que quedó a medias comienza otra vez con
reset/historia previa; las completas se conservan. Ver comparación se habilita al
completar toda la matriz. Repetir configuración congelada crea una comparación
nueva; no equivale a continuar. Si cambió código de replay, tracking o un artefacto
completo, se informa el error y se requiere repetir como nueva. Detalles/API/CLI
en EVALUATION.md. No modifica el instrumento ni obliga a evaluar antes de jugar.


## Comparador · paquete seleccionable

Abrir Ver comparación y bajar hasta Preparar paquete local para revisar. Elegir
corridas; dejar desactivadas las opciones privadas para un resumen sin nombres,
rutas ni escala. Si querés pedidos de reproducción, traces o PCM, activarlos de
forma explícita. Ver contenido del paquete muestra archivos/tamaño y si hay esos
contenidos privados; Generar paquete local crea un ZIP cancelable. Descargar al
completar. Revisarlo antes de compartir: el resumen también contiene resultados
derivados que podrían ser sensibles. No publica nada ni copia video/tracking.

Descargar/importar preferencias conserva flags/presupuesto y limpia las corridas
seleccionadas al importar. El JSON portable no aplica selección de otra fuente.
La descarga antigua Informe y manifest sigue siendo completa y contiene rutas:
no equivale al resumen del paquete. El soporte común del resumen sigue siendo el
de la matriz original completa. Contrato y límites en EVALUATION.md.

R03 permite explorar sensibilidad al tiempo declarado de las marcas: elegir
comparación/señal/grupo y declarar intervalos realmente observados como antes.
Semiancho de sensibilidad temporal = 0 conserva el recorrido anterior. Para
examinar, por ejemplo, ±0.2 s alrededor del offset manual, poner semiancho 0.2 y
2 pasos por lado: se comparan cinco offsets, incluidos centro y extremos.
Hasta 8 pasos por lado (17 condiciones), semiancho ≤5 s y offsets totales ±10 s.
La configuración exportada conserva este método; no transporta persona/cobertura.

El resultado conserva la comparación nominal y añade una tabla de sensibilidad
con soporte común, marcas/candidatos elegibles, coincidencias y precisión/recall.
Los rangos son mínimos/máximos **entre los puntos muestreados**, sin elegir un
“mejor” offset ni afirmar significación. El barrido desplaza todas las marcas y
su cobertura juntas: representa una hipótesis declarada de offset global, no
latencia medida, incertidumbre por marca ni jitter independiente. Los controles
temporales manuales existentes permanecen separados. Gaps no se interpolan;
sin soporte/denominador se informa ausencia, no una puntuación perfecta o cero.

R12 → Importar tabla CSV R12: declarar proveedor, slot, reloj, canales y tarea en
el protocolo actual; abrir CSV UTF-8, definir mapeo de columnas/unidades temporales,
e inspeccionar. Guardar y usar conserva primero original + mapeo + metadatos en
`<data-dir>/research/r12-csv-imports/` y carga sus muestras en el análisis normal.
Mapa portable exportable/importable; fuentes y calibración se declaran aparte.
Lista y descargas permiten recuperar originales/conversiones. Ver protocolo
`research/laboratory/R12_MEASUREMENT_PROTOCOL.md`. La plantilla permanece
sintética hasta una declaración explícita; importar no conecta un sensor.

R01 sintético o corporal → Predictores: activar Armónicos declarados, fijar
fundamental de movimiento en Hz y ratios separados por coma; se aplican al salir
del campo. Ajusta sin/cos + DC con ridge sobre pasado. Para un control positivo
sintético elegir `Control con ratios armónicos declarados`; sus frecuencias son
conocidas deliberadamente. En corporal elegir señales de igual unidad como antes;
clocks/gaps y soporte siguen explícitos. No son frecuencias de síntesis ni cambian
voces/presets. Configuración JSON porta método. Datos/traces permiten inspeccionar
el tiempo objetivo estimado frente al observado; no se optimizan frecuencias por
los errores. Banco y límites en research/laboratory/r01_grassmann/README.md.

Los resultados R01 con armónicos muestran ahora diagnóstico de elegibilidad por
origen y objetivos puntuados, por control. Ventana insuficiente o frecuencias
fuera del límite del reloj pasado se explican aparte del MSE Sin soporte. La
media/máxima diferencia entre tiempo objetivo estimado y observado ayuda a revisar
relojes irregulares; no mide latencia de tracking/audio ni sincronía física. Un
commit es una predicción para un objetivo futuro, por lo que no sumar commits y
objetivos puntuados como observaciones independientes.

CSV R11/R12: Formato temporal permite tiempo numérico o ISO 8601 con zona horaria.
Para ISO, completar origen de cada archivo y revisar offset/rate del protocolo:
se aplica a segundos relativos **después** de restar ese origen. Export/import de
mapeo portable limpia el origen; abrir el import archivado conserva la entrada
original. [Contrato y ejemplo](SENSOR_CSV_TIME.md). Sin detección ni sincronía
inferidas; el formato numérico existente y los defaults musicales se conservan.

### Sensores CSV sin columna de índice

Investigación → R11 o R12 → importación CSV: declarar canales, unidades y Clock,
elegir Índice CSV → Numerar filas desde cero si el archivo no tiene contador,
y mapear la columna temporal real. Inspeccionar antes de guardar/aplicar.
La numeración no detecta muestras perdidas del dispositivo; tiempos y faltantes
permanecen declarados. Default sigue columna del archivo. Formatos/versiones y
presets portables en [SENSOR_CSV_TIME.md](SENSOR_CSV_TIME.md).

### R08 · Verificar el mapeo sobre el frame original

En Soga visible, elegir video de biblioteca y Preparar anotación. En Evaluar
tracking de extremos elegir referencia/corrida compatibles. Mostrar frame
original habilita el PNG exacto bajo semillas/etiquetas del frame inicial;
Ocultar vuelve al esquema. Cambiar selección limpia/cancela la vista. Si el
video preparado no coincide en hash/dimensiones/reloj, el botón queda bloqueado.
No cambia borrador, correspondencias, métricas ni sonido; ayuda a revisar
visualmente antes de declarar semilla→extremo. Referencia sin anotación inicial
se informa sin trasladar extremos de otro tiempo. Imágenes sólo locales.

### R09 · Exploración multivista inicial

Investigación → Observaciones y relojes → Pares de cámaras calibradas. Cargar
control sintético para probar sin hardware; para datos propios importar Request
JSON con píxeles ya sin distorsión, cámaras K/R/t en metros, correspondencias,
calibración y relojes explícitos. Ajustar tolerancias y Reconstruir pares.
Revisar inferidos/faltantes y causas; no llamar observado al 3D resultante.
Exportar resultado conserva entradas/método; export/import de ajustes conserva
sólo umbrales, sin transferir cámaras/calibración/cuerpo/relojes. Import no corre.
Usar stream carga su contrato en R09 como declaración para validar/guardar;
conservar resultado completo aparte para repetir triangulación. No conexión
a HarMoCAP live ni dispositivos automática. Ver README R09 para CLI/límites.


Para guardar el cálculo multivista completo, usar **Guardar y reconstruir multivista
R09** bajo el preview. Sigue en worker aunque cierres la pestaña; Cancelar detiene
el hijo propio y cerrar servidor detiene sus workers. Si se pierde respuesta, usar
Recuperar inicio: conserva los inputs originales en IndexedDB y la misma clave,
también al recargar, sin duplicar cálculo. Descartar sólo borra el intento local;
no cancela una corrida que el servidor haya recibido. Actualizar lista y Abrir
recuperan resultados sin recalcular. Abrir restaura cámaras/calibración/relojes
específicos de esa corrida; no es un preset portable. Repetir crea otro ID y
Verificar recálculo requiere implementación/entorno coincidentes. Descargar
request.json, result.json y manifest.json mantiene el paquete local completo.


Si recargás durante un cálculo multivista, elegir **Seguir cálculo multivista ID**
en el inventario para retomar su estado y acceder a Cancelar. No inicia otra corrida.
Si editás inputs durante Abrir, la apertura tardía se descarta; volver a abrir
explícitamente reemplaza la edición. Un intento local inválido permite Descartar;
esto sólo limpia IndexedDB, no cancela cálculos del servidor.


Para comparar un cálculo multivista sin perder su origen: en la fila completa,
**Guardar stream con procedencia multivista ID**. Si falla la respuesta, repetir
ese botón recupera la misma conversión (también tras reload). Se muestra el ID y
aparece en conversiones R09. En Comparación espacial elegir Conversiones guardadas,
Actualizar conversiones y seleccionar referencia/candidato. Admitir puntos inferidos
es opt-in; relojes/marcos deben ser compatibles. La conversión conserva hashes del
cálculo completo; guardarla/reabrirla no recalcula DLT ni valida cámaras físicas.


R10 → Registros de transporte → Archivo local: **Conservar borrador en navegador**
guarda una copia independiente del ensayo actual (sin medios) que permanece al
cerrar la pestaña. Exportar descarga JSON; Restaurar lo coloca como borrador en
esta pestaña, sin reproducir, enviar ni alterar un envío pendiente. Guardar borrador
de transporte es la acción separada para persistirlo en servidor. Borrar archivo
local sólo borra esa copia. Preparar otro ensayo no borra archivos conservados.
Datos del sitio/origen/navegador determinan acceso; exportá para conservar copia
independiente. 4MiB por snapshot/64MiB total; fallo de storage se informa.


### Verificación R05 con fuente corporal congelada (desarrollo)

El fixture `tests/laboratory_ui_fixture.py` permite `--read-frozen-evaluation`
junto a `--frozen-evaluation-request <job/request.json>` y
`--frozen-cache-root <directorio-cache>`. Usa esa EVAL existente sólo para lectura;
iniciar/repetir/resumir/cancelar EVAL quedan bloqueados. El `--root` de la prueba
debe ser un directorio nuevo; allí se generan R05 y estado de sesión separados.
No copia video/cache/artefactos EVAL ni ejecuta pose nueva. Mantener comandos/rutas
corporales locales. Audio del fixture sólo registra controles, no abre dispositivo.

Con el fixture y UI de producción corriendo, ejecutar desde laboratory-ui:
`LAB_R05_BODY_URL=http://127.0.0.1:<puerto> PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/resonatorBodyNetwork.spec.ts`.
`LAB_R05_BODY_START`/`LAB_R05_BODY_END` ajustan segmento dentro de la EVAL (defaults
10–16s); se genera comparación de dos mecanismos a8000Hz/seis voces/cola0.5s,
con positive_delta para el resonador. Presets/defaults live no cambian. Prueba
seeks/pausa/offset/cola, video original, pose observada causal y figura para ambos
brazos con audio muted. Es verificación software, no escucha/sincronía física.


R04 puede probarse con el mismo fixture de sólo lectura: seleccionar una EVAL
que ya contenga torso_scale/calibration_provenance, no completar campos faltantes.
`LAB_R04_FROZEN_BODY_URL=http://127.0.0.1:<puerto> PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalFrozenBodyNetwork.spec.ts`
desde laboratory-ui. Segmento configurable por LAB_R04_BODY_START/END; defaults
usan la fuente completa hasta120s. Para probar bloqueo de otra EVAL sin escala,
levantarla en fixture separado y añadir LAB_R04_UNSCALED_BODY_URL. Tests necesitan
inputs explícitos y no calibran cuerpos ni transfieren escala entre evaluaciones.

### Comparar corridas R13 guardadas

Investigación → R13 → **Comparar corridas R13 sobre soporte común**. Elegir2–6
corridas de las mismas secuencias congeladas; primera seleccionada es referencia.
Pueden variar parámetros/prefijo, pero no observaciones, unidades, grupos o tarea.
**Comparar soporte común R13** muestra pares compartidos, exclusiones y MSE/deltas
sobre esos pares; no compara promedios de tiempos distintos. Sin pares idénticos
no hay puntuación. **Guardar comparación R13** descarga soporte/procedencia/settings
localmente; no recalcula tracking, ajusta modelos ni modifica el instrumento.

### Ver la geometría colectiva en vivo

En **Figura → Geometría del movimiento**, elegir **Proyector del subespacio**
o **Base y modos**. Usar un modelo local, relacional, angular o colectivo y
calibrar el cuerpo; baseline no calcula este subespacio. La vista explica si
falta soporte o la ventana está calentando, sin inventar una matriz.

**Ejes visibles de la geometría** permite mostrar2–34 ejes del vector de
velocidades seleccionado en Modelos. Recortar la imagen no cambia el cálculo.
El proyector muestra relaciones entre ejes; la base muestra ejes×componentes.
Colores con escala fija[-1,+1], sin normalizar cada frame; amplitudes/residuo y
ángulos quedan visibles junto a los valores originales. No representa posición
3D del cuerpo ni demuestra HIT. Las seis voces siguen siendo independientes
del número de componentes. Guardar el preset conserva vista y límite de ejes
para otra fuente, sin incluir escala corporal. Default **Apagada**; no cambia
audio, fases, ruteos ni historial.

### Comparar corridas R01 guardadas

Investigación → **Comparar corridas R01 guardadas**: elegir2–6 corridas completas
con las mismas entradas/reloj/unidades/transformaciones. La primera elegida
es referencia. Default **Mismo origen y objetivo**; al variar horizonte puede
no haber pares idénticos. **Mismo objetivo, orígenes pueden variar** permite
contrastar esos errores, conservando orígenes individuales en el JSON. No
interpretarlo como comparación con la misma información disponible al pronosticar.

**Comparar soporte común R01** separa original/rotación/shuffle; muestra soporte,
exclusiones, MSE y delta contra primera corrida para familias compartidas.
Cambiar selección/soporte limpia la tabla anterior. **Guardar comparación R01**
descarga JSON local con soporte/orígenes/configuraciones/procedencia. No reajusta
modelos ni toca tracking/audio/preset. Archivos antiguos sin origen archivado
se rechazan explícitamente; no se reconstruye un origen supuesto.

### Comparar candidatos R03 de centros o señales alternativas

Investigación → R03: crear corridas por señal usando el mismo corte de marcas,
grupo/cuerpo/generación, cobertura de observación, tolerancia y offset.
**Comparar señales o centros R03** selecciona2–6 corridas completas; muestra
señal/unidad/umbrales, cobertura disponible, marcas/candidatos comunes, matches,
precisión/recall y exclusiones. Todas se restringen al soporte observado común.
Sin soporte hay ausencia de puntuación. **Guardar comparación R03** descarga
intervalos/candidatos/procedencia localmente. No decide un centro causal ni
recalcula pose/audio. Marcas humanas y cobertura no se fabrican.

### Ajuste de clickeo y colectivo (2026-10-04)

Los presets de fábrica 02–05 ahora dejan pitch/fase desactivados y suavizan gain
30 ms, siguiendo la referencia afinada. Pitch/fase siguen disponibles como ruteos
explícitos. No cambian el realce ×10, transientes ni los presets baseline aceptados.
Sólo se actualizan ejemplos guardados idénticos a la versión de fábrica anterior;
las configuraciones modificadas se conservan.

Los ejemplos colectivos 05/11 usan `collective_support=observed`: el subespacio
se calcula sobre coordenadas realmente observadas en común en la ventana causal,
sin rellenar huecos. Figura indica ejes excluidos. `fixed` conserva la exigencia de
todas las articulaciones seleccionadas. Cambiar a colectivo desde Modelos propone
`observed`; ambos modos se pueden elegir desde ese panel. La velocidad global
usa articulaciones observadas en ese instante y no se presenta como modo PCA.

### Filtrar saltos de tracking

En Modelos, activar **Filtrar glitches de tracking**. Ajustar mediana causal,
suavizado y aceleración máxima por articulación. La sesión actual de Nicolás lo
prueba con mediana de 3 cuadros, respuesta de 50 ms, caderas 35 y muñecas 240 T/s².
El control de corrección de caderas atiende intercambios de etiquetas, no cambios
reales de cuerpo. Figura permite **Ver esqueleto crudo en vez del filtrado**.
Los ajustes se guardan con el preset; apagar el filtro recupera la entrada original.
No se recalcula ni sobrescribe tracking. [Funcionamiento y opciones 3D](TRACKING.md).
