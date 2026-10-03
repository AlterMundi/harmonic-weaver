---
project: harmonic-weaver
title: 'Matemática de la consonancia del movimiento: suavidad, coordinación y acople'
type: research-report
tags: [movement-consonance, smoothness, minimum-jerk, SPARC, LDLJ, coordination, relative-phase, HKB, Kuramoto, PLV, synchronization, arnold-tongues, dance-aesthetics, processing-fluency, kinetic-chain, harmonic-beacon]
date: 2026-09-24
confidence: high
---

# Matemática de la consonancia del movimiento: suavidad, coordinación y acople

**Marcas de confianza**: ✅ revisado por pares / fuente primaria · 📊 secundaria especializada · 📰 prensa/blog · ⚠️ controvertido · ❓ inferencia del agente.

**Contexto de uso (Harmonic Beacon)**: keypoints 2D COCO-17 a 30 fps por persona vía OSC; se busca un dato de "consonancia de movimiento" por articulación: cuando el movimiento de una articulación es eficiente/coordinado/rítmicamente acoplado, su armónico de una serie de 40 Hz suena afinado; el movimiento disonante lo desafina ±50 % del intervalo al armónico vecino. Este informe aporta la matemática: qué cantidades cinemáticas capturan realmente "eficiente, coordinado, fluido", con fórmulas y patologías.

---

## 0. TL;DR

1. ✅ **El modelo de jerk mínimo (Flash & Hogan 1985) predice trayectorias rectas con velocidad acampanada para alcances discretos, pero NO aplica al movimiento rítmico continuo** — que es exactamente el caso de uso del Beacon (danza, artes marciales). Aplicar métricas de suavidad de movimientos discretos a series rítmicas completas sin segmentación da valores inválidos (Balasubramanian et al. 2015).
2. ✅ **SPARC (longitud de arco espectral del perfil de velocidad) es la única métrica de suavidad que pasó las cuatro pruebas de validez** (independencia de forma, respuesta monótona a perturbaciones armónicas, robustez al ruido, monotonía con sub-movimientos) en la comparación sistemática de 32 métricas (Mohamed Refai et al. 2021, JNER Part 1). El jerk adimensional logarítmico (LDLJ) es válido pero MUY sensible al ruido; el número de picos es frágil.
3. ✅ **La coordinación interarticular se formaliza como fase relativa φ = φ₁ − φ₂ con el modelo HKB**: φ̇ = Δω − a·sin(φ) − 2b·sin(2φ) + ruido. Atractores en 0° y 180°; al subir la frecuencia de ciclo el atractor anti-fase desaparece por bifurcación (transición de fase de Kelso 1984), con fluctuaciones críticas (varianza de φ y tiempo de relajación divergen) cerca del punto crítico.
4. ✅ **Coordinación = phase-locking = la misma matemática de la consonancia armónica**: el modelo de Kuramoto (dθᵢ/dt = ωᵢ + K/N·Σ sin(θⱼ−θᵢ)) y su parámetro de orden r·e^(iψ) = (1/N)Σe^(iθⱼ) son estructuralmente idénticos al PLV de Lachaux et al. (1999), PLV = |1/N Σ e^(iΔφₙ)|. Un "acople de consonancia" más fuerte ensancha la lengua de Arnold: el sistema tolera mayor desafinación sin perder el lock — analogía directa con el parámetro de detuning del Beacon.
5. ✅ **Evidencia musical directa**: en cuartetos de cuerdas, el acople de balanceo corporal (Granger causality entre motion-capture de los 4 músicos) predice la calificación de "bondad" de la ejecución; los líderes asignados influyen más de lo que son influidos (Chang et al. 2017, PNAS).
6. ⚠️ **"Suave = bello" está discutido**: en danza, secuencias con perfiles de velocidad VARIADOS (más complejos, menos suaves) pero predecibles se juzgan MÁS placenteras que las uniformes (Orlandi, Cross & Orgs 2020, Cognition). La fluidez de procesamiento (Reber, Schwarz & Winkielman 2004) rige para acciones cotidianas, pero en arte opera la heurística del esfuerzo ("efecto Cirque du Soleil": lo difícil de reproducir gusta más). La consonancia debe medir coordinación/eficiencia, no suavidad cruda.
7. ❓ **Para el Beacon se proponen 5 métricas candidatas por articulación** (§6): SPARC ventaneado por ciclo, PLV contra el beat global, estabilidad de fase relativa en pares de miembros, continuidad de transferencia de energía proximal→distal, y error de predicción de un modelo armónico simple — cada una con fórmula, normalización, patologías y mapeo a d ∈ [−1,1].
8. ✅ **La derivación numérica amplifica el jitter de cámara ~×30 por orden a 30 fps**: el ruido blanco de posición de 1 px se vuelve ~30 px/s en velocidad, ~900 px/s² en aceleración y ~27 000 px/s³ en jerk por diferencias finitas crudas (§6.1); esto descalifica cualquier métrica basada en jerk crudo sin filtrado, y obliga a ventanear/filtrar antes de derivar.

---

## 1. El modelo de jerk mínimo (Flash & Hogan 1985)

### 1.1 Formulación

✅ Flash & Hogan, "The coordination of arm movements: an experimentally confirmed mathematical model", *J Neurosci* 5(7):1688–1703, 1985. DOI 10.1523/JNEUROSCI.05-07-01688.1985 (abstract fetchado en jneurosci.org).

La hipótesis: un objetivo mayor de la coordinación motora es producir **el movimiento más suave posible de la mano**. Formalmente, se define la función objetivo como el cuadrado de la magnitud del jerk (derivada tercera de la posición) integrado en todo el movimiento:

```
C = ∫₀ᵀ |d³x/dt³|² dt   →   minimizar
```

donde x(t) es la posición de la mano en el espacio extracorpóreo (no en espacio articular — el modelo solo funciona en coordenadas de la mano, ✅). La solución por optimización dinámica (ecuación de Euler-Lagrange con d³x/dt³ ⇒ condiciones de contorno en posición, velocidad y aceleración nulas en inicio y fin) es un polinomio de quinto grado. Para un movimiento de x₀ a x_f en duración T, con τ = t/T:

```
x(τ) = x₀ + (x_f − x₀)·(10τ³ − 15τ⁴ + 6τ⁵)
v(τ) = (x_f − x₀)/T · (30τ² − 60τ³ + 30τ⁴)
```

(Forma verificada contra la Ec. del perfil de velocidad de jerk mínimo citada textualmente en Mohamed Refai et al. 2021: v_mj(t) = d_t·(30t⁴/T⁵ − 60t³/T⁴ + 30t²/T³). ✅)

### 1.2 Predicciones (confirmadas experimentalmente en el paper de 1985) ✅

- Movimientos punto a punto sin restricciones son **aproximadamente rectos** con **perfiles de velocidad tangencial acampanados** (un solo pico, simétrico).
- Movimientos curvos (a través de un punto intermedio o alrededor de un obstáculo) tienen **porciones de baja curvatura unidas por porciones de alta curvatura**; en los puntos de alta curvatura la **velocidad tangencial se reduce**; las duraciones de las porciones de baja curvatura son aproximadamente iguales.
- El análisis es **puramente cinemático**, independiente de la dinámica musculoesquelética.

### 1.3 Soporte empírico y alcance

✅ La velocidad acampanada y las trayectorias rectas del alcance humano sano se replican desde Morasso 1981 y Flash & Hogan 1985 en adelante; es la "kinematics estereotípica" sobre la que se construyeron casi todas las métricas de suavidad (✅ Balasubramanian et al. 2015, Introducción: "nearly all existing measures are motivated by the stereotypical smooth kinematics of discrete arm movements... the single peaked bell-shaped speed profile"). La suavidad aumenta con el desarrollo neural, el aprendizaje motor y la recuperación post-ACV, y correlaciona con escalas clínicas (Fugl-Meyer) (✅ mismo paper). Se interpreta como resultado de minimización de esfuerzo (Harris & Wolpert 1998, citado ahí) y reduce la carga de control sobre el cerebro (✅ Mohamed Refai et al. 2021, Intro).

