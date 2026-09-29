# Evidencia de la primera iteración local

2026-09-29, Legion. Esto verifica software e integración; **no registra una escucha
ni aceptación humana** y no es una evaluación formal de HIT o eficacia corporal.

## Pruebas

- Weaver: suite general **229 tests + 4 subtests**, 117,68 s. Después de añadir
  identidad de control en telemetría: **45 tests del laboratorio**, 5,10 s.
- Shaper: **35 tests** de laboratorio, audio y estado, 8,72 s. Incluyen
  reconstrucción desde telemetría con 1/6/32 voces, continuidad, lease y silencio.
- Web: build TypeScript/Vite y **6 pruebas Playwright**. La prueba real comprueba
  avance de video, edición sin detenerlo, revisión efectivamente consumida por
  audio, arrastre de macro y píxeles dibujados en WebGL. Incluye el caso en que
  los esquemas llegan después del primer estado de sesión.

La cámara física produjo captura/inferencia con frames recientes, sin error del
worker en el smoke; después se cerró. No se grabó cámara ni micrófono.

## Fuente real y cache

Se extrajeron cuatro fragmentos locales de 12 s: perfil, espalda, frente y movimiento
sin soga. H.264, 540×960, rotación incorporada, sin audio original. Suman ~21 MB;
el original grande no fue copiado. Los medios y tracking no forman parte del repo.

| Fragmento | Frames | Frames con cuerpo observado |
|---|---:|---:|
| Perfil | 360 | 359 |
| Espalda | 360 | 360 |
| Frente | 359 | 359 |
| Sin soga | 359 | 359 |

«Cuerpo observado» significa al menos un joint observado en alguna persona; **no**
equivale a todos los joints correctos ni a exactitud de pose validada manualmente.
La primera reapertura frontal reutilizó el cache (2,08 s, incluido probe/hash).
Los cinco modelos alcanzaron seis voces efectivas sobre el frontal, sin errores de
runtime. Colectivo y propagación llegaron a estado observado.

### Error GPU encontrado y recuperación

