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
