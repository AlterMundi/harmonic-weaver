La figura debe integrar todos los armónicos que están sonando y ser precisa y atractiva. No preservar el aspecto antiguo ni reemplazar la composición polifónica por un par de señales/armónicos.

## Punto de entrada

Tines `drawLissajous` muestra la suma de fasores; usa fundamental visual fija y un punto por reloj de pared, que no son requisitos. Shaper audio_engine.py conoce fases/envelopes reales; api.py transmite parámetros target, insuficientes para equivalencia durante ataque/release. Registrar fronteras de señal.

## Implementación

- VoiceFrame con sample index/rate, timestamp, IDs, freq real, fase integrada y gain efectivo incluyendo envolvente/normalización. Snapshot en borde de bloque, publicación fuera del callback; incluir voces en release.
- Consumidor web: z(τ)=Σ a_i exp(j(2π f_i τ+φ_i)), ventana editable en segundos/períodos y todas las voces activas. No imponer cierre a frecuencias detuneadas.
- Vista conjunta, componentes/fasores opcionales e historia de figuras. WebGL con antialias, trazo legible, luminancia/persistencia/escala/paleta configurables. Vista performance limpia e inspector preciso.
- Muestreo de curva según frecuencia/ventana con límites de costo y calidad visible. Normalización visual no oculta amplitud real.
- La UI identifica si muestra fasores de osciladores o PCM final. Waveshaping/limitación puede añadir componentes que la suma de osciladores no representa. No llamarla simulación de membrana.
- Extrapolar fase solo desde timestamp válido con lease; desconexión limpia o congela con indicación. No inventar movimiento decorativo como si fuera fase sonora.

## Pruebas

Silencio, una voz, seis/32 voces, ratios simples, detune, fase, ataque/release, mute/solo, cambio de fundamental y pérdida de telemetría. Fixtures numéricos de curva más prueba visual y recorrido real con Shaper. Alinear con el tiempo sonoro, no solo con target HTTP.

La telemetría en Shaper se publica mediante su repo/PR; el renderer vive en Weaver. Coordinar formato mediante LAB-01 y usar fixtures para avanzar en paralelo.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-04 -->