### 1.4 Fallas documentadas — crítico para el caso de uso del Beacon

1. ✅ **El movimiento rítmico NO es discreto ni jerk-mínimo.** Schaal, Sternad, Osu & Kawato, "Rhythmic arm movement is not discrete", *Nat Neurosci* 7:1136–1143, 2004 (PMID 15452580, abstract fetchado): con fMRI, el movimiento discreto recluta áreas corticales de planificación adicionales que el rítmico no usa, "even when both movement conditions are confined to the same single wrist joint" → los movimientos rítmicos "may require separate neurophysiological and theoretical treatment". Los movimientos rítmicos (caminar, masticar, rascarse) son filogenéticamente viejos; los discretos (alcance, agarre) sofisticados en primates.
2. ✅ **El debate discreto-vs-rítmico**: Hogan & Sternad 2007 (*Exp Brain Res* 181:13–30, citada y discutida en Balasubramanian et al. 2015) proponen clasificar movimientos por su estructura temporal (puntos de equilibrio estables); propusieron el jerk cuadrático medio como criterio discriminante — que luego los mismos autores reconocieron como medida de suavidad inválida (✅ Balasubramanian et al. 2015, ref. [14] Hogan & Sternad 2009).
3. ✅ **Las métricas de suavidad discretas NO se pueden aplicar a una serie rítmica completa sin segmentar.** Balasubramanian et al. 2015 lo demuestran con un ejemplo simulado: aplicar SPARC o LDLJ a 10 idas-y-vueltas entre dos targets trata la organización temporal de los ciclos (tiempo de movimiento vs dwell-time) como intermitencia → dos expertos con componentes igualmente suaves pero distinto dwell-time reciben suavidades distintas, y duplicar el número de ciclos cambia el valor aunque la calidad de cada ciclo sea idéntica. Solución prescriptiva del paper: **segmentación por eventos** (Eq. 6) + promedio ponderado de las suavidades por componente (Eq. 8), con peso wᵢ ≥ 0.
4. ✅ **Trayectorias curvas**: el propio modelo predice reducción de velocidad en puntos de alta curvatura, pero movimientos con restricciones dinámicas reales (fuerzas, obstáculos, contacto) se desvían del mínimo jerk; además la validez es solo en espacio de la mano, no articular (abstract Flash & Hogan).
5. ❓ **Consecuencia para el Beacon**: el bailarín/artista marcial opera en régimen rítmico continuo. La "suavidad" tipo jerk mínimo mide la calidad de componentes DISCRETOS dentro del flujo. La consonancia por articulación debe computarse **por ciclo/evento segmentado** (usar el beat phase existente del pipeline como segmento natural) o con métricas que toleren periodicidad (PLV, fase relativa), nunca con jerk integral de toda la ventana.

---

## 2. Métricas de suavidad: NJ normalizado, SPARC, LDLJ y la comparación de 2021

Definición de referencia (✅ Balasubramanian et al. 2015): la suavidad es la **continuidad o no-intermitencia** de un movimiento, **independiente de su amplitud y duración**. Intermitencia = dips en el perfil de velocidad (segunda derivada cero con reaceleración) o períodos de arresto (velocidad cero no trivial). Una buena medida debe ser: válida (adimensional, monótona con la intermitencia), sensible, confiable (robusta al ruido de medición) y práctica.

### 2.1 Jerk adimensional (DLJ/NJ) y log-jerk adimensional (LDLJ)

✅ Fórmulas textuales de Balasubramanian et al. 2015 (Eq. 2):

```
DLJ ≜ − (t₂−t₁)⁵ / v_peak²  · ∫_{t₁}^{t₂} (d²v/dt²)² dt
LDLJ ≜ − ln(DLJ)
```

donde v(t) es la rapidez (norma de la velocidad), v_peak = max v(t). Notas:

- El DLJ es el "normalized jerk score" clásico: normalizar el jerk cuadrático integrado por duración⁵ y velocidad-pico² lo vuelve adimensional e invariante a escala de amplitud y duración (variante Teulings; la variante de Balasubramanian "DSJb" usa velocidad media en vez de pico — no son transformaciones lineales entre sí, ✅ Mohamed Refai et al. 2021).
- ⚠️ **Problema de dependencia velocidad/duración**: las versiones SIN normalizar (jerk integrado, jerk absoluto medio, RMS jerk) tienen unidades y dependen de la forma del movimiento; Hogan & Sternad 2009 documentaron su sensibilidad a duración, amplitud y arrestos (citado ✅ en ambos papers JNER). Aun normalizado, el DLJ "lacks sensitivity in the physiological range" — el log (LDLJ) corrige la sensibilidad, ✅ Balasubramanian et al. 2015.
- ✅ **Patología principal: ruido.** "both DLJ and LDLJ are very sensitive to measurement noise and have poor reliability" (Balasubramanian 2015). Cuantificado en Mohamed Refai et al. 2021 (Tabla 2): DSJt/LDSJt/DSJb/LDSJb cruzan el umbral del 10 % de desvío a **SNR ≈ 45 dB** — es decir, basta un ruido ~0,3 % de la amplitud de velocidad para corromper la métrica (la métrica más frágil junto con Peaks). Motivo: la tercera derivada amplifica el ruido de alta frecuencia (~×(1/Δt)³ en diferencias finitas).
- ✅ En la simulación de sub-movimientos, DSJ/LDSJ **NO responden monótonamente** al aumento del retardo entre sub-movimientos (Tabla 3 Part 1: "No" para ambas tareas) → fallan como medidas de intermitencia progresiva.

### 2.2 SPARC (SPectral ARC length)

✅ Definición de Balasubramanian et al. 2015 (Eqs. 4–5). Sea V(ω) el espectro de magnitud de Fourier de v(t), V̂(ω) = V(ω)/V(0) el espectro normalizado por el DC:

```
SPARC ≜ − ∫₀^{ωc} √( 1/ωc² + (dV̂/dω)² ) dω

con corte adaptativo:  ωc ≜ min{ ωc_max ,  min_ω { V̂(r) < V̄ ∀ r > ω } }
```

Parámetros de referencia del paper: V̄ = 0.05, ωc_max = 20π (10 Hz) para el ejemplo rítmico; la versión SAL de 2012 fijaba ωc = 40π (20 Hz). Interpretación geométrica: longitud de arco de la curva del espectro normalizado; un perfil de velocidad suave y acampanado tiene un espectro que decae monótonamente rápido (arco corto → SPARC ≈ −1.4, el máximo observable); los perfiles intermitentes tienen espectro con lóbulos laterales y decaimiento lento (arco largo → SPARC más negativo). Rango típico: [−3.5, 0] aprox., más negativo = menos suave.

Robustez declarada y verificada:

- ✅ **Independiente de escala temporal** (el corte adaptativo ωc resuelve la sensibilidad de SAL al escalado temporal — motivo explícito de la modificación 2012→2015).
- ✅ **Robusta al ruido**: en Part 1 (Tabla 2), SPARC cruza el umbral del 10 % recién a **SNR ≈ 15 dB** (vs 45 dB del LDLJ): tolera ~30× más ruido. Motivo estructural: el corte espectral ωc elimina la banda de alta frecuencia donde vive el ruido blanco; además el espectro normalizado por DC es insensible a amplitud.
- ✅ **Respuesta monótona a perturbaciones armónicas** (temblor simulado: senoides 2–25 Hz, amplitud 0–0.2 m/s sobre perfil base): SPARC baja la suavidad monotónicamente con amplitud y frecuencia (CE = 66.9 % de combinaciones con cambio >10 %, el más sensible junto a SPAL/DSJ).
- ⚠️ **Límites**: (a) es insensible a perturbaciones por encima del corte (~20 Hz) — a 30 fps el Nyquist es 15 Hz, así que fijar ωc_max ≈ 10 Hz cubre casi todo el banda utilizable ❓; (b) en la simulación de sub-movimientos solo es monótona para retardos > 0.2 s (20 % de la duración del sub-movimiento) con pasos de 0.06 s (Tabla 3: "No2,3" — califica condicionalmente); (c) requiere que la ventana contenga al menos un perfil de velocidad con estructura espectral distinguible — ventanas muy cortas (< ~1 s) empobrecen la resolución en frecuencia ❓.

