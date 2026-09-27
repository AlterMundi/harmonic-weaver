---
project: harmonic-weaver
title: "ADDENDUM — La rejilla f1/2: el detuneo máximo aterriza en la serie armónica de la sub-fundamental"
type: design-addendum
tags: [research, movement-consonance, addendum, detuning, subharmonic, just-intonation, hit, design]
date: 2026-09-27
confidence: high
supersedes: "CROSS_REPORT §A.6 (riesgo de segregación), §G riesgo #1, §H decisión límite-por-armónico"
---

# ADDENDUM 2026-09-27 — La rejilla f1/2

> Origen: aclaración de Nicolás tras leer el pack. Dos correcciones de intención +
> un descubrimiento matemático verificado que reescribe parte del diseño.
> Los reportes crudos NO se modifican (son sagrados); este addendum es aditivo y
> el CROSS_REPORT §G/§H queda enmendado por referencia a este archivo.

## 1. Las dos aclaraciones de Nicolás (texto y traducción al diseño)

### 1.1 La disonancia es desviación intencional de la inercia, no aspereza cualquiera

> "cuando yo me refiero a aceleraciones y desaceleraciones no consonantes quiero
> decir que respecto del movimiento que viene ocurriendo desde donde se inició el
> impulso algunas joints pueden en lugar de seguir su inercia natural por estar
> conectadas al sistema, frenar a proposito o acelerar en otras direcciones, esto
> debe notarse en la musica."

Traducción operacional:

- La referencia de consonancia por articulación NO es el beat global ni la
  suavidad cruda: es la **continuación inercial del impulso iniciado** — lo que
  la articulación haría si siguiera conectada al flujo del movimiento en curso.
- Disonante = desvío intencional de esa continuación: frenar a propósito
  (potencia firmada P=⟨a,v⟩ < 0) o acelerar en otra dirección (componente de
  aceleración no predicha por el modelo inercial/de cadena).
- "esto debe notarse en la música" = la desviación intencional es CANAL
  EXPRESIVO, no error a suprimir. El snap no debe borrarla; debe hacerla
  audible como posición en la rejilla (ver §2).

Consecuencia para las métricas (enmienda a CROSS_REPORT §B): las candidatas
(iv) continuidad de la transferencia de energía por cadena cinemática y
(v) error de predicción del modelo de movimiento pasan de complementarias a
CENTRALES — son las únicas dos que miden desviación-respecto-de-la-inercia-
propagada. (ii) PLV contra beat queda como término de acople rítmico global.
(i) SPARC baja de prioridad (mide suavidad, que ya sabemos que no es el
constructo). El modelo de predicción por articulación (v) debe incluir la
extrapolación balística simple (posición + velocidad actuales → posición
esperada) y el residuo normalizado es la "sorpresa" = drive candidato de d_j.

### 1.2 Detune = moverse a otra posición de la rejilla, posible OTRA NOTA percibida

> "Cuando yo digo detune igualmente me refiero a moverse del FX correspondiente
> pero no a que efectivamente suene desafinado, puede sonar justamente a que nos
> movimos a otra 'nota' en la percepción musical nuestra. El intérprete podría
> utilizar sus movimientos intencionalmente para afectar la armonía o las
> múltiples melodías interconectadas."

Traducción: el destino del detuneo no es "sonar feo" — es **modulación de
posición armónica**. El intérprete toca la rejilla con el cuerpo. Las
"múltiples melodías interconectadas" son las voces de las distintas
articulaciones recorriendo posiciones de la rejilla (ver §2.3).

## 2. El descubrimiento: la regla ±50% aterriza en la serie de f1/2 (verificado numéricamente)

### 2.1 La álgebra

La regla del diseño (R4/R5, verificada dos veces):

```
f'(n,d) = n·f1·(1 + d/(2n)) = f1·(n + d/2)      d ∈ [−1,1]
```

Reordenada, la forma reveladora: **f' = f1·n + (f1/2)·d** — el detuneo mueve
cada parcial en múltiplos de MEDIA fundamental. Con g = f1/2:

- d = 0 → f' = 2n·g → múltiplos PARES de g = serie original de f1
- d = ±1 → f' = (2n±1)·g → múltiplos IMPARES de g = las posiciones nuevas
- d intermedio → múltiplos no-enteros de g → entre rejillas (zona de batido/rugosidad)

### 2.2 Las posiciones extremas son intervalos justos (tabla verificada con Python, f1=40, g=20)

| k (múltiplo de g=20Hz) | Hz | ratio vs f1 | intervalo | posición |
|---|---|---|---|---|
| 1 | 20.0 | 1/2 | sub-fundamental | d=−1 en H1 |
| 2 | 40.0 | 1 | f1 | d=0 en H1 |
| 3 | 60.0 | 3/2 | **quinta justa** | d=+1 en H1 = d=−1 en H2 |
| 4 | 80.0 | 2 | octava (H2) | d=0 en H2 |
| 5 | 100.0 | 5/2 | **tercera mayor justa +8a** | d=+1 en H2 = d=−1 en H3 |
| 6 | 120.0 | 3 | 8a+5a (H3) | d=0 en H3 |
| 7 | 140.0 | 7/2 | **séptima armónica (blue note)** | d=+1 en H3 = d=−1 en H4 |
| 8 | 160.0 | 4 | 2 octavas (H4) | d=0 en H4 |
| 9 | 180.0 | 9/2 | **segunda mayor +2·8a** | d=+1 en H4 |
| 10 | 200.0 | 5 | H5 | d=0 en H5 |
| 11 | 220.0 | 11/2 | **undécima (alphorn, +35c)** | d=+1 en H5 |
| 13 | 260.0 | 13/2 | **decimotercera (sexta neutral)** | d=+1 en H6 |
| 15 | 300.0 | 15/2 | **séptima mayor +8a** | d=+1 en H7 |

