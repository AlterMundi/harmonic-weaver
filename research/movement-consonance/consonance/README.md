---
project: harmonic-weaver
title: "Consonance driver v1 — README de implementación"
type: code-readme
tags: [movement-consonance, driver, implementation, shaper, osc]
date: 2026-09-27
confidence: verified-by-execution
---

# consonance/ — driver v1 (prototipo de exploración)

Primer código ejecutable del modo consonancia. Dos archivos, stdlib puro:

| Archivo | Rol |
|---|---|
| `metrics.py` | cinemática por zona + matemática de snap/detune (sin I/O) |
| `driver.py` | fuentes (jsonl/OSC live) → métricas → OSC al shaper esclavo |

## Pipeline

```
HarMoCAP (jsonl o wire OSC :9000)
  → ZoneTracker: 9 zonas anatómicas sobre COCO-17
      pelvis(hip_mid)=H1 … under_navel=H2, navel=H3 (virtuales),
      shoulders=H4, head=H5, knees=H6, ankles=H7, elbows=H8, wrists=H9
  → por zona y frame (dt real de captured_at_us, NUNCA índices):
      surprise  = error de predicción balística (desvío de la inercia en curso)
      P = ⟨a,v⟩ = potencia mecánica firmada (freno < 0 / bombeo > 0)
      d_raw = sign(P)·min(2, surprise/p90)·(w_s + w_b·(2·brake_frac − 1))
  → snap_map(d_raw, snap, theta): pozo finito alrededor de d=0
      snap=0 → continuo puro; snap→1 → pozos duros; el desvío DEBE superar
      theta·snap para salirse del snap (Nicolás: "continuo con nivel de snap")
  → f'(n,d) = f1·(n + d/2)   [ADDENDUM: |d|=1 = impares de f1/2 = justa]
  → OSC /beacon/voice/{on,freq,off} al puerto esclavo del shaper (:9001)
```

## Por qué el puerto esclavo y no una capability nueva

El motor del shaper YA renderiza `params.freq` por bloque con fase continua
(`audio_engine.py` L242/L268-270) y `voice_on`/`voice_freq` aceptan frecuencia
ARBITRARIA; los resets a `f1·n` sólo pisan voces de envolvente
(voice_id = −10000−n). Un driver externo con voice_id = 7000+n posee las voces
con detune continuo → **cero cambios al shaper, cero bump de contrato**.
La capability nativa `/digital/harmonic/*/detune` queda para cuando el diseño
asiente (CROSS_REPORT §G). Verificado en código, no asumido.

## Uso

```bash
# Shaper (necesita --slave para escuchar /beacon/* en :9001):
cd ~/Projects/harmonic-shaper && .venv/bin/harmonic-shaper --slave
# (agregar --no-audio para probar en silencio; API en :8123 por defecto)

# Driver, replay de una sesión grabada a velocidad real:
python3 driver.py --source ~/Projects/HarMoCAP/examples/session_v1.jsonl \
    --snap 0.6 --f1 40.4

# Tabla seca (sin audio, imprime zonas a 1 Hz):
python3 driver.py --source sesion.jsonl --dry

# Live desde HarMoCAP corriendo (wire a :9000):
python3 driver.py --source osc --osc-port 9000 --snap 0.6

# Modos de snap: off | series (pozo en d=0) | grid (imanes en −1/0/+1) | both
python3 driver.py --source sesion.jsonl --snap 0.6 --snap-mode grid
```

Parámetros clave: `--snap` (0=continuo … 1=pozos duros), `--theta` (umbral de
escape, default 0.15 T), `--w-surprise`/`--w-brake` (pesos), `--pred-tau`
(horizonte balístico, default 0.15 s), `--f1` (default 40.0; el shaper real
usa 40.4), `--max-persons` (v1: 1).

## Verificado (2026-09-27)

- 720 frames de `session_v1.jsonl` reproducidos en tiempo real contra shaper
  `--no-audio --slave`: voces H1-H9 creadas, frecuencias DETUNEADAS visibles en
  `/api/state` (ej. H6 249.90 Hz vs nominal 242.4; detunes vivos de −498 a +80
  cents según zona y frame), `voice_off` libera, `panic` al salir limpia.
- Bugs encontrados y corregidos durante la verificación:
  1. **OSC strings sin NUL-terminator**: la dirección se decodificaba como
     `/beacon/voice/on,iffi` (typetag pegado) y el mensaje caía al default
     handler silencioso del shaper. Regla: string OSC = NUL y DESPUÉS pad a 4.
  2. Doble división por T en aceleraciones (vx ya está en T/s).
  3. d_raw sumaba el bias de freno como offset constante → zonas quietas
     quedaban en d=−0.45 en vez de 0. Ahora el carácter freno/bombeo MODULA la
     magnitud: d = sign·mag·(w_s + w_b·(2bf−1)).
  4. `python -m harmonic_shaper.main` no ejecuta nada (falta bloque
     `__main__`); usar el entry point `.venv/bin/harmonic-shaper`.

## Compromisos v1 (documentados, no ocultos)

- Ganancia por voz se actualiza re-assertando `voice_on`, que llama
  `record_strum()` en el shaper — throttled a cambios > `--gain-eps` (0.03)
  para no contaminar el estimador de período de strum. La vía limpia es la
  capability nativa de detune/gain (fase 2).
- El modo live implementa reset por stream_id + descarte monotónico + lease,
  pero NO el handshake estricto hello/calibration (el `osc_receiver_example`
  del kit sí). Aceptable para exploración; flagged.
- Gain = velocidad normalizada (soft knee). La "ganancia más elevada cuando el
  cuerpo absorbe el impulso y quedamos en otra velocidad resultante" (Nicolás)
  emerge naturalmente de esto: si el brazo arrastra al cuerpo, más zonas se
  mueven rápido → más ganancia total. Sin mecanismo dedicado todavía.