### 2.3 Otras métricas relevantes del catálogo de 2021

✅ Mohamed Refai et al., "Smoothness metrics for reaching performance after stroke. Part 1: which one to choose?", *J NeuroEng Rehabil* 18:154, 2021 (texto completo CC-BY vía EuropePMC, PMC8549250). Revisión sistemática (PRISMA, PROSPERO CRD42020173211): 476 artículos → 102 elegibles → **32 métricas distintas** → 17 excluidas por criterios matemáticos (E1 no adimensional, E2 no reproducible, E3 no basada en tasa de cambio de posición, E4 transformación lineal de otra) → 15 sometidas a 4 simulaciones (Shape: duración 0.5–6 s × distancia 0.2–0.7 m; Harmonic Disturbances; Measurement Noise; Sub-movements 2–4 con lag creciente) sobre dos perfiles base (alcance simétrico de jerk mínimo y asimétrico tipo reach-to-grasp).

Conclusiones (Tabla 3 + Discusión, ✅ textuales):

| Métrica | Indep. forma | Armónicos | Sub-mov. | Ruido |
|---|---|---|---|---|
| NOS (nº sub-mov.) | No | No | No | sin datos |
| SM (speed metric) | Sí¹ | Sí | **No** | Alta |
| MAPR (arrest ratio) | Sí¹ | **No** | **No** | Alta⁴ |
| VAL (velocity arc length) | **No** | **No** | Sí | Alta |
| Peaks (nº de picos) | Sí¹ | Sí | **No** | **Baja** |
| DSJt/DSJb + logs | Sí | Sí | **No** | **Baja** |
| CM (correl. c/ jerk mín.) | Sí¹ | **No** | **No**² | Alta⁴ |
| SPM/SPMR | **No** | Sí/**No** | **No** | Baja |
| SPAL (2012) | **No** | Sí | **No**²,³ | Alta⁴ |
| **SPARC** | **Sí** | **Sí** | **No**²,³ | **Alta** |

(¹ nunca cruzó el umbral del 10 %; ² monótona solo con lag > 0.2 s; ³ con pasos de 0.06 s; ⁴ robusta a todo el ruido probado pero inválida en otro criterio.)

> ✅ Veredicto textual: "Eventually, we found that, for reach-to-point and reach-to-grasp movements, **only Spectral Arc Length (SPARC) was found to be a valid metric**." Y: "We recommend the use of SPARC as a valid metric to measure the smoothness of the upper limb reaching after stroke."

Nota de scope ⚠️: la comparación es para **alcances discretos post-ACV**; la extrapolación a movimiento rítmico de cuerpo completo requiere la segmentación por eventos de Balasubramanian et al. 2015 (§1.4.3) ❓.

---

## 3. Coordinación interarticular: fase relativa, Kelso y el modelo HKB

### 3.1 Fase relativa continua: definición operacional

La variable colectiva (order parameter) de la coordinación es la **fase relativa** φ(t) = φ₁(t) − φ₂(t) entre dos componentes oscilatorios (dos manos, dos piernas, o dos articulaciones). Métodos estándar de extracción (✅ práctica establecida; Lachaux et al. 1999 para señales de banda estrecha, y la literatura de coordinación dinámica):

- **Peak-picking** (método de eventos discretos): marcar picos de aceleración (reversiones del movimiento) en cada serie; φᵢ(tₖ) en el k-ésimo ciclo = instante del evento mapeado a [0, 2π); interpolar linealmente entre eventos → φᵢ(t) continua. Es el método clásico de Kelso para ciclos de movimiento ✅❓ (reconstrucción estándar; los papers de Kelso usan puntos de retorno).
- **Transformada de Hilbert**: φᵢ(t) = arg( xᵢ(t) + i·H[xᵢ](t) ), donde H es la transformada de Hilbert; aplicable si la señal es suficientemente de banda estrecha (filtrada alrededor de la frecuencia de movimiento). Para velocidad de articulación rítmica, filtrar banda 0.5–f_Nyquist y aplicar Hilbert ✅ fórmula estándar, ❓ elección de banda.

### 3.2 Hallazgos de Kelso (1984)

✅ Kelso, "Phase transitions and critical behavior in human bimanual coordination", *Am J Physiol* 246:R1000–R1004, 1984 (PMID 6742155; abstract fetchado vía EuropePMC REST; DOI 10.1152/ajpregu.1984.246.6.r1000 — PubMed directo devolvió CAPTCHA, citado por landing).

Del abstract (✅ citas textuales):

- Al aumentar continuamente la frecuencia de ciclo, el modo **anti-fase asimétrico** (φ ≈ 180°, manos alternadas) **cambia abruptamente** al modo **en-fase simétrico** (φ ≈ 0°, activación simultánea de grupos musculares homólogos).
- "The boundary between the two coordinative states is indexed by a **dimensionless critical number**, which remains constant regardless of whether the hands move freely or are subject to resistive loading" → el parámetro crítico es adimensional e invariante a carga.
- Mecanismo: "Coordinated shifts appear to arise because of **continuous scaling influences that render the existing mode unstable**. Then, at a critical point, **bifurcation** occurs and a new stable (and perhaps energetically more efficient) mode emerges."
- Firma de criticalidad (✅ Schöner, Haken & Kelso 1986, *Biol Cybern* 53:247–257, citada en Bressler & Kelso 2016): cerca de la transición, la **variabilidad de φ (desviación estándar circular) crece** y el **tiempo de relajación tras perturbaciones diverge** (critical fluctuations + critical slowing down), y aparece **histéresis** (la transición ocurre a distinta frecuencia al subir que al bajar).

### 3.3 El modelo HKB (Haken–Kelso–Bunz 1985 + extensiones)

✅ Descripción tomada de la revisión open-access de Bressler & Kelso, "Coordination Dynamics in Cognitive Neuroscience", *Front Neurosci* 10:397, 2016 (PMC5023665, texto completo fetchado), que describe explícitamente el HKB y su extensión.

Modelo original (Haken, Kelso & Bunz 1985): la dinámica de la fase relativa φ se deriva de un potencial V(φ):

```
V(φ) = −a·cos(φ) − b·cos(2φ)
φ̇ = −dV/dφ = −a·sin(φ) − 2b·sin(2φ)
```

con a, b > 0 funciones del **parámetro de control** (frecuencia de movimiento ω): al aumentar ω, b/a decae → los puntos fijos estables en φ = 180° y φ = 0° (que coexisten a baja frecuencia: **multiestabilidad**) se fusionan por **bifurcación saddle-node** y solo sobrevive φ = 0° a alta frecuencia (✅ Bressler & Kelso 2016, leyenda de Fig. 1: "two stable fixed points near Φ = 0° and Φ = 180°... For intermediate values of k, one stable fixed point disappears in a saddle-node bifurcation... Metastable, intermittent dynamics is observed for low values of k: although there are no longer any fixed points, there is still attraction to the remnants of the previously stable states").

Extensiones (✅ mismo source):

- **Ruido** (Schöner et al. 1986): φ̇ = −a·sin φ − 2b·sin 2φ + ζ(t), ζ ruido estocástico → explica las fluctuaciones críticas y la distribución de φ.
- **Simetría rota / detuning** (Kelso et al. 1990): los osciladores tienen frecuencias intrínsecas distintas δω = ω₁ − ω₂ ≠ 0:

```
φ̇ = δω − a·sin(φ) − 2b·sin(2φ) + ζ(t)
```

Esto produce **coordinación relativa** (von Holst 1939): los componentes tienden a coordinarse sin quedar nunca totalmente trabados en una fase fija — "relative coordination should be seen as a tendency for cortical areas [o miembros] to become coordinated without them becoming fully coordinated in a fixed phase relation" (✅ textual). Con δω grande o acople débil, φ deriva con "residuos" de atracción cerca de los antiguos atractores (**dinámica metaestable, intermitente**).

### 3.4 Correlación cruzada vs fase relativa: tradeoffs

- ✅ La **coherencia espectral / correlación** mide consistencia de fase EN UNA FRECUENCIA pero mezcla amplitud y forma de onda; la fase relativa aisla la relación temporal y es la variable con significado dinámico (atractores, bifurcaciones, metaestabilidad). Lachaux et al. 1999 motivan su PLS exactamente así: "Unlike the more traditional method of spectral coherence, PLS **separates the phase and amplitude components**" (✅ abstract fetchado).
- ✅ En registros corticales, la coherencia interareal muestra transiciones rápidas entre valores altos y bajos "reflecting **partial** synchronization of cortical sites, without locking in global synchronization" (Bressler & Kelso 2016) — la coordinación real es relativa, no lock total.
- ⚠️ La **correlación cruzada con lag** (max sobre retardos) es robusta a ruido pero: (a) no distingue acople de fase de covariación de amplitudes; (b) el lag óptimo cambia con la frecuencia; (c) en señales no estacionarias (baile con cambios de tempo) un solo número por ventana oculta las transiciones. ❓ Recomendación: fase relativa ventaneada (o PLV deslizante) como primaria, correlación como diagnóstico secundario.

### 3.5 LA CONEXIÓN MUSICAL: coordinar = phase-locking = consonancia

✅❓ La consonancia armónica entre dos parciales de frecuencias f₁, f₂ con relación entera simple es, dinámicamente, **bloqueo de frecuencia con fase estable**: Δφ(t) = 2π(f₁−f₂)t + const se mantiene acotado; cuando la relación no es racional-simple, Δφ deriva y el oído percibe batidos/rugosidad (ver reporte 04 del proyecto). El aparato matemático es idéntico al de la coordinación motora:

| Consonancia armónica | Coordinación motora |
|---|---|
| dos osciladores, fases θ₁, θ₂ | dos miembros/articulaciones, fases φ₁, φ₂ |
| detuning Δω = ω₁ − ω₂ | diferencia de frecuencias intrínsecas δω (simetría rota) |
| acoplamiento (interacción no lineal) | acoplamiento neuromecánico a, b (HKB) o K (Kuramoto) |
| lock: Δφ estable → sonido fusionado/afinado | lock: φ estable → patrón coordinado (0°/180°) |
| fuera de la lengua de Arnold → batidos/rugosidad | fuera del régimen de acople → deriva, intermitencia |

Esto legitima la metáfora fundacional del Beacon: **una articulación "consonante" es una cuya fase (contra el beat global o contra su par anatómico) está establemente lockeada; una "disonante" deriva o fluctúa** — y el detuning del armónico puede pilotearse con la estabilidad de fase medida. ✅ La misma identidad estructural aparece en la música conjunta: el balanceo corporal de cuartetistas se analiza como sistema de osciladores acoplados con flujo de información direccional (Granger causality), y el grado global de acople predice la calidad percibida (Chang et al. 2017, ver §4.4).

---

## 4. Teoría de sincronización transferible

### 4.1 Modelo de Kuramoto

✅ (Wikipedia: Kuramoto model, fetchado — ecuaciones verificadas; el modelo original es Kuramoto 1975, *Chemical Oscillations, Waves and Turbulence*, Springer.)

N osciladores de fase θᵢ con frecuencias naturales ωᵢ ~ g(ω), acoplamiento global sinusoidal:

```
dθᵢ/dt = ωᵢ + (K/N)·Σⱼ sin(θⱼ − θᵢ)         i = 1…N
```

- **Parámetro de orden**: r·e^(iψ) = (1/N)·Σⱼ e^(iθⱼ); r ∈ [0,1] mide coherencia de fase poblacional, ψ la fase media. El sistema se reescribe desacoplado: dθᵢ/dt = ωᵢ + K·r·sin(ψ − θᵢ).
- **Transición**: para g unimodal simétrica existe Kc = 2/(π·g(0)); con K < Kc, r → 0 (incoherencia); con K > Kc emerge sincronización parcial: se lockean los osciladores con |ω| < K·r (los demás derivan).
- **Caso N=2** (relevante para pares de articulaciones): en marco rotante ω₁ = −ω₂; si K < Kc = 2|ω₁| el ángulo Δθ gira (el rápido "laps" al lento); si K > Kc cae a un atractor estable → **phase lock**. Es exactamente la condición de la lengua de Arnold.
- Supuestos: acople débil, osciladores casi idénticos, interacción sinusoidal en la diferencia de fase ✅.

### 4.2 Valor de bloqueo de fase (PLV)

✅ Lachaux, Rodriguez, Martinerie & Varela, "Measuring phase synchrony in brain signals", *Hum Brain Mapp* 8:194–208, 1999 (PMID 10619414, abstract fetchado vía EuropePMC; PMC6873296; full-text XML devolvió error 500 del servidor — fórmulas reconstruidas, estándar en la literatura).

Método PLS (phase-locking statistics): dado Δφ(t) = φ₁(t) − φ₂(t) muestreado en N instantes de una ventana/ensayo:

```
PLV = | (1/N) · Σₙ e^(i·Δφₙ) |   ∈ [0, 1]
```

PLV = 1 ⇔ fase relativa perfectamente estable; PLV ≈ 0 ⇔ Δφ uniformemente distribuida. Significancia contra datos surrogate (barajado de fases) sin supuestos a priori ✅. Propiedades clave para el Beacon: **insensible a amplitud** (solo usa fase), resolución temporal <100 ms demostrada en señales gamma (45 Hz) ✅ — y por construcción es el r de Kuramoto para el par (o contra una referencia: θ_beat).

### 4.3 Lenguas de Arnold

✅ (estructura matemática estándar; fuentes fetchadas: Wikipedia Kuramoto §N=2/circle map; Herzel et al. 2026, "Theoretical chronobiology of circadian timing", *npj Biol Timing Sleep* 3:32, PMC13385350, revisión OA que usa explícitamente lenguas de Arnold para explicar entrainment de osciladores biológicos; preprint Biber et al. 2026 sobre respuestas sub-armónicas en DBS con estructura de lengua de Arnold e histéresis 📊.)

Para un oscilador forzado a frecuencia Ω con frecuencia natural ω y fuerza de acople K (circle map / phase-locked loop, ✅ Wikipedia): el lock n:m ocurre en una región del plano (desafinación × acople) con forma de lengua. Propiedades transferibles:

- **El ancho de la lengua crece con K** (a mayor acople, mayor rango de desafinación |ω − Ω| tolerado manteniendo lock). Para N=2 Kuramoto: lockeado sii K > 2|ω₁|.
- **Dentro de la lengua**: Δφ converge a un valor estable (con ruido: distribución concentrada, PLV alto). **Fuera**: deslizamiento de fase a tasa ≈ √(Δω² − K²) — "laps" periódicos que se ven como batidos.
- **Histéresis y sub-armónicos**: las lenguas de orden alto (2:1, 3:2) aparecen a acoples mayores; el lock puede persistir al bajar K más allá del umbral de subida (✅ preprint DBS 2026 📊).

**Analogía directa con el Beacon** ❓: si la "consonancia de movimiento" se conceptualiza como fuerza de acople entre el oscilador-articulación y el beat global (o entre pares), entonces **una articulación bien entrenada/coordinada tiene un K efectivo alto → tolera desvíos de tempo (Δω) sin perder el lock → puede sonar "afinada" en una banda más ancha**. Inversamente, el detuning del armónico (±50 % del gap al vecino) puede mapearse desde la distancia normalizada a la frontera de la lengua: d = 1 en el centro del lock, d → −1 cuando Δφ desliza (PLV colapsa). Esto da un puente cuantitativo exacto entre la métrica motora y el parámetro de síntesis.

### 4.4 Balanceo corporal en ensambles: evidencia empírica musical

✅ Chang, Livingstone, Bosnyak & Trainor, "Body sway reflects leadership in joint music performance", *PNAS* 114(21):E4134–E4141, 2017 (PMID 28484007, PMC5448222; abstract fetchado vía EuropePMC REST; el HTML de PMC pidió cookies — citado por abstract + landing doi.org/10.1073/pnas.1617657114).

- Motion capture del **body sway** de los 4 integrantes de cuartetos de cuerdas durante ejecución real; **Granger causality** entre las series temporales de movimiento → magnitud y dirección del flujo de información.
- Resultados (✅ textuales del abstract): los **líderes asignados ejercieron influencia significativamente mayor** sobre los demás y fueron menos influidos que los seguidores; el efecto persiste sin contacto visual y se **potencia con información visual** → la coordinación musical usa señales visuales además de auditivas.
- **Clave para el Beacon**: "performers' ratings of the 'goodness' of their performances were **positively correlated with the overall degree of body sway coupling**" → el acople de movimiento entre cuerpos predice la calidad percibida de la performance. La sincronía corporal no es epifenómeno: es el canal de la acción conjunta y su fuerza es un juicio estético.
- 📊 Complemento (citado en Orlandi & Candidi 2025): Vicary et al. 2017 (*PLoS One*, "Joint action aesthetics"): la sincronía de movimiento entre bailarines predice el engagement de la audiencia con la performance en vivo; Bigand et al. 2024 (*Curr Biol*): "The geometry of interpersonal synchrony in human dance".

---

## 5. Percepción: fluidez, expectativa y estética del movimiento

### 5.1 Teoría de fluidez de procesamiento

✅ Reber, Schwarz & Winkielman, "Processing fluency and aesthetic pleasure: Is beauty in the perceiver's processing experience?", *Pers Soc Psychol Rev* 8(4):364–382, 2004 (PMID 15582859, DOI 10.1207/s15327957pspr0804_3; registro EuropePMC fetchado). Tesis: **los estímulos procesados con mayor fluidez (facilidad) se experimentan como más placenteros**; la fluidez es una señal meta-cognitiva que se atribuye al estímulo.

Matices empíricos posteriores (✅ ambos fetchados vía EuropePMC):

- Forster, Leder & Ansorge 2013 (*Emotion* 13:280–289, PMID 23088777): la fluidez **subjetivamente sentida** (no la objetiva) determina el liking; priming subliminal y duración de presentación modulan ambas.
- Goller et al. 2015 (*PLoS One*, PMC4545584): el sentimiento de fluidez no depende del marco de referencia, pero **el liking solo cambia cuando la fluidez varía DENTRO del participante** (comparación relativa) → los juicios estéticos por fluidez son comparativos, no absolutos. ⚠️ Importante para el Beacon: la desafinación se percibirá relativa al contexto de la pieza/sesión, no en absoluto ❓.

### 5.2 Predicción y expectativa en la observación de movimiento

✅ Orlandi & Candidi, "Toward a neuroaesthetics of interactions: insights from dance...", *iScience* 28(5):112365, 2025 (PMC12051600, texto completo fetchado). Puntos relevantes:

- **Marco de codificación predictiva** para la comprensión de acciones: comparar kinemática predicha vs percibida genera errores de predicción que actualizan el modelo; "this framework is also relevant for aesthetic evaluation of movements, **which often hinges on surprise and expectation violations**" (✅ textual). La actividad del AON (action observation network) varía con familiaridad/novedad del movimiento observado y la excitabilidad somatotópica motora aumenta ante movimientos inesperados o erróneos ✅.
- **Point-light / movimiento biológico** (Johansson 1973, clásico): el pSTS es sensible a animaciones point-light (figuras humanas de puntos luminosos vs scrambled) ✅ (la revisión lo cita como evidencia consolidada de percepción de movimiento biológico sin información de forma). El STS codifica señales sociales y emocionales del movimiento corporal dinámico ✅. — Cita de Johansson vía revisión (✅ secundaria peer-reviewed; el paper de 1973, *Biol Psychol* 1:201–211, no se fetchó directamente).
- **Fluidez y expertise**: "movements that are practiced, and thus more familiar and feasible for the observer, are generally preferred over unfamiliar ones — likely due to increased processing fluency. **Interestingly, the effect appears to reverse for more complex and** [skilled movements]" (✅ textual de la revisión, que cita la literatura de esfuerzo). Es decir: la fluidez predice el liking en acciones cotidianas, pero en arte/virtuosismo la relación se invierte parcial o totalmente ⚠️.

### 5.3 Estética de la danza: resultados empíricos con kinemática

✅ Orlandi, Cross & Orgs, "Timing is everything: Dance aesthetics depend on the complexity of movement kinematics", *Cognition* 205:104446, 2020 (OA CC-BY, texto completo fetchado desde eprints.gla.ac.uk/227924).

- Diseño: 12 extractos de la coreografía *Duo* de William Forsythe ejecutados por un bailarín profesional en dos versiones: **uniform** (velocidad constante) y **varied** (acentuando cambios dinámicos de velocidad — misma trayectoria, distinto timing). 41 participantes naive califican velocidad, esfuerzo, reproducibilidad y disfrute; motion capture offline; **entropía de Shannon (estimador Chao-Shen) de los perfiles de aceleración por miembro** como medida de complejidad/predictibilidad (mayor entropía = menor predictabilidad).
- **Resultado principal (✅ textual del abstract)**: "faster, **more predictable** movement sequences with **varied velocity profiles** are judged to be more effortful, less reproducible, and **more aesthetically pleasing** than slower sequences with more uniform velocity profiles."
- Interpretación de los autores: consistente con **teoría de la información** (Berlyne; complejidad intermedia preferida) y la **heurística del esfuerzo**: el "efecto Cirque du Soleil" (Cross et al. 2011: correlación negativa entre disfrute y capacidad de reproducir el movimiento — lo difícil de ejecutar gusta más) ✅.
- 📊 Torrents et al. 2013 (*Perception* 42:447–458, citado en el paper): no-expertos son atraídos por alta velocidad de giro, gran amplitud de movimiento y balances sostenidos — parámetros cinemáticos objetivos predicen belleza en danza contemporánea.
- ⚠️ Christensen et al. 2016/2019 (citados ✅ en Orlandi 2020): la expresividad del movimiento NO se reduce a la cantidad total de movimiento (videos forward/backward idénticos en velocidad y aceleración globales se discriminan emocionalmente solo en dirección forward).

### 5.4 La nota honesta: "¿suave = bello?" está discutido ⚠️

- **A favor de la suavidad**: fluidez de procesamiento → placer (Reber et al. 2004 ✅); la suavidad es marca de pericia y salud motoras (✅ Balasubramanian 2015); el movimiento patológico (ACV, Parkinson) es intermitente y se percibe como tal ❓inferencia.
- **En contra de la ecuación simple**: (1) la danza virtuosa incluye movimientos **explosivos, no suaves** (aceleraciones altas, pausas, cambios bruscos) y justamente la versión "varied" — más compleja, menos suave en el sentido de jerk mínimo — fue la MÁS gustada (Orlandi et al. 2020 ✅); (2) la sorpresa controlada y la violación de expectativa son motores del placer estético (Orlandi & Candidi 2025 ✅; Van de Cruys & Wagemans 2011, cuenta de error de predicción en arte, citada ahí ✅); (3) el efecto de la fluidez se invierte para movimientos complejos/expertos (✅ revisión iScience); (4) el liking por fluidez es relativo al contexto de comparación (Goller et al. 2015 ✅).
- ❓ **Síntesis para el diseño del Beacon**: la "consonancia" no debe ser suavidad cruda. Debe ser **suavidad DENTRO del componente de movimiento** (cada gesto bien ejecutado, sin intermitencia patológica) **combinada con acople rítmico estable y riqueza temporal entre componentes** (variedad predecible). Un movimiento perfectamente suave pero metronómicamente uniforme sería "consonante" en el eje 1 y pobre en el eje 2; la virtuosidad explosiva bien coordinada puntúa alto en ambos. La arquitectura propuesta en §6 separa estos ejes en métricas distintas.

---

## 6. SÍNTESIS: métricas candidatas de consonancia por articulación

**Setup**: stream 30 fps de keypoints 2D COCO-17 (x, y, confianza) por persona vía OSC; el pipeline ya produce `tempo_bpm` y `beat_phase`. Objetivo: por articulación j, un dato d_j ∈ [−1, 1] que pilote el detuning de su armónico de la serie de 40 Hz (0 = afinado; ±1 = ±50 % del gap al armónico vecino, es decir medio tono "armónico" en cada dirección, según el diseño del proyecto — ver reporte 04).

### 6.1 Patología transversal: ruido de cámara y derivadas (cuantificación)

✅/❓ Derivación propia verificada aritméticamente (❓): a 30 fps, Δt = 1/30 s ≈ 0.0333 s. Para ruido blanco de posición de amplitud ε = 1 px por coordenada:

- **Diferencias finitas crudas**: la amplificación es ≈ 1/Δt ≈ ×30 por orden de derivada:
  - velocidad (diferencia simple): ruido ≈ ε/Δt ≈ **30 px/s**
  - aceleración (diferencia central 2º orden): ruido ≈ 2–2.5·ε/Δt² ≈ **900–2250 px/s²**
  - jerk (diferencia 3er orden): ruido ≈ 4·ε/Δt³ ≈ **27 000–108 000 px/s³**
- **Con ventana de suavizado de ~1 s** (estimación suavizada tipo Savitzky-Golay/promedio, la referencia del equipo del Beacon): 1 px → ≈ **0.9 px/s → ≈ 27 px/s² → ≈ 810 px/s³** (cada orden multiplica ×30; cifras del brief del proyecto, consistentes con Δt_efectiva ≈ 1.1 s ❓).
- Consecuencias: (a) el **jerk crudo está dominado por ruido** a menos que la señal real tenga jerk ≥ 10³–10⁴ px/s³ (movimientos rápidos de mano a ~1 m/s en 0.3 s con escala ~1 px/cm sí llegan: jerk real ~ 10³–10⁴ px/s³ ❓ orden de magnitud); (b) LDLJ/DLJ fallan a SNR 45 dB ✅ (Tabla 2 Part 1) — con ε=1 px y velocidad pico típica de 100–300 px/s el SNR es ~40–50 dB → **zona de fallo del LDLJ**; SPARC aguanta hasta SNR ≈ 15 dB ✅; (c) el espectro de ruido blanco de posición es plano hasta Nyquist (15 Hz a 30 fps): el corte adaptativo de SPARC (V̄ = 0.05) lo poda automáticamente ✅ — fijar ωc_max ≤ 2π·12 Hz para dejar margen ❓; (d) **nunca derivar la posición cruda**: filtrar primero (Butterworth zero-phase de 4º orden, corte ~10 Hz — el mismo que usó Part 1 como condición "filtered noise" ✅) o usar suavizado spline.
- **Oclusión/imputación** ❓: keypoints con confianza baja interpolados producen tramos artificialmente suaves (sesgo pro-consonancia) o saltos al reaparecer (spikes de jerk). Mitigar: ponderar cada métrica por la confianza media de la ventana; descartar ventanas con >20 % de frames imputados; tratar reapariciones como ruptura de serie (reiniciar ventanas).
- **Confusores de velocidad** ✅: SM y métricas de velocidad pura dependen de distancia/duración (Part 1); SPARC es invariante a escala temporal ✅ pero ventaneada: si la ventana mezcla fases rápidas y dwell, el espectro refleja la mezcla. Segmentar por beat (el pipeline ya lo tiene) ❓.
- **Proyección 2D** ❓: la profundidad perdida comprime velocidades cuando el movimiento es hacia/desde la cámara (v_2d = v_3d·sin(ángulo)); una articulación puede parecer "congelada" o "errática" por rotación corporal. Mitigaciones parciales: normalizar por la escala del torso (distancia hombro-cadera en px) para invariancia de distancia a cámara; reportar confianza baja cuando el torso cambia mucho de tamaño en la ventana; las métricas de fase (PLV, fase relativa) son más robustas que las de amplitud porque solo usan timing ❓.

### 6.2 Candidata (i): SPARC ventaneado de la rapidez por articulación

- **Qué captura** ✅: intermitencia/continuidad del gesto — el eje "ejecución limpia" de la suavidad; única métrica validada sistemáticamente (Part 1).
- **Fórmula** (✅ §2.2): por ventana W (1–2 ciclos de beat), v_j(t) = ‖(ẋ_j, ẏ_j)‖ con posiciones filtradas; SPARC_j(W) = −∫₀^{ωc} √(1/ωc² + (dV̂/dω)²) dω con V̂ = V(ω)/V(0), ωc adaptativo (V̄ = 0.05, ωc_max = 2π·10 Hz a 30 fps ❓ ajuste por Nyquist).
- **Ventaneo** ✅: NO aplicar a la serie rítmica completa sin segmentar (§1.4.3): usar la fase de beat existente para alinear ventanas, o segmentar por eventos (mínimos de velocidad = reversiones), y promediar ponderado por duración (Eq. 8 de Balasubramanian 2015: Λ = Σwᵢλᵢ/Σwᵢ, wᵢ = duración del componente).
- **Normalización a d**: SPARC ∈ [≈−3.5, ≈−1.4] para perfiles fisiológicos (rango empírico de las tablas ✅: base −1.4, perturbado hasta −3.1). Mapeo lineal ❓: d_i = clip(2·(SPARC_j − SPARC_min)/(SPARC_max − SPARC_min) − 1, −1, 1) con SPARC_max ≈ −1.4 (muy suave → d→+1, afinado), SPARC_min ≈ −3.0. Alternativa robusta: z-score contra la línea base del propio performer en la sesión (percentiles), dado que el liking por fluidez es comparativo (✅ Goller et al. 2015).
- **Patologías** ✅/❓: ruido (mitigado: robustez 15 dB + filtro previo); ventanas con dwell/pausas → SPARC castiga la pausa como intermitencia aunque sea expresiva (la pausa coreográfica NO es disonancia ❓) — detectar arrestos y excluir o tratar la pausa como evento; ωc_max por debajo de componentes rápidas legítimas (golpes percusivos de artes marciales tienen energía >10 Hz ❓) — para esos gestos el SPARC subestima la calidad; movimiento lento con amplitud baja → espectro pobre, V̂ ruidoso → SPARC inestable (umbral de velocidad mínima ❓).

### 6.3 Candidata (ii): PLV de la articulación contra el ritmo global (beat)

- **Qué captura** ✅: acople rítmico — el eje central de la metáfora de consonancia (§3.5): la articulación como oscilador lockeado al "driver" del tempo. Es el análogo directo del lock de Kuramoto/Lachaux.
- **Fórmula** (✅ Lachaux et al. 1999, estándar): fase de la articulación por peak-picking de ciclos (máximos de velocidad o reversiones de posición filtrada) o Hilbert de v_j(t) banda-angosta; φ_beat(t) = 2π·beat_phase del pipeline (ya existe). Δφₙ = φ_j(tₙ) − φ_beat(tₙ) sobre N muestras de la ventana:
  ```
  PLV_j = | (1/N) · Σₙ e^(i·Δφₙ) |
  ```
  Opción más estricta (entrainment n:m) ❓: Δφₙ = m·φ_j − n·φ_beat para relaciones rítmicas (2:1 en pasos de danza).
- **Normalización a d**: PLV ∈ [0,1]; d_ii = 2·PLV_j − 1 (PLV ≥ 0.8 → afinado; PLV ≈ 0 → d = −1, detuning máximo) ❓. Mejor: restar el PLV esperado por azar para N finito (E[PLV_null] ≈ √(π/(4N)) + … o surrogate por barajado de fases ✅ práctica de Lachaux) y reescalar.
- **Patologías** ❓: (a) articulación quieta (tronco en pose sostenida) no tiene fase significativa → gatear por amplitud de movimiento (si ‖v_j‖ < umbral, congelar d anterior o reportar NaN→0); (b) rubato/tempo no estacionario: el beat_phase del pipeline debe ser la referencia en el mismo marco temporal; (c) sesgo de armónicos: si la articulación se mueve al doble del tempo (8th notes), PLV contra el beat fundamental baja aunque el movimiento esté perfectamente entrained → probar también contra 2×beat y tomar el máximo (invariancia de octava, coherente con la serie armónica del diseño sonoro ❓); (d) N pequeño (2–4 beats por ventana) → PLV ruidoso; usar ventanas deslizantes de ≥4 ciclos con paso de 1 ciclo.

### 6.4 Candidata (iii): estabilidad de fase relativa en pares de miembros

- **Qué captura** ✅: coordinación interarticular — el order parameter de HKB/Kelso (§3): atractores 0°/180°, fluctuaciones críticas, metaestabilidad. Pares naturales en COCO-17: muñecas (L/R), tobillos, hombros, caderas, y pares ipsilaterales muñeca-tobillo (coordinación cruzada de caminata/danza).
- **Fórmula** (✅ estándar de coordinación dinámica): φ_j y φ_k por Hilbert/peak-picking (§3.1); φ_rel(t) = φ_j(t) − φ_k(t); concentración circular de la ventana:
  ```
  R_jk = | (1/N)·Σₙ e^(i·φ_rel(tₙ)) |        (PLV entre las dos articulaciones)
  S_jk = √( −2·ln R_jk )                      (desviación estándar circular, rad)
  ```
  Opcional: ψ_jk = arg del vector medio → dónde está el atractor (≈0° en-fase, ≈180° anti-fase).
- **Normalización a d**: d_iii = 2·R_jk − 1 ❓, o con penalización de deriva: si R alto pero ψ lejos de 0/180 (patrón inusual/inestable) ❓ mantener R como principal (la estabilidad es la consonancia; el valor del atractor es estilo, no afinación — decisión de diseño del Beacon ❓).
- **Patologías** ✅/❓: (a) cerca de una transición de fase legítima (cambio de paso coreográfico) S diverge (critical fluctuations ✅ Kelso/Schöner) → la "disonancia" transitoria puede ser musicalmente deseable; suavizar d con constante de tiempo larga o detectar bifurcaciones (cambio de ψ ≈ 180°) y excluir la ventana de transición; (b) la metaestabilidad es funcional ("relative coordination... prevents the cortex from becoming locked in stable coordination states" ✅ Bressler & Kelso 2016) — R ≈ 0.5–0.7 con ψ estable puede ser coordinación experta flexible, no fallo ❓; (c) frecuencias distintas entre miembros (δω ≠ 0, simetría rota ✅): si no comparten frecuencia, R cae aunque el patrón sea coherente — verificar lock de frecuencia (razón de frecuencias ≈ n:m) antes de computar R, o computar R en el marco n:m; (d) 2D: la proyección puede convertir anti-fase real en apariencia en-fase cuando el movimiento es sagital y la cámara es frontal ❓.

### 6.5 Candidata (iv): continuidad de la transferencia de energía (cadena cinemática)

- **Qué captura** ✅: eficiencia coordinativa del movimiento balístico/explosivo — la secuencia proximal→distal de la literatura de cadena cinética: "In the dominant tasks of the upper extremity, the energy generation and production are in a proximal-to-distal sequenced pattern"; en la patada: absorción por la pierna de apoyo, arco de tensión excéntrico torso-cadera y liberación concéntrica, con secuenciación proximal→distal en el downswing; una transferencia eficiente pasa energía de segmentos grandes proximales a terminales pequeños, maximizando la velocidad distal (✅ Almansoof, Nuhmani & Muaidi, "Role of kinetic chain in sports performance and injury risk", *J Med Life* 16(11):1591–1596, 2023, PMC10893580, texto fetchado; 📊 complementa: Sakamoto et al./jeb227207 "Time-varying motor control strategy for proximal-to-distal sequential movements" — la secuencia P-D reduce el trabajo muscular usando las articulaciones proximales como fuente de energía, snippet de búsqueda no fetchado completo).
- **Fórmula** (proxy 2D, ❓ construcción del agente): para una cadena (p. ej. cadera→rodilla→tobillo, u hombro→codo→muñeca), definir la envolvente de "energía cinética proxy" por segmento: e_i(t) = ‖v_i(t)‖² (sin masas reales; la masa segmentaria se puede aproximar con constantes antropométricas ❓). Medir (a) **orden de secuencia**: t_peak(e_prox) < t_peak(e_med) < t_peak(e_dist) → indicador binario/gradual de orden correcto; (b) **continuidad del traspaso**: correlación cruzada con lag entre e_i(t) y e_{i+1}(t) — un traspaso fluido da picos sucesivos solapados con lag positivo estable (τ* ≈ constante entre repeticiones); (c) **suavidad de la envolvente total** E(t) = Σe_i(t): SPARC o coeficiente de variación de E — los "fugas" de energía (articulaciones que frenan sin transferir) producen dips.
  ```
  d_iv = w₁·orden_correcto + w₂·R_xcorr(lag estable) + w₃·suavidad(E)   (combinación convexa, ❓)
  ```
- **Normalización a d**: cada término en [0,1] → d ∈ [0,1] → reescalar a [−1,1]; o z-score contra la línea base del performer ❓.
- **Patologías** ❓: (a) 2D sin profundidad: la secuencia P-D de un golpe hacia la cámara se comprime (todas las velocidades proyectadas caen a la vez); (b) proxy ‖v‖² sin masas distorsiona la energía real (el tronco pesa ~50 % del cuerpo); (c) solo es aplicable a gestos balísticos (lanzamientos, patadas, golpes) — en danza lenta/adagio la "cadena cinética" no es el principio organizador; gatear por régimen detectado (velocidad distal alta + duración corta); (d) el orden proximal→distal tiene excepciones documentadas según tarea (estrategias time-varying 📊 jeb227207) — no penalizar fuerte el orden "incorrecto", solo la inconsistencia entre repeticiones.

### 6.6 Candidata (v): error de predicción de un modelo de movimiento por articulación (consonancia = baja sorpresa)

- **Qué captura** ✅: predictibilidad/expectativa — el eje de la codificación predictiva aplicada a estética del movimiento ("comparing predicted and perceived movement kinematics results in prediction errors... also relevant for aesthetic evaluation of movements, which often hinges on surprise and expectation violations" ✅ Orlandi & Candidi 2025) y de la entropía cinemática como complejidad (✅ Orlandi et al. 2020 usaron entropía de Shannon Chao-Shen de los perfiles de aceleración).
- **Fórmula** (❓ construcción del agente sobre base ✅): modelo simple por articulación en la ventana: regresión armónica a la frecuencia de beat y sus primeros armónicos (ajusta movimiento rítmico con pocos parámetros):
  ```
  x̂_j(t) = μ + Σ_{h=1..H} [ a_h·cos(2π·h·f_beat·t) + b_h·sin(2π·h·f_beat·t) ]
  PE_j = RMS( x_j − x̂_j ) / RMS( x_j − μ )      ∈ [0, 1] (fracción de varianza no explicada)
  ```
  Alternativa sin beat: modelo AR(p) ajustado en línea; PE = varianza del residuo normalizada. Variante entrópica ✅ (Orlandi 2020): discretizar aceleración y computar entropía de Shannon con estimador Chao-Shen; mayor entropía = menor predictabilidad.
- **Normalización a d — la U invertida**: ⚠️ NO mapear monotónicamente: PE ≈ 0 total = movimiento metronómico (aburrido; la preferencia es por complejidad intermedia ✅ Berlyne vía Orlandi 2020; y lo "varied pero predecible" fue lo preferido ✅). Proponer ❓: d_v = 1 − |PE_j − PE*|/PE_max con PE* ≈ 0.2–0.3 (óptimo estético calibrable empíricamente), o combinar: consonancia alta si el residuo del modelo armónico es bajo PERO la entropía de la envolvente de amplitud es media-alta (estructura predecible con dinámica rica — exactamente el hallazgo de Orlandi 2020: varied + predictable).
- **Patologías** ❓: (a) el modelo armónico asume tempo constante — con rubato, PE sube espuriamente (usar fase de beat deformada del pipeline en vez de f_beat constante); (b) cambios coreográficos legítimos disparan PE (novedad ≠ disonancia — la sorpresa puede ser el punto estético ✅) — ventana larga promedia y amortigua; (c) sobreajuste con H grande → PE artificialmente bajo; regularizar (H ≤ 3–4, o validación cruzada); (d) articulaciones con movimiento irregular pero funcional (manos en gestos semánticos) tendrán PE alto crónico → normalizar por articulación contra la línea base del performer.

### 6.7 Composición final sugerida ❓

d_j total = combinación ponderada de los ejes (pesos calibrables en el instrumento):

```
d_j = clip( w_i·d_i + w_ii·d_ii + w_iii·d_iii + w_iv·d_iv + w_v·d_v , −1, 1 )
```

con pesos mayores en (ii) y (iii) para material rítmico/ensemble (el acople ES la consonancia, §3.5), (i) para calidad de gesto, (iv) solo en gestos balísticos gateados, (v) como modulador de riqueza. El signo de d_j puede asignarse por el sentido del desvío (p. ej. fase adelantada → detuning hacia arriba del armónico, fase atrasada → hacia abajo), lo que da una geometría de desafinación que refleja la dirección del error temporal, no solo su magnitud ❓. Histeresis/suavizado temporal (EMA con τ ≈ 0.5–1 s) para evitar parpadeo del detuning, y cuantización opcional a escala (snap) según el reporte 04 del proyecto.

---

## Sources

- ✅ Flash, T. & Hogan, N. (1985). The coordination of arm movements: an experimentally confirmed mathematical model. *J Neurosci* 5(7):1688–1703. https://www.jneurosci.org/content/5/7/1688 (abstract fetchado; DOI 10.1523/JNEUROSCI.05-07-01688.1985)
- ✅ Balasubramanian, S., Melendez-Calderon, A., Roby-Brami, A. & Burdet, E. (2015). On the analysis of movement smoothness. *J NeuroEng Rehabil* 12:112. Texto completo CC-BY fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4674971/fullTextXML (PMC4674971; DOI 10.1186/s12984-015-0090-9). **Nota: la URL semilla jner.biomedcentral.com/articles/10.1186/s12984-015-0076-1 devolvió "Application Unavailable" (Springer) y el DOI correcto del paper SPARC de 2015 es s12984-015-0090-9, no 0076-1.**
- ✅ Mohamed Refai, M.I., Saes, M., Scheltinga, B.L., et al. (2021). Smoothness metrics for reaching performance after stroke. Part 1: which one to choose? *J NeuroEng Rehabil* 18:154. Texto completo CC-BY fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8549250/fullTextXML (PMC8549250). **Nota: el DOI real es 10.1186/s12984-021-00949-6 (la semilla decía s12984-021-00927-w, que devolvió "Application Unavailable"); tablas 1–3 extraídas del texto.**
- ✅ Kelso, J.A.S. (1984). Phase transitions and critical behavior in human bimanual coordination. *Am J Physiol* 246:R1000–R1004. Abstract fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:6742155 (PMID 6742155; DOI 10.1152/ajpregu.1984.246.6.r1000 — pubmed.ncbi.nlm.nih.gov directo devolvió CAPTCHA).
- ✅ Bressler, S.L. & Kelso, J.A.S. (2016). Coordination Dynamics in Cognitive Neuroscience. *Front Neurosci* 10:397. Texto completo fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5023665/fullTextXML (PMC5023665) — descripción del modelo HKB, extensión con ruido y detuning, metaestabilidad.
- ✅ Schaal, S., Sternad, D., Osu, R. & Kawato, M. (2004). Rhythmic arm movement is not discrete. *Nat Neurosci* 7:1136–1143. Abstract fetchado vía EuropePMC REST (PMID 15452580; DOI 10.1038/nn1322).
- ✅ Lachaux, J.P., Rodriguez, E., Martinerie, J. & Varela, F.J. (1999). Measuring phase synchrony in brain signals. *Hum Brain Mapp* 8:194–208. Abstract fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:10619414 (PMID 10619414, PMC6873296; el fullTextXML devolvió error 500 del servidor — fórmula PLV reconstruida, estándar).
- ✅ Kuramoto model — Wikipedia, fetchado: https://en.wikipedia.org/wiki/Kuramoto_model (ecuaciones, parámetro de orden, Kc, caso N=2, circle map/PLL).
- ✅ Chang, A., Livingstone, S.R., Bosnyak, D.J. & Trainor, L.J. (2017). Body sway reflects leadership in joint music performance. *PNAS* 114(21):E4134–E4141. Abstract fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=PMCID:PMC5448222 (PMID 28484007; DOI 10.1073/pnas.1617657114; el HTML de PMC pidió cookies).
- ✅ Orlandi, A. & Candidi, M. (2025). Toward a neuroaesthetics of interactions: insights from dance... *iScience* 28(5):112365. Texto completo fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12051600/fullTextXML (PMC12051600).
- ✅ Orlandi, A., Cross, E.S. & Orgs, G. (2020). Timing is everything: Dance aesthetics depend on the complexity of movement kinematics. *Cognition* 205:104446. PDF OA fetchado: https://eprints.gla.ac.uk/227924/1/227924.pdf (DOI 10.1016/j.cognition.2020.104446).
- ✅ Reber, R., Schwarz, N. & Winkielman, P. (2004). Processing fluency and aesthetic pleasure. *Pers Soc Psychol Rev* 8(4):364–382. Registro/abstract fetchado vía EuropePMC REST (PMID 15582859; DOI 10.1207/s15327957pspr0804_3).
- ✅ Forster, M., Leder, H. & Ansorge, U. (2013). It felt fluent, and I liked it. *Emotion* 13(2):280–289 (PMID 23088777, registro EuropePMC fetchado); y Goller et al. (2015) *PLoS One* (PMC4545584, registro fetchado) — fluidez sentida y relatividad del liking.
- ✅ Almansoof, H.S., Nuhmani, S. & Muaidi, Q. (2023). Role of kinetic chain in sports performance and injury risk. *J Med Life* 16(11):1591–1596. Texto completo fetchado vía https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10893580/fullTextXML (PMC10893580).
- 📊 Herzel, H. et al. (2026). Theoretical chronobiology of circadian timing. *npj Biol Timing Sleep* 3:32 (PMC13385350, registro+abstract fetchado vía búsqueda EuropePMC "Arnold tongue entrainment") — estructura de lenguas de Arnold en osciladores biológicos.
- 📊 Biber, S.W. et al. (2026, preprint). Heterogeneity in deep brain stimulation gamma enhancement explained by bifurcations in neural dynamics (EuropePMC PPR1268726, abstract fetchado) — lenguas de Arnold, sub-armónicos e histéresis.
- 📊 *J Exp Biol* 224(20):jeb227207 — Time-varying motor control strategy for proximal-to-distal sequential movements (solo snippet de búsqueda: https://journals.biologists.com/jeb/article/224/20/jeb227207/272482/ ; no fetchado completo).
- ✅ Johansson, G. (1973). Visual perception of biological motion... *Biol Psychol* 1:201–211 — citado vía la revisión Orlandi & Candidi 2025 (point-light, pSTS), no fetchado directamente.
- ✅ Hogan, N. & Sternad, D. (2007/2009) — discreto-vs-rítmico y sensibilidad de métricas de suavidad; citados dentro del texto completo fetchado de Balasubramanian et al. 2015 y Mohamed Refai et al. 2021.

**Fallos de fetch documentados** (política: un reintento, luego landing page + marca): jner.biomedcentral.com (Springer "Application Unavailable" ×2 intentos, ambas URLs semilla), pubmed.ncbi.nlm.nih.gov (CAPTCHA), pmc.ncbi.nlm.nih.gov (cookie wall), fullTextXML de PMC5448222 y PMC6873296 (error 500 del servidor EuropePMC). Todos los contenidos esenciales se obtuvieron por vías alternativas (EuropePMC REST search/fullText, PDF institucional).