Propiedades estructurales (todas verificadas aritméticamente):

1. **La rejilla consonante completa = la serie armónica de f1/2.** Pares =
   serie de f1; impares = serie extendida. El "detuneo máximo" NO es
   desafinación: es modulación a la serie de la sub-fundamental, y cada
   extremo es un intervalo justo de la serie natural.
2. **d=+1 en Hn ≡ d=−1 en Hn+1** (misma frecuencia): las celdas del continuo
   comparten bordes — el mosaico perfecto que R4 verificó tiene ahora
   interpretación musical: los bordes son las notas justas compartidas.
3. **Invariante de escala (HIT H6)**: la estructura es pura proporción — vale
   igual con f1=40.40 real del shaper. El diseño no depende de la fundamental.
4. La zona verdaderamente áspera (batido/rugosidad Plomp-Levelt) son los d
   intermedios NO enteros en la rejilla de g — el continuo entre notas.

### 2.3 Consecuencias de diseño

**(a) El riesgo #1 del CROSS_REPORT se invierte.** R4 recomendaba limitar el
detuneo por armónico (~±15-70 cents de banda fusional) para evitar la
segregación del parcial. La aclaración 1.2 dice que la segregación percibida
como "otra nota" es el RECURSO, no el fallo: en los extremos esa "otra nota"
es un intervalo justo de la serie de f1/2. La limitación por armónico queda
opcional (para modos suaves), no obligatoria. NUEVA DECISIÓN: ¿el sistema
ofrece ambos regímenes (fusional-expresivo limitado vs rejilla-f1/2 completa)
como parámetro de escena?

**(b) El snap tiene dos destinos.** El parámetro s de R5 se bifurca:
- snap a d=0 → serie de f1 (modo "tuned" original)
- snap a |d|=1 → impares de f1/2 (modo "extended series": quinta, tercera,
  blue note...)
- sin snap → continuo libre (zona de rugosidad entre rejillas)

El "grado de snap" de Nicolás es ahora: cuánta atracción hacia CUALQUIER
entero de la rejilla de g (pares Y impares). Implementación natural: pozo de
potencial periódico en d con periodo 2 (o fuerza de atracción proporcional a
distancia al entero más cercano de k=2n+d). Los transforms existentes del
weaver (gate+hysteresis, slew_limiter) siguen sirviendo; la cuantización pasa
a ser contra la rejilla de g completa.

**(c) "Múltiples melodías interconectadas" = las dos series entrelazadas.**
Con 9 articulaciones mapeadas, cada una en una posición d_j del continuo, el
sistema suena como un tejido de la serie de f1 (articulaciones en pares) y la
serie de f1/2 (articulaciones en impares). Un intérprete que lleva una muñeca
de d=0 a d=+1 modula esa voz de la fundamental a la quinta justa — gesto
melódico tocable con el cuerpo. La armonía resultante es de JUST INTONATION
por construcción (todas las posiciones de rejilla son ratios (2n±1)/2 · f1).

**(d) Lectura HIT del descubrimiento.** El continuo pares↔impares es análogo
al eje almacenamiento↔recuperación del Cap.10: los pares son la recurrencia
lockeada (serie de f1, régimen de almacenamiento); los impares son la serie
del acople a frecuencia mitad — una organización latente que la perturbación
bien colocada (el gesto intencional, Jpsh!) libera sin reescribir la serie
original. La sub-fundamental f1/2 existe como estructura latente en la rejilla
desde el principio; el cuerpo la activa. Esto merece validación con Mariano
(no forzar la analogía — marcarla ❓ hasta su lectura).

**(e) Prioridad de métricas reordenada** (ver 1.1): el drive d_j debe salir
primariamente del error de predicción inercial + potencia firmada (freno/bomba
respecto de la continuación del impulso), con PLV-beat como término de acople
global y la cadena cinética como contexto de propagación. El baseline
experimental (C.4) no cambia en su mecánica, pero el script de métricas debe
implementar el modelo de extrapolación balística por articulación como
métrica primaria — es la operacionalización directa de la definición de
Nicolás.

## 3. Enmiendas formales al pack

- CROSS_REPORT §A.6 y §G riesgo#1: enmendados por este addendum (la
  segregación a ±f1/2 es recurso, no riesgo; la rugosidad real vive en los d
  intermedios).
- CROSS_REPORT §B: prioridades de métricas reordenadas según §1.1/§2.3e.
- CROSS_REPORT §D: el snap de dos destinos (§2.3b) reemplaza al deadband
  único como diseño de referencia; θ/histésis siguen vigentes como parámetros
  de cada pozo.
- CROSS_REPORT §H: decisión "límite global vs por-armónico" se reformula como
  "¿ofrecer ambos regímenes como parámetro de escena?"; se AGREGA decisión:
  destino del snap (d=0 / |d|=1 / ambos / continuo).
- SYNTHESIS item 5: la "corrección" de R4 queda matizada por este addendum.
- Reportes crudos R1-R5: INTACTOS (regla de inmutabilidad del método).

## 4. Verificación

Aritmética ejecutada en Python durante la sesión 2026-09-27 (dos corridas:
tabla por armónico n=1..9 con d=±1, y tabla de la rejilla k=1..15 de g=f1/2
con ratios, cents y pasos). Los resultados de ambas corridas son los
transcriptos en §2.2. Fórmula verificada: f1·(n+d/2) ≡ n·f1·(1+d/(2n)).