- 2D: la profundidad se pierde; sorpresa y potencia son proyecciones. El
  baseline con video lo va a mostrar.

## Siguiente (fase 2, cuando el diseño asiente)

- Capability nativa `/digital/harmonic/{n}/detune` en el shaper (contrato +
  golden) → ganancia y detune sin re-assertar voice_on.
- Escena `consonance` en el weaver (geometría = topología de zonas,
  activación = rutas/gains), respetando la regla de arquitectura.
- Protocolo baseline del ADDENDUM §C: clips experto/neutro/disonante →
  ratings ciegos → Spearman ρ para calibrar w_surprise/w_brake/theta.

## Integración en vivo — 2026-09-27

El lanzador común ahora selecciona el modo excluyente
`--scene kinetic-consonance`, con la ventana de cámara y tracking habitual.
Ver [guía de uso](../../../docs/KINETIC_CONSONANCE.md). El receptor conserva
el foco por slot, descarta secuencias repetidas y libera voces tras 2 s sin
datos; reinicia cinemática al cambiar de persona/stream. El cierre libera
sólo las voces propias, en lugar del panic global del prototipo original.

## Drone sostenido — 2026-09-27

A pedido del usuario tras escuchar el modo, las voces permanecen encendidas
en reposo: piso de ganancia 0.12, variación por movimiento hasta 0.45, fase
±45° según desvío cinético y suavizado de 200 ms. Gain/phase usan los controles
nativos de Shaper en 9002, sin re-disparar voice_on. Esta revisión reemplaza
el gating por velocidad y el compromiso de re-assertar voice_on de v1.

### Controles y feedback corporal (2026-09-27)

El launcher aislado sirve la UI en **http://localhost:8766**. Shaper expone
su estado técnico en http://localhost:8080/api/state; su raíz no es una UI.
El video permanece en la ventana HarMoCAP, con los mismos colores por voz
que el esqueleto web. Las estelas unen las posiciones medidas de cada joint,
se desvanecen hacia el pasado y se cortan ante una observación perdida.
El historial visual guarda hasta 24 poses; no introduce un buffer de audio.

F1 caderas, F2 hombros, F3 rodillas, F4 codos, F5 tobillos, F6 muñecas.
Cada par tiene sensibilidad, distancia al core y rangos de velocidad y
aceleración editables. El factor es `sensibilidad / (1 + caída * distancia)`.
Las distancias iniciales son 0, 1, 1, 2, 2, 3; son parámetros expresivos,
no distancias anatómicas inferidas. La velocidad, medida en largos de torso/s,
determina el gain: `min(1, velocidad * factor / rango_velocidad)` antes del
master y del techo de voz. Cero velocidad sigue dando cero sonido.

El desvío tonal usa el error firmado respecto de la predicción inercial:
`clip(2 * drive * factor / (tau² * rango_aceleración), -1, 1)`.
No equivale directamente al módulo de aceleración mostrado como diagnóstico.
Los rangos iniciales (0.6 T/s y 6 T/s²) son un punto de partida ajustable;
el p95 observado de las últimas 900 muestras ayuda a calibrar cada cuerpo.
También se controlan fundamental, fase, snap, master, silencio y solo por voz.
Snap inicia en cero. Las estelas sólo afectan la imagen.

Los parámetros se guardan en
`~/.config/harmonic-weaver/kinetic-consonance.json` (respeta XDG_CONFIG_HOME).
El tag local **kinetic-consonance-raw-v1** conserva el sonido anterior a estos
controles en ambos repos: harmonic-weaver `7aaa8c0`, HarMoCAP `4503393`.

### Articulación por impulsos

La UI inicia ahora con plucks: umbral de aceleración normalizada 0.15,
ataque 80 ms y cola 700 ms. Se dispara al cruzar el umbral y se rearma
al bajar de la mitad; aceleración sostenida no produce repetición.
Cada impulso añade una envolvente (hasta 32 por par), con entrada smoothstep
y caída cuadrática. La suma se limita a 1; la velocidad modula su amplitud
entre 20% y 100%. Por pedido posterior, queda una cola finita al detenerse;
tracking perdido o silencio global la cancelan. No hay grilla temporal.
La envolvente se actualiza también entre cuadros, sin volver a derivar la pose.
`Plucks = 0` vuelve al volumen crudo por velocidad, sin cola en reposo.
El launcher desactiva los generadores internos del sintetizador.

El launcher aislado inicia GPU y sólo UI web; `--window` recupera la ventana
de video, `--harmocap-device cpu` permite comparar. En este host el modo auto
ya utilizaba la RTX 2060; la captura observada era 720p a 10 fps, por lo que
no se atribuye una mejora de latencia no medida a este cambio.

### Corrección de respuesta en modo sin ventana

El launcher aislado usa ahora inferencia a 320 (override `--harmocap-imgsz 640`)
y desactiva `CUDA_LAUNCH_BLOCKING`, que antes forzaba sincronización de depuración.
HarMoCAP espera una señal del hilo de captura cuando no tiene ventana, evitando
el giro continuo entre cuadros; se mantiene un solo frame reciente, sin cola.
Los logs `[health]` muestran FPS y captura→envío (no latencia de audio completa).
En la sesión `live-consonance-light-gpu-20260927` se observó alrededor de 8 FPS
y 91 ms captura→envío tras warmup; el archivo `responsiveness.json` junto al
run registra una muestra de antigüedad de poses leída desde la API.
La GPU reportó 91–93 °C y thermal slowdown a 300 MHz durante el diagnóstico;
reducir resolución alivia la carga pero no resuelve la limitación térmica.