Seguimiento: [issue #31](https://github.com/AlterMundi/harmonic-weaver/issues/31).

Una extracción forzada de espalda con `device=auto` falló en frame 166 por
`CUDA error: an illegal memory access was encountered`. No se determinó la causa
de bajo nivel; no se atribuye sin evidencia al video, modelo o driver.
La generación anterior de 360 frames quedó intacta y se reabrió con cache hit.
Reprocesar con `device=cpu` explícito produjo una generación completa de 360 frames.
Esa configuración tiene su propia clave de cache; no se mezclaron silenciosamente
resultados CPU/GPU. Si se repite el error, seleccionar **cpu** en percepción y
reprocesar. Un worker fallido no publica el prefijo parcial como cache completo.
Un segundo forzado CPU reemplazó su generación anterior; reabrir produjo cache hit.
El mismo preset portable se aplicó en los cuatro fragmentos con nueva calibración
explícita en cada fuente, seis voces activas y silencio comprobado después de pausar.

## Salida de audio

JACK sobre PipeWire, salida estéreo integrada, 48 kHz, bloques de 256 frames.
Se conectaron explícitamente los dos puertos de Shaper a un capturador de prueba
sin conexión a micrófono. La ruta normal hacia la salida integrada quedó conectada.

- RMS previo: 0.
- RMS durante movimiento: 0,03606; pico: 0,11401 (escala completa = 1).
- RMS posterior a pausa/liberación: 0.

Esto prueba señal en los puertos de salida y ausencia de voces colgadas al pausar.
No sustituye escuchar los altavoces. El launcher prefiere JACK porque el camino
ALSA `pipewire` tiene antecedentes de callbacks activos sin salida útil en este host.

## Prueba prolongada

600,10 s de video cacheado en loop, modelo colectivo, con cambios web durante la
prueba: 2234 observaciones de estado, 51 epochs de transporte, seis voces máximas,
**cero errores** de runtime/cliente de audio observados.

| Medida de software (ms) | p50 | p95 | p99 | máximo |
|---|---:|---:|---:|---:|
| Costo de tick de análisis | 9,45 | 37,19 | 50,74 | 117,83 |
| HTTP de control, ida/vuelta | 1,38 | 9,77 | 21,99 | 49,32 |
| Control preparado → primer bloque que lo consume | 14,45 | 27,92 | 33,25 | 84,68 |
| Edad de telemetría al consultar Weaver | 31,97 | 56,08 | 67,49 | 95,31 |

Control→bloque empieza al entregar targets al cliente Shaper; excluye preparación
del modelo y gesto/cola del navegador. La identidad de control se toma atómicamente
con los parámetros del bloque, no se deduce de un ACK HTTP. Edad de telemetría no
incluye pintura del navegador ni latencia del DAC/altavoz. No se midió latencia física
captura→sonido ni audio→luz con instrumentación. Los máximos muestran picos que
conviene seguir investigando; no se afirma cumplimiento físico de las metas.

## Límites para el primer feedback

- Tracking de cámara es 2D; el subespacio colectivo puede tener muchas dimensiones
  latentes, pero no convierte las observaciones en pose física 3D.
- Cache de archivo se carga en memoria. Para fuentes extensas conviene usar
  fragmentos durante esta iteración; no se ensayó cargar el tracking de 98 minutos.
- Evaluadores/centros son proxies cinemáticos. El score retardado es evidencia de
  mejora predictiva respecto del baseline elegido, no causalidad.
- Figura usa osciladores efectivos antes de shape/limiter; no modela una placa
  cimática física ni todos los parciales generados por procesamiento no lineal.
- Escucha, comodidad al moverse y aceptación humana siguen pendientes.

Grabación opcional, comparación formal y sensores conservan sus issues y agenda.

### Reactividad: primera escucha humana (2026-09-29)

Nicolás reportó que la primera versión responde mucho menos que el instrumento
anterior. La aceptación sonora sigue pendiente. En el fragmento frontal local,
reproduciendo el tracking guardado con el controlador preservado, el preset
baseline con plucks produjo ganancias medias por zona
[0.0062, 0.0055, 0.0131, 0.0089, 0.0157, 0.0427]; con plucks desactivados,
[0.3044, 0.2478, 0.2029, 0.4350, 0.1330, 0.4395].
Son ganancias del controlador, antes de normalización polifónica y salida física,
no una medición de volumen percibido. Las velocidades medias fueron idénticas.
Caderas, hombros y codos dispararon un solo impulso en el fragmento: la histéresis
del pluck requiere bajar del umbral de rearme, y movimiento continuo no garantiza
nuevos ataques. Esto explica una respuesta escasa en este caso, sin demostrar aún
qué configuración exacta se usó en la comparación histórica.

Se incorpora «01b · Instrumento original / movimiento continuo», con el mismo
controlador baseline y plucks desactivados. El preset original se conserva.
Próxima comparación humana: mismo fragmento, misma salida y nivel, alternar 01/01b.
Si se desea mantener articulación percutiva durante flujo continuo, estudiar
disparos por cambios de aceleración o mezcla continuo/impulso; no introducir un
reloj de retrigger que invente eventos corporales.

### Clics durante activación y cambios de movimiento

La escucha humana detectó clics repetidos con respuesta continua. Shaper aplicaba
ganancia y offset de fase como escalones entre bloques y omitía el último bloque
de algunas colas. Para voces del laboratorio se interpolan ganancia efectiva
(incluida normalización polifónica) y offset de fase por el arco corto, muestra
a muestra durante un bloque. La cola final se renderiza antes de retirar la voz.
A 48 kHz/256 muestras la transición dura 5.33 ms. El silencio explícito con
release=0 conserva su semántica inmediata.

VoiceFrame informa gain/phase_rad al inicio del bloque y gain_end/
phase_offset_delta_rad para reconstruir la transición; la figura sigue usando
el estado efectivo inicial, no el objetivo sin renderizar.
Pruebas: reconstrucción PCM de 1/6/32 voces y continuidad en activación a fase
de pico, cambios grandes de ganancia/fase y liberación. Falta confirmar por
escucha con la R24 si esto resuelve todos los clics percibidos.
