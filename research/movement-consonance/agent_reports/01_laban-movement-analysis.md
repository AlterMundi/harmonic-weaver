---
project: harmonic-weaver
title: "Laban Movement Analysis como teoría canónica de la calidad del movimiento: Effort, Shape, Space Harmony, certificación y operacionalizaciones computacionales"
type: research-report
tags: [research, movement-consonance, laban, lma, effort, shape, space-harmony, choreutics, labanotation, harmocap, hit]
date: 2026-09-24
confidence: high
---

# Reporte R1 — Laban Movement Analysis (LMA) canónico

> Carril: teoría canónica. Este reporte NO cubre sistemas movimiento→música (R2), matemática de suavidad/consonancia (R3), pitch/detuning (R4) ni diseño interno HIT (R5).
> Leyenda de confianza: ✅ primaria/peer-reviewed/libro · 📊 secundaria especializada · 📰 prensa/blog · ⚠️ contestado/draft · ❓ inferencia del agente a verificar.

## 0. TL;DR

1. **Effort en Laban es la actitud/intención interna hacia el uso de la energía, no la cinemática.** Las cuatro factores — Weight (Strong/Light), Time (Sudden/Sustained), Space (Direct/Indirect), Flow (Bound/Free) — describen el *cómo* intencional del movimiento; Laban lo define como el "impulso interno" que origina el movimiento y la interfaz entre lo mental y lo físico. ✅ Cualquier proxy cinemático es un *correlato observable* de esa actitud, nunca una medición canónica de Effort.
2. **Space Harmony / Choreutics ES el ancla canónica de "armonía" en Laban**: Laban construyó explícitamente su teoría espacial con metáforas musicales — escalas coreúticas análogas a escalas musicales, la "ley de los acordes de dirección espacial" (*Gesetz der Raumrichtungsakkordik*), teoría de la armonía (*Harmonielehre*) — sobre el icosaedro, el octaedro y el cubo del kinesfera. ✅ Para el modo "consonancia del movimiento", el linaje labaniano legítimo es Choreutics, no Effort.
3. **La confiabilidad inter-observador de LMA es débil a aceptable, y Effort es la categoría MENOS confiable**: Krippendorff's α global 0.47–0.68; Space 0.66 y Phrasing más altos; Effort 0.46; Shape aún menor. ✅ Un sistema automático que pretenda "medir Effort Laban" hereda ese techo de validez; las categorías más espaciales/temporales son las más observables.
4. **Existen operacionalizaciones cinemáticas publicadas y validadas contra anotación de CMAs**: Weight ≈ energía cinética máxima o desaceleración (correlación ~81% con CMA), Time ≈ aceleración/jerk (~77%), Shape Directional ≈ curvatura de trayectoria (~93%), Flow ≈ forma de curvas de velocidad/energía (~67%, el más débil). ✅ Estos son los números de referencia cuando HarMoCAP nombre sus proxies "laban_*".
5. **Flow es el factor más esquivo de computar desde pose/kinect**: los expertos certificados (CMAs) reportan que Weight "es lo más esquivo de capturar en video" y que la observación de Flow requiere información de tensión muscular (EMG) que el video no da; desde cámara 2D, Weight y Flow sólo se infieren indirectamente vía organización corporal. ✅
6. **El sistema de certificación (CMA, ~520 horas en LIMS) y la observación experta son cualitativos-encarnados, no cuantitativos**: LMA se aprende encarnando las calidades antes de observarlas; los CMAs alcanzan consenso por negociación kinestésica. ✅ La cuantificación existe (motifs contados, features cinemáticas) pero siempre como operacionalización secundaria del sistema observacional.
7. **La literatura perceptual apoya que propiedades cinemáticas simples cargan cualidad expresiva percibida**: desde point-light displays, la "activación" del afecto percibido correlaciona directamente con la cinemática (Pollick et al.), y la emoción se reconoce por encima del azar desde movimiento puro (Dittrich et al., 63%); pero la consistencia perceptual de los elementos Effort por observadores NO entrenados es imperfecta (sobre todo "Light"). ✅⚠️
8. **Guía para un escalar de "consonancia del movimiento"**: los anclajes labanianos más legítimos son (a) Space Harmony — escalas/acordes/counterbalance de tensiones espaciales, el constructo de Laban literalmente llamado "armonía"; (b) Free Flow — continuidad sin retención; (c) Effort Phrasing — dinámica de la intensidad del esfuerzo en el tiempo. Los pitfalls: llamar "Laban" a magnitudes cinemáticas (es Effort-canónico lo que no son), asumir que Flow es medible desde keypoints sin tensión muscular, y confundir suavidad (smoothness/jerk) con Free Flow (actitud de control vs. release). ❓✅

## 1. Effort: los cuatro factores, combinaciones y el framing de Laban

### 1.1 Definiciones canónicas

Effort (o "dinámica", como Laban lo llamaba a veces) es el sistema para entender las características sutiles del movimiento **respecto de la intención interna**. El ejemplo clásico: golpear con ira vs. alcanzar un vaso difieren poco en organización corporal (ambos extienden el brazo), pero la atención a la fuerza, el control y el timing es completamente distinta. ✅ (Wikipedia LMA, apoyado en Laban & Lawrence, *Effort*, 1947)

Los cuatro factores, cada uno un continuo con dos polaridades ("elementos"), y su doble encuadre *fighting/indulging* (combatir/conceder): ✅

| Factor | Polaridad "fighting" | Polaridad "indulging" | Qué atiende |
|---|---|---|---|
| **Space** | Direct | Indirect (flexible) | Atención al entorno: foco en un punto vs. escaneo de la totalidad |
| **Weight** | Strong | Light | Intención de fuerza: impacto/consistencia vs. delicadeza |
| **Time** | Sudden (quick) | Sustained | Urgencia: aceleración vs. deceleración; decisión de timing |
| **Flow** | Bound | Free | Actitud hacia la tensión corporal y el control: contención/progresión controlada vs. liberación |

Detalle por factor, tal como lo formulan fuentes primarias y revisores especializados:

- **Space = atención**. "Se escanea la totalidad del entorno en Indirect Space Effort o se investiga un punto específico en Direct Space Effort" (cita de texto de certificación en Fdili Alaoui et al., CHI 2017). ✅ No es "trayectoria recta vs. curva" — es dónde está puesta la atención espacial del mover; la rectitud de trayectoria es el proxy habitual. ✅
- **Time = cualidad de la urgencia/decisión temporal**. Los CMAs lo observan "a través de patrones de cambio en aceleración y deceleración" (CHI 2017). ✅ Sudden no es "rápido" en velocidad absoluta: es la actitud de inmediatez; Sustained es demorar la decisión. ✅
- **Weight = sentido del impacto/intención de fuerza**. "Cómo uno ejerce fuerza expresando Strength en Strong Weight o usando una intención delicada en Light Weight Effort" (CHI 2017). ✅ Es intención de peso, no peso físico: un movimiento Light puede ser rápido; un Strong puede ser lento. ✅
- **Flow = la cualidad de progresión del movimiento**: liberar (Free) vs. controlar/restringir (Bound). ✅ Flow es "responsable de la continuidad o ongoingness del movimiento"; sin Flow Effort, el movimiento queda contenido en una sola iniciación y acción. ✅ Chambers-Coe (2023, *Theatre, Dance and Performance Training*) explora precisamente el flow effort de Laban como parámetro del tacto — señal de que Flow sigue siendo un área de reinterpretación activa. ✅

### 1.2 El framing de Laban: effort como actitud interna

- Laban ve Effort como **el impulso interno — una sensación de movimiento, un pensamiento, un sentimiento o emoción — del cual el movimiento se origina; constituye la interfaz entre los componentes mental y físico del movimiento**. ✅ (Aristidou et al., citando el marco Laban)
- "Effort describe la actitud interna hacia el uso de energía" — fórmula estándar en la literatura computacional (Samadani et al.; Burton/LASG white paper). ✅
- Irmgard Bartenieff: "Dynamics da el feel, textura, tono o color del movimiento e ilumina la **actitud del mover, su intención interna**, y cómo ejerce y organiza su energía. Effort está en flujo y modulación constantes..." ✅ (cita de Bartenieff en CHI 2017)
- En *The Mastery of Movement* (1960/1971, MacDonald & Evans; ed. anotada por Lisa Ullmann), Laban plantea que "el hombre se mueve para satisfacer una necesidad" y que el movimiento corporal es análogo a la vida interna; los "effort rhythms" son los movimientos visibles del cuerpo humano **como resultado de su actitud interna**. ✅📊 (Selioni, *Choros* International Dance Journal, resumiendo el libro)
- Los Basic Effort Actions (BEAs) se definieron originalmente **observando movimientos de trabajadores fabriles** durante el trabajo de Laban con la industria en la WWII — el análisis de effort nació en estudios de eficiencia del trabajo ("effort economy"). ✅ (CHI 2017; LSSI: Laban extendió su trabajo a "assessment y entrenamiento de movimiento para trabajadores fabriles durante la guerra"). Esto es directamente relevante para el proyecto: la noción de *economía/eficiencia del esfuerzo* está en el origen mismo de la teoría. ✅

### 1.3 Combinaciones: acciones, estados y drives

- **Effort Actions (Action Drive)**: combinaciones de Space+Weight+Time **sin Flow**. Las ocho: Float, Punch (Thrust), Glide, Slash, Dab, Wring, Flick, Press. ✅ Tabla canónica (CHI 2017, Tabla 1): ✅

| Acción | Space | Time | Weight |
|---|---|---|---|
| Float | Indirect | Sustained | Light |
| Punch | Direct | Quick | Strong |
| Glide | Direct | Sustained | Light |
| Slash | Indirect | Quick | Strong |
| Dab | Direct | Quick | Light |
| Wring | Indirect | Sustained | Strong |
| Flick | Indirect | Quick | Light |
| Press | Direct | Sustained | Strong |

- **States**: combinaciones de DOS factores — Awake (Space+Time), Dreamlike (Weight+Flow), Distant (Space+Flow), Near/Rhythm (Time+Weight), Stabile (Space+Weight), Labile/Mobile (Time+Flow). ✅ (Wikipedia LMA, citando Dell 1975 / Moore & Yamamoto 1988)
- **Drives**: combinaciones de TRES factores — Action Drive (W+S+T, falta Flow), Passion Drive (W+T+Flow, falta Space), Spell Drive (W+S+Flow, falta Time), Vision Drive (S+T+Flow, falta Weight). ✅
- **Full effort** (los 4 factores igualmente expresados) se considera un evento raro y usualmente momentáneo. ✅
- Los estados y drives se discuten como portadores de características psicológicas distintas. ✅ Los Action Efforts se usan extensivamente en escuelas de actuación (ALRA, Manchester School of Theatre, LIPA) para entrenar cambios rápidos entre manifestaciones físicas de emoción. ✅

### 1.4 Effort Phrasing

Además de los factores, LMA distingue el **phrasing**: dónde cae el énfasis dentro de la frase de movimiento — impulsive (al inicio), swing (en el medio), corrective (al final), o condicional. ✅ (formalización del estudio de confiabilidad de Bernardet et al.). En el trabajo de Ek/Visi/Froneman (2026) se anota además la fluctuación de intensidad del effort ("Effort Phrasing") como señal de entrenamiento para un modelo de regresión. ✅ Relevante para R5: el phrasing es el constructo labaniano de *dinámica temporal de la intención*, más cercano a un envelope musical que los factores puntuales. ❓

## 2. Shape y Space Harmony: la dimensión "armónica" canónica de Laban

### 2.1 Shape

Shape describe **cómo el cuerpo cambia de forma y qué lo motiva**: ✅

- **Shape Forms**: formas estáticas (wall-like, ball-like, pin-like). ✅
- **Modes of Shape Change**: (a) *Shape Flow* — relación del cuerpo consigo mismo (stream of consciousness motriz; encogerse/estirarse con la respiración); (b) *Directional* — el cuerpo se dirige a algo del entorno, subdividido en Spoke-like (puñear, señalar: radio desde el centro) y Arc-like (balancear una raqueta: arco); (c) *Carving/Shaping* — el cuerpo esculpe activamente en 3D el volumen del entorno (amasar pan, escurrir una toalla). ✅
- **Shape Qualities**: Opening/Closing en general; Rising, Sinking, Spreading, Enclosing, Advancing, Retreating como dimensiones espaciales específicas. ✅
- **Shape Flow Support**: el torso cambia de forma para soportar el movimiento del resto del cuerpo; suele tratarse como presente/ausente. ✅

Samadani et al. operacionalizan Shape Directional con la **curvatura media de trayectoria** (arc-like vs. spoke-like) y obtienen la correlación más alta de todo su estudio con la anotación de CMA (93%). ✅

### 2.2 Space Harmony (Choreutics): los sólidos platónicos

Laban llamó a su teoría espacial **Space Harmony** o **Choreutics**; Eukinetics era el nombre de sus estudios de effort. ✅ (LSSI; Wikipedia LMA)

- Laban describió un sistema de geometría basado en **formas cristalinas, sólidos platónicos y la estructura del cuerpo humano**, y sostenía que hay maneras de organizarse y moverse en el espacio que son específicamente armónicas **en el mismo sentido en que la música puede ser armónica**; algunas combinaciones son "teórica y estéticamente más placenteras". ✅ (Wikipedia LMA, sección Space)
- **Kinesphere**: el espacio personal alrededor del cuerpo alcanzable sin dar un paso — Near/Mid/Far reach. ✅ Se define tanto físicamente (alcance) como psicológicamente (el espacio que el mover siente como suyo). ✅
- **26 direcciones**: derivadas de los vértices del octaedro, el icosaedro y el cubo, con símbolos propios usables en notación. ✅
- Arquitectura dimensional: ✅
  - **3 Dimensiones** (vertical, horizontal/lateral, sagittal/front-back) cruzando en el centro de gravedad → **Octaedro**; Dimensional Scales.
  - **3 Planos** (door/vertical=vertical+horizontal; table/horizontal=horizontal+sagittal; wheel/sagittal=vertical+sagittal), con sus diámetros → conectando esquinas de los planos se llega al **Icosaedro**; escalas Primary, Axis, Girdle, A y B.
  - **4 Diagonales** del cubo → Diagonal Scale.
  - **Inclinations**: diagonales deflectadas por una dimensión (Flat=side-side, Steep=up-down, Suspended=front-back). ✅
- **Pathways**: Central (desde/a través del centro), Peripheral (a lo largo del límite del kinesfera), Transverse (entre centro y periferia). ✅

### 2.3 Las metáforas musicales de Laban — documentación explícita

Este es el hallazgo central del carril canónico para el proyecto "consonancia del movimiento": **Laban usó vocabulario musical de manera sistemática, no decorativa**:

- **"Ley de los acordes de dirección espacial" (*Gesetz der Raumrichtungsakkordik*)** — una de las leyes explícitas del movimiento corporal enumeradas en *Choreographie* (1926): junto a la ley del contramovimiento (*Gesetz der Gegenbewegung*), la del equilibrio (*Gleichgewichtsgesetz*), la de la secuencia (*Gesetz der Folge*), la del fluir-desde-el-centro (*Aus-der-mitte-fliessens*) y la de las correlaciones. ✅ (Longstaff, traducción anotada de *Choreographie*)
- **"Harmonielehre" (teoría de la armonía)** aparece como nombre de capítulo/doctrina en *Choreographie*. ✅ (Longstaff)
- **Escalas coreúticas**: "Análogas a una escala musical, cada escala coreútica (o escala de space harmony) abarca sistemáticamente rangos particulares de espacio" ✅ (Wikipedia Space Harmony); en la traducción de Longstaff: "Análogas a escalas musicales, una variedad de 'escalas' (*Skalen*) se desarrolla para el movimiento corporal... la realización de las escalas de movimiento es considerada una práctica prescriptiva" ✅.
- **Definición de escala de Laban**: "Hay un orden lógico subyacente a la evolución de las varias formas en el espacio que puede realizarse en escalas. Las escalas son series graduadas de movimiento que atraviesan el espacio en un orden particular de tensiones balanceadas según un esquema específico de relaciones." ✅ (Laban, citado vía tesis de Barnard/Columbia)
- **Vocabulario de "nota falsa"**: en el glosario de *Choreographie*, "false-position (*Falschposition*)" se explica como "igual que una 'nota falsa' en música, fuera de armonía". ✅ (Longstaff)
- Las escalas presentan simetría tridimensional (rotacional y especular), forman circuitos cerrados y usan cada vértice o cada arista del poliedro una sola vez; el patrón de muchas escalas se basa en el **trefoil knot** ("9-part knot" en manuscritos inéditos de Laban). ✅ (Wikipedia Space Harmony, citando Moore)
- La tesis de Merolla (Barnard College, 2020) desarrolla la comparación con el contrapunto de Bach: la exigencia labaniana de que "cada movimiento del miembro en una dirección particular sea contrabalanceado por una contra-dirección aproximada" se lee como contrapunto corporal; y los puntos numerados del icosaedro sobre el cuerpo como razones análogas a las proporciones pitagóricas de la armonía musical. 📊 (tesis de grado — interpretación de la autora, no texto de Laban)
- Carol-Lynne Moore publicó *The Harmonic Structure of Movement, Music, and Dance According to Rudolf Laban: An Examination of His Unpublished Writings and Drawings* (Edwin Mellen Press, 2009) — el examen de referencia del material inédito donde Laban relaciona movimiento, música y danza. ✅ (registro editorial verificado; ⚠️ el libro en sí no está accesible online)
- Lynn Matluck Brooks, "Harmony in Space: A Perspective on the Work of Rudolf Laban", *The Journal of Aesthetic Education* 27(2), 1993, pp. 29–41 — artículo académico sobre la noción de armonía en Laban. ✅ (registro bibliográfico JSTOR; texto completo tras paywall)
- Caveat de la tesis de Merolla: "no hay conocimiento conocido de que Laban supiera leer música" — sus metáforas musicales son estructurales (escalas, acordes, tensiones balanceadas, contrapunto), no técnicas de teoría musical. 📊⚠️

**Conclusión del carril canónico para el proyecto**: cuando el Harmonic Beacon hable de "consonancia del movimiento", el precedente labaniano legítimo es **Space Harmony**: movimiento que sigue escalas/órdenes de tensiones balanceadas en el kinesfera, con counterbalance direccional — no Effort. Effort aporta el vocabulario de la *calidad dinámica/intencional* (fuerza, urgencia, atención, fluidez); Choreutics aporta el de la *armonía espacial* (acordes de dirección, equilibrios, escalas). Ambos conviven en LMA como categorías separadas (Effort vs. Space). ✅❓

## 3. Certificación y observación: ¿cuantitativo o cualitativo?

### 3.1 LMA vs. Bartenieff Fundamentals

- LMA contemporáneo se organiza en las cuatro categorías **BESS** — Body, Effort, Shape, Space — elaboradas por Irmgard Bartenieff a partir de las dos categorías originales de Laban (Eukinetics=Effort, Choreutics=Space Harmony). ✅ En UK, influidos por Lisa Ullmann, se usa otra organización: Body, Effort, Space y Relationship, con Shape entretejido. ✅
- **Bartenieff Fundamentals (BF)** es el brazo somático del sistema: patrones de organización corporal y conectividad (los "Basic 6": Breath Support, Rocking Preparation, Thigh Lift, Head-Tail/Spinal Flexion, Upper-Lower/Arm-Leg diagonal, Diagonal Roll), más los patrones de conectividad corporal total (body-half, upper-lower, core-distal, head-tail, diagonal, ipsilateral/contralateral — los seis de Hackney). ✅ BF se practica como repatterning somático que soporta la integración corporal; es experiencia de primera persona, no esquema de medición. ✅ (Longstaff 2004; LIMS)
- **Kestenberg Movement Profile (KMP)** es un sistema derivado (Judith Kestenberg) que amplía Effort/Shape para evaluación psicoterapéutica — mencionado aquí sólo para delimitar que no es parte del LMA canónico. 📊❓

### 3.2 Certificación

- **LIMS® (Laban/Bartenieff Institute of Movement Studies, NYC)**: programa profesional post-baccalaureate que lleva al título internacionalmente reconocido de **Certified Movement Analyst (CMA)**; formación de ~520 horas teóricas y prácticas; formatos anual y modular; el egresado debe poder articular verbalmente y demostrar físicamente los conceptos de Body, Effort, Shape y Space, los principios de BF, y registrar/interpretar datos de movimiento usando Motif y escritura de frases. ✅
- **LSSI (Laban/Bartenieff and Somatic Studies International)**: programa aprobado por ISMETA; califica "CMA-SPs". ✅ **Integrated Movement Studies** califica "CLMAs". ✅ El **Laban Guild** (UK) preserva el trabajo y ofrece cursos; **Trinity Laban Conservatoire** ofrece un diploma de postgrado en Choreological Studies. ✅
- **ICKL (International Council of Kinetography Laban, fundada 1959)** es el cuerpo decisorio sobre ortografía y principios del sistema de notación; conferencia bienal; ~60 miembros/fellows activos. ✅

### 3.3 Cualitativo vs. cuantitativo

- LMA es **primariamente un sistema observacional cualitativo, encarnado**: "sistema empírico observacional y analítico basado en conocimiento adquirido a través de práctica somática y encarnada". ✅ (Bernardet et al. 2019)
- Los CMAs observan **encarnando primero la calidad** (kinesthetic empathy) y alcanzan confiabilidad por consenso negociado en observación grupal. ✅ (CHI 2017, citando Fdili Alaoui et al. 2015)
- La tradición computacional asume LMA como método de codificación objetivo de tercera persona; Bernardet et al. señalan que esto está en tensión con la práctica tradicional primera/segunda persona. ✅
- Sí existen protocolos de **cuantificación**: Tsachor & Shafir (2019) describen un método multi-etapa para convertir movimiento no guionado en variables LMA cuantificables (protocolo de Davis de 3 pasos + motifs + piloto + cuantificación de prevalencia por emoción) para análisis estadístico en dance/movement therapy. ✅
- **Labanotation/Kinetography Laban** es la capa simbólica "cuasi-cuantitativa": ver §4.1.
- **Confiabilidad medida** (el dato duro): Bernardet et al. 2019 (*PLoS ONE*) — primer estudio comprehensivo de confiabilidad inter-rater de LMA como sistema completo, con CMAs como raters: Krippendorff's α entre **0.473 (una sola ronda)** y **0.676 (combinación "óptima" de dos rondas)**; por categoría: Space α≈0.66, Effort α≈0.46; "Space y Phrasing se califican más confiablemente; la categoría Effort es la más difícil de acordar". ✅ Estudios previos: McCoubrey encontró confiabilidad significativa para weight/space/time pero no para free(flow), indirect(space), sustained(time); Davis (1987, LIMS reliability project) encontró acuerdo para strong/direct/sudden y, en danza, sustained/light, pero confiabilidad pobre para dirección espacial. ✅

**Implicación para HarMoCAP**: si los observadores humanos expertos apenas alcanzan acuerdo moderado en Effort, un "laban_weight_proxy" no puede validarse contra una ground truth de Effort con precisión alta; la validación honesta es correlación con consenso de CMAs (lo que hace Samadani et al.) y declaración explícita del techo. ❓✅

## 4. Operacionalizaciones computacionales de LMA

### 4.1 Labanotation / Kinetography Laban

- Sistema de notación publicado por Laban en **Schrifttanz** (1928); versiones francés/inglés 1930; el manual canónico de Albrecht Knust, *Das Handbuch der Kinetography Laban*, 8 volúmenes (1946–50). ✅ (Wikipedia Labanotation)
- Dos linajes divergieron en los 1930s–50s: **Kinetography Laban** (Europa, conservadora, sólo descripción espacial) y **Labanotation** (EEUU, Ann Hutchinson Guest / Dance Notation Bureau, expandida para expresar motivación/significado). El ICKL (1959) existe para estandarizar. ✅
- Estructura del sistema: símbolos en un **pentagrama vertical leído de abajo hacia arriba**; columnas = partes del cuerpo; forma del símbolo = dirección (9 direcciones básicas); sombreado = nivel (alto/medio/bajo); longitud del símbolo = duración; el pentagrama se organiza en compases que corresponden a los compases de la música, con marcas de beat. ✅ (Dance Notation Bureau, "Labanotation Fundamentals")
- Es un sistema **simbólico-discreto**, no numérico-continuo: registra "qué" espacial/temporal con precisión, pero la calidad dinámica (effort) es anotación de motivación en la variante Labanotation. ✅❓
- En computación existen intentos de usar Labanotation como capa intermedia de análisis desde depth sensors (p.ej. Borge Kordts et al. 2015, citado en CHI 2017). ✅

### 4.2 Estudios de motion capture / sensores que midieron Effort

Revisión ordenada por tipo de evidencia (todo verificado en las fuentes listadas):

**(a) Cuantificación cinemática validada contra CMA — el estudio de referencia:**
- **Samadani, Burton, Gorbet & Kulić, "Laban Effort and Shape Analysis of Affective Hand and Arm Movements"** (2014, LNCS/Springer; full text verificado). Adaptan dos esquemas de cuantificación (Q1 agregado, Q2 por parte corporal) de posición/velocidad/aceleración/jerk: ✅
  - **Weight** Q1 = máximo de la suma de energías cinéticas de las partes en movimiento (masas normalizadas a 1); Q2 = máximo de desaceleración (la desaceleración implica absorción de energía cinética, ej. al final de un punch).
  - **Time** Q1 = máximo de la serie de aceleraciones ponderadas; Q2 = aceleración neta acumulada.
  - **Space** = producto interno de tangentes de trayectorias (monótono ⇒ Direct; fluctuante con múltiples cambios ⇒ Indirect).
  - **Flow** = esquema propio (Q2 adaptado): predice la anotación del CMA con correlación **67%** — el más bajo.
  - **Shape Directional** = curvatura media de trayectoria: correlación **93%**.
  - Resultados contra anotación CMA: **Weight 81%, Time 77%**, Space no verificable por desbalance del dataset (mayoría Direct). Todas las correlaciones altas, estadísticamente significativas (p<0.05). ✅
  - Limitación reconocida: el dataset constreñía los paths (parada obligada), lo que limita variación de Flow. ✅

**(b) Modelo multimodal guiado por expertos (CMAs):**
- **Fdili Alaoui, Françoise, Schiphorst, Studd & Bevilacqua, "Seeing, Sensing and Recognizing Laban Movement Qualities" (CHI 2017)**. Entrevistan a 2 CMAs senior para derivar los cues visuales/kinestésicos reales de observación, y diseñan sensores por factor: ✅
  - **Time → norma del jerk** (derivada de la aceleración), desde IMU 6-DOF en la muñeca: legitima jerk como feature de Sudden vs. Sustained.
  - **Weight → EMG** de antebrazos (contracción vs. release muscular): los CMAs afirman que el video disminuye la capacidad de percibir Weight — "Weight es lo más esquivo de capturar en video" — y que lo interpelan empáticamente desde organización corporal, uso del piso y soporte respiratorio.
  - **Space → expansión/contracción corporal** (distancia codos–pecho), vinculado por los CMAs a las Shape Qualities Spreading (Indirect) / Enclosing (Direct); la intención indirecta real incluye conciencia del espacio detrás del cuerpo y gaze, que el video no captura bien.
  - Conclusión del paper: "modelar cualidades de Effort permanece como una de las tareas más desafiantes y **un problema no resuelto** en representación y computación del movimiento". ✅

**(c) Reconocimiento desde trackers/VR y HMMs:**
- **Garcia & Ronfard, "Recognition of Laban Effort Qualities from Hand Motion" (MOCO 2020)**: desde señal 6D de trackers VR en la mano, extraen features euclídeas, equi-afines y de moving frame; las **equi-afines resultan altamente discriminantes** para qualities de Effort; comparan HMMs por 6 elementos (light/strong/sudden/sustained/direct/indirect) vs. HMMs por 8 action verbs combinados — el segundo método mejora; conclusión: señales de baja dimensión pueden predecir motion qualities "con precisión razonable". ✅
- **EURASIP JIVP 2017 (Laban movement analysis and hidden Markov models for dynamic 3D gesture recognition)**: features LMA + diccionario de poses (k-medians) + HMMs; >92% de reconocimiento en 11 acciones; validado también en datasets Microsoft Gesture y UTKinect. ✅
- **Aristidou et al., "Emotion Recognition for Exergames using Laban Movement Analysis"** (ACM, 2013/2015): features de cuerpo basadas en Effort (trayectorias de manos, pies, cabeza; aceleración, jerk, velocidad) clasifican 4 estados emocionales (concentración, meditación, excitación, frustración) "a tasa muy alta". ✅
- **Turab, Colantoni & Muselet (arXiv 2025)**: dos papers que mejoran descriptores LMA sobre keypoints 3D de bailarines profesionales — emotion recognition en danza contemporánea (hasta 96.85% con RF/SVM + XAI) y dance style recognition. ⚠️ (preprints arXiv, no peer-reviewed al momento de este reporte)

**(d) Generación de movimiento afectivo:**
- **Samadani et al., "Affective Movement Generation using Laban Effort and Shape and HMM-based Data Representation" (arXiv 2006.06071)**: dado un motion path objetivo y una emoción, busca en dataset etiquetado en espacio Effort/Shape, abstrae con HMM y modula el path; emociones reconocidas al 72% por modelo automático + user study. ✅
- **Chi, Costa, Zhao & Badler, "The EMOTE model for effort and shape" (SIGGRAPH 2000)**: modelo de animación 3D que integra Effort y Shape de LMA para animar personajes con datos de mocap — el trabajo seminal del grupo de Badler (UPenn). ✅ (verificado vía referencia en Wikipedia LMA y CHI 2017; PDF no accesible en esta corrida)
- **Eyesweb (Camurri et al.)**: plataforma de video-streaming cuyas expressive features aproximan: Space ≈ extensión/contracción de miembros y rectitud; Time ≈ duración de pausas y cambios de tempo; Weight ≈ cantidad de tensión; Flow ≈ formas de las curvas de velocidad y energía, ritmo y cantidad de aceleración. ✅ (descripción en CHI 2017; es el antecedente directo de las features `contraction`/`expansion`/`qom` de HarMoCAP — verificar contra R2/R5)

**(e) Puente biomecánica↔LMA:**
- **Kim, Vette, Ottes & Wahl, "Bridging Biomechanics and Laban Movement Analysis" (Sensors 2024)**: integra LMA con principios biomecánicos en el golf swing. ✅ (texto completo PMC verificado)
- **Ek, Visi & Froneman, "Real-Time Detection of Laban Effort Factors in Music Performance Using Machine Learning" (Arts 15(7):157, 2026)**: anotación experta de Effort + Effort Phrasing sobre video de una sonata de Brahms para clarinete, revisada con el performer (stimulated recall), y usada como training data para regresión interactiva (GIMLeT/Max) sobre datos de gesto en tiempo real; el modelo captura "matices de variación de Effort casi inobservables humanamente"; mindset de small-data, idiosincrásico por performer, no generalizable. ✅ Es el ejemplo más reciente de Effort-LMA operando como señal de control musical en vivo — frontera directa con R2/R5.

**(f) Segmentación y clasificación general:**
- **Bouchard & Badler, "Semantic Segmentation of Motion Capture Using Laban Movement Analysis" (IVA 2007, UPenn)**: segmentación semántica de mocap con conceptos LMA. ✅ (verificado vía referencia; PDF tras timeout del repositorio)

### 4.3 Críticas conocidas a la reducción de LMA a números

1. **Categoría equivocada**: Effort es una descripción de la *actitud interna*; las features cinemáticas miden *output observable*. La literatura seria nunca afirma medir Effort — afirma estimar correlatos (Samadani et al.: "correlatos físicos medibles... permiten cuantificación"; CHI 2017: "features que correlacionan estrechamente con las definiciones de Efforts"). ✅ Llamar al resultado "medición Laban" es un error categorial que el propio campo evita. ✅
2. **Techo de confiabilidad humana**: α de Effort ≈ 0.46 entre CMAs (Bernardet et al. 2019) — cualquier validación automática contra anotación humana está acotada por esa variabilidad. ✅
3. **Inconsistencia perceptual**: Kim, Neff & Lee (ACM TAP 2022) construyen un database de videos con los 8 extremos de elementos Effort y evalúan observadores: "aunque los observadores no perciben el elemento Effort 100% como intencionado, las tasas de respuesta verdadera de siete elementos superan a las falsas, **excepto para Light**"; un elemento Effort tiende a co-ocurrir perceptualmente con elementos de otros factores (indirect↔free, light↔free). ✅ Es decir: la categoría no es perceptualmente pura ni para humanos — menos para un pipeline.
4. **El problema de Flow**: desde keypoints sin información muscular, Bound/Free (tensión/control) no es observable directamente; los CMAs lo observan vía cues kinestésicos y sugieren EMG (CHI 2017); la cuantificación de Flow es la de menor correlación (67%, Samadani et al.). ✅
5. **Weight sin masa ni fuerza**: Weight Effort es intención de fuerza; la energía cinética con masas normalizadas es un proxy doblemente indirecto (Samadani et al. fijan α=1 para todas las partes). ✅
6. **Dependencia del entrenamiento**: la observación de Effort requiere encarnar la calidad; observadores no entrenados difieren sistemáticamente (CHI 2017, citando Mentis et al.). ✅
7. **Contexto perdido**: la crítica de Davis incorporada por Bernardet et al.: los raters marcan presencia de qualities "en cualquier momento del clip", sin distinguir movimiento postural vs. gestual, parte corporal o grado de intensidad — la granularidad del coding cambia los resultados. ✅
8. **Contra-crítica constructiva**: Tsachor & Shafir (2019) demuestran que SÍ se puede cuantificar sistemáticamente (motifs, prevalencia, frecuencia, duración, énfasis) con protocolo replicable — la crítica no es "no cuantificar" sino "cuantificar declarando la transformación". ✅

## 5. Literatura empírica: Effort/movimiento ↔ calidad percibida

### 5.1 Percepción de cualidad desde movimiento (incluye point-light)

- **Dittrich, Troscianko, Lea & Morgan (1996), "Perception of emotion from dynamic point-light displays represented in dance", *Perception* 25**: bailarines entrenados comunican miedo, ira, pena, alegría, sorpresa y asco; reconocimiento desde full-light 88%, desde **point-light upright 63%** (significativamente sobre azar); la inversión del display degrada el reconocimiento biológico-motor a cerca del azar (pero aún sobre azar). El análisis espacio-temporal del movimiento de los puntos se relaciona con la discriminabilidad de las emociones. ✅ — Evidencia de que la información de *calidad* sobrevive a la eliminación casi total de la forma: sólo kinemática de 13 puntos.
- **Pollick, Paterson, Bruderlin & Sanford (2001), "Perceiving affect from arm movement", *Cognition* 82**: point-light de beber/golpear con 10 afectos; MDS de matrices de confusión → espacio psicológico tipo circumplejo (Dim1=activación, Dim2=placer); **"Dimension 1 ... fue altamente correlacionada con la cinemática del movimiento"** — la activación percibida es una cue "formless" ligada directamente a la cinemática; el placer (pleasantness) parece viajar en las relaciones de fase entre segmentos de miembros. ✅ — Dato crucial para R3/R5: la percepción de "energía/activación" es cinemática directa, pero la valía estética depende de coordinación inter-segmentos (fase), no de un solo canal.
- **Camurri, Lagerlöf & Volpe (2003), "Recognizing emotion from dance movement: comparison of spectator recognition and automated techniques", *IJHCS* 59(1-2)**: compara ratings de espectadores con clasificación automática de gesto expresivo en danza; identifica qué cues de movimiento comunican intención expresiva y valida modelos de análisis contra ratings humanos. ✅ (abstract verificado en ScienceDirect)
- **Kim, Neff & Lee (2022), "The Perceptual Consistency and Association of the LMA Effort Elements", *ACM Transactions on Applied Perception* 19(1)**: el estudio perceptual directo de los elementos Effort (ver §4.3.3). ✅

### 5.2 Estética del movimiento y expertise

- **Calvo-Merino, Jola, Glaser & Haggard (2008), "Towards a sensorimotor aesthetics of performing art", *Consciousness and Cognition* 17(3):911–922**: fMRI durante visión pasiva de 24 movimientos de danza; los movimientos con ratings estéticos altos vs. bajos activan diferencialmente corteza occipital bilateral y **premotor derecho** — respuesta estética automática sensomotora a la danza. ✅ (manuscrito aceptado verificado)
- **Christensen & Calvo-Merino (2013), "Dance as a subject for empirical aesthetics", *Psychology of Aesthetics, Creativity, and the Arts* 7(1):76–88**: revisión que conecta percepción/reconocimiento de movimiento con experiencia estética de la danza; señala que features comunes de estilos de danza de todo el mundo sugieren una capacidad cognitiva evolucionada de apreciación estética del movimiento. ✅ (registro+abstract verificados)
- **Broughton & Davidson (2016), "An Expressive Bodily Movement Repertoire for Marimba Performance, Revealed through Observers' Laban Effort-Shape Analyses...", *Frontiers in Psychology* 7:1211**: 6 músicos profesionales entrenados hacen Effort-Shape analysis de grabaciones de marimba; emerge un repertorio pequeño de movimientos corporales percibidos como expresivos (body sway + acciones locales generadoras de sonido), aliado a estructura musical, técnica e interpretación; las observaciones consensuadas se examinan como ground truth cualitativa. ✅
- **Broughton, et al. (2014), "Action and familiarity effects on self and other expert musicians' Laban effort-shape analyses...", *Frontiers in Psychology* 5:1201**: el análisis Effort-Shape de músicos expertos varía según su expertise motora específica (percusión vs. canto) y familiaridad con la música; los hallazgos apoyan modelos percepción–acción y cognición encarnada — **la observación de Effort es expertise-dependiente incluso entre expertos**. ✅

### 5.3 Qué NO encontré (gap honesto)

- No encontré un estudio que mapee explícitamente "Free Flow ↔ percepción de fluidez/gracia" como variable dependiente aislada con estadística limpia. Lo más cercano: Pollick (activación~cinemática), Dittrich (emoción desde point-light), Kim/Neff/Lee (consistencia de elementos Effort) y Stevens/Broughton (Effort-Shape en música). La hipótesis del proyecto "movimiento eficiente/consonante ⇒ placer visual" es consistente con Calvo-Merino (respuesta sensomotora a danza) y con la interpretación de Pollick sobre relaciones de fase, pero **no existe un experimento publicado que mida 'consonancia del movimiento' como constructo** — eso es terreno nuevo que R3/R5 deberán operacionalizar. ❓

## 6. Guía explícita: el escalar "consonancia del movimiento" y los pitfalls de llamar 'Laban' a los proxies

### 6.1 Anclajes labanianos legítimos (ordenados por legitimidad canónica)

1. **Space Harmony / Choreutics — EL ancla de "armonía"**. Si el proyecto quiere un escalar cuyo nombre invoque armonía/consonancia con linaje labaniano, Choreutics es el constructo correcto: tensiones balanceadas, counterbalance direccional (cada dirección contrabalanceada por su contra-dirección), escalas como "series graduadas de movimiento... en un orden particular de tensiones balanceadas", acordes de dirección espacial. ✅ Un candidato operacional: grado en que el movimiento del cuerpo recorre/respeta patrones de balance direccional del icosaedro del kinesfera (ej. counterbalance de trayectorias, compensación de tensiones entre dimensiones). ❓ (el constructo es canónico; la operacionalización es diseño nuevo)
2. **Free Flow (continuidad sin retención)**. Flow es "la continuidad u ongoingness del movimiento" ✅; Free Flow = progresión por liberación vs. Bound = progresión por control ✅. Es el factor Effort más cercano a "el movimiento fluye sin desperdicio". Pero: la correlación más baja con juicio experto entre los cuatro factores (67%, Samadani et al.) ✅, y los CMAs advierten que la tensión muscular real requiere EMG (CHI 2017) ✅. Desde keypoints de cámara, un `flow_proxy` honesto es "suavidad de la progresión + ausencia de freezing/staccato", no Flow canónico. ❓
3. **Effort Phrasing**. El patrón temporal de la intensidad del esfuerzo (énfasis inicial/medio/final) es canónico ✅ y es lo que Ek et al. usan como señal de entrenamiento para detección en tiempo real en música ✅ — el ancla más directa para "fraseo consonante" (phrasing que el sistema puede aprovechar rítmicamente). ❓
4. **Eukinetics como "economía del esfuerzo"**. El análisis de effort nació de estudios de eficiencia del trabajo industrial ✅; "effort economy" es lenguaje del propio Laban & Lawrence (título: *Effort: economy of human movement*, ed. Princeton Book 1974). ✅ Un escalar de "eficiencia del esfuerzo" tiene por tanto precedente conceptual directo — aunque Laban nunca lo redujo a una magnitud cinemática. ❓
5. **Shape change quality (Directional: arc-like vs. spoke-like; Carving)**. Operacionalizada con curvatura de trayectoria al 93% de correlación con CMA ✅ — la subcategoría LMA con mejor track record de medición automática. Útil si "consonancia" incluye cualidad de la forma del recorrido (arcos fluidos vs. trayectorias angulosas). ❓
6. **Weight-continuity NO es un constructo labaniano**. En Laban, Weight es polaridad de intención de fuerza, no continuidad; la continuidad pertenece a Flow/phrasing. Un "weight_proxy" continuo (ej. energía cinética suavizada) mezcla dos factores — hay que nombrarlo como compuesto, no como Weight. ⚠️❓

### 6.2 Pitfalls de llamar "Laban" a los proxies cinemáticos

1. **Error categorial**: Effort describe intención interna; la cinemática describe resultado. La literatura seria dice "proxy/correlato/operacionalización" (ver §4.3.1). El schema de HarMoCAP ya hace lo correcto al declarar "operacionalizaciones cinemáticas, no mediciones Laban canónicas" ✅ — mantener esa fórmula en toda la documentación y los nombres de features es la práctica validada por el campo. ✅
2. **Techo de validez humana**: si los CMAs acuerdan Effort con α≈0.46 ✅, ninguna validación de `laban_*_proxy` contra "ground truth Effort" puede aspirar a exactitud tipo instrumento físico. Validar contra consenso CMA y reportar correlación (método Samadani) es el estándar honesto. ❓✅
3. **Contaminación perceptual entre factores**: indirect↔free, light↔free co-ocurren perceptualmente ✅ — los proxies derivados de la misma cinemática van a estar correlacionados entre sí por construcción; no tratarlos como canales independientes.
4. **Flow/Weight sin señales fisiológicas**: desde cámara 2D/3D-pose, ni tensión muscular ni intención de fuerza son observables ✅; los proxies deben documentar qué cue observable sustituye al constructo (aceleración→Time, energía cinética→Weight, expansión/contracción→Space, forma de curva de velocidad→Flow, siguiendo CHI 2017/Samadani). ✅
5. **Confundir smoothness con consonancia**: jerk-bajo (suavidad) es condición de Free Flow pero no es Space Harmony ni Effort economy; un movimiento puede ser suavísimo y espacialmente "desharmonizado" (sin counterbalance) o rítmicamente muerto. Los constructos canónicos son distintos y el escalar del proyecto debe declarar cuál (o qué combinación) está midiendo. ❓
6. **Nombrar "consonancia"**: en Laban, "harmony" tiene un significado técnico espacial (Space Harmony). Usar "movement consonance" como término nuevo del proyecto es legítimo si se documenta que NO es un término LMA — igual que HIT define consonance como logro relacional de acople estable, no como propiedad de razones aisladas (contexto del brief; verificar en R5). ❓
7. **Validación perceptual pendiente**: el claim fundacional del proyecto ("la percepción de placer visual ES la consonancia perceptual") tiene apoyo indirecto (Dittrich: emoción desde point-light; Pollick: activación~cinemática, placer~relaciones de fase; Calvo-Merino: respuesta sensomotora estética) ✅ pero ningún estudio midió consonancia-de-movimiento como constructo — el protocolo de video propuesto en R5 será investigación original, y debe citar estos tres papers como fundamento y limitación. ❓

### 6.3 Recomendación sintética para el diseño

Un escalar de "consonancia del movimiento" con vocabulario defendible podría declararse como: **"proxy de Space-Harmony cinemática + Free-Flow + economy de Effort"**, construido desde (a) balance/counterbalance direccional de trayectorias en el kinesfera (linaje Choreutics), (b) suavidad de progresión y ausencia de retención (linaje Flow, con la advertencia EMG), (c) aprovechamiento de energía cinética sin frenados disipativos (linaje effort-economy, con la advertencia de que Weight canónico es intención). Cada componente con su cita, cada uno marcado como operacionalización — nunca como medición Laban. ❓✅

## Sources

- ✅ https://en.wikipedia.org/wiki/Laban_movement_analysis — LMA: categorías BESS, tabla de factores Effort, acciones/estados/drives, Shape, Space, kinesphere, certificación (verificado en texto; Wikipedia cita a su vez Laban & Lawrence 1947, Dell 1975, Hackney 1998)
- ✅ https://en.wikipedia.org/wiki/Space_Harmony — Space Harmony/Choreutics: sólidos platónicos, 26 direcciones, dimensiones/planos/diagonales, escalas análogas a escalas musicales, trefoil knot (cita Laban *Choreutics* 1966, Dell *Space Harmony* 1977, Bradley *Rudolf Laban* 2009, Moore 2011)
- ✅ https://en.wikipedia.org/wiki/Labanotation — historia Schrifttanz 1928, Knust, divergencia Labanotation/Kinetography Laban, ICKL
- ✅ https://ickl.org/ — International Council of Kinetography Laban: fundación 1959, rol de cuerpo decisorio de ortografía/principios
- ✅ https://labaninstitute.org/certification-programs/ — LIMS: certificación CMA, 520 horas, competencias Body/Effort/Shape/Space + Bartenieff Fundamentals
- ✅ https://labaninternational.org/scope-of-practice/movement-analysis/ — LSSI: LMA/LBMS como sistema cualitativo; Choreutics=Eukinetics originales; extensión Body/Shape por Bartenieff/Lamb/Kestenberg; trabajo fabril de Laban en WWII
- 📊 http://www.laban-analyses.org/jeffrey/2004-Bartenieff-fundamentals-Developmental-movement/summary-of-concepts.htm — Longstaff: Bartenieff Fundamentals "Basic 6" y patrones de conectividad (Hackney)
- ✅ http://www.laban-analyses.org/jeffrey/2011-Rudolf-Laban-1926-Choreographie/annotations-introduction/major-concepts-Laban-1926-Choreographie.htm — Longstaff, glosario anotado de Laban *Choreographie* (1926): Gesetz der Raumrichtungsakkordik (ley de acordes de dirección espacial), Harmonielehre, Skalen análogas a escalas musicales, Falschposition como "nota falsa... fuera de armonía"
- ✅ https://pmc.ncbi.nlm.nih.gov/articles/PMC6564005/ — Bernardet, Fdili Alaoui, Studd, Bradley, Pasquier & Schiphorst (2019), "Assessing the reliability of the Laban Movement Analysis system", PLoS ONE 14(6):e0218179 — Krippendorff α 0.473–0.676; Effort 0.46 vs Space 0.66; revisión de McCoubrey y Davis 1987
- ✅ https://inria.hal.science/hal-01663132/file/CHI2017-HAL.pdf — Fdili Alaoui, Françoise, Schiphorst, Studd & Bevilacqua (CHI 2017), "Seeing, Sensing and Recognizing Laban Movement Qualities" — definiciones de factores, tabla BEAs, cues de CMAs (Weight "el más esquivo en video"; jerk→Time; EMG→Weight; expansión/contracción→Space), revisión Eyesweb/EMOTE/EffortDetect, "problema no resuelto"
- ✅ https://artefacts-discovery.researcher.life/full_text_files/DA-2/f3/f3383725c2d233c5bc3b5ed5e4681f30/full_text/u6GDSFXC9VQDX8PXLpA5SqnGJq6tYPrHftND3i7K8AY%3D.pdf — Samadani, Burton, Gorbet & Kulić, "Laban Effort and Shape analysis of affective hand and arm movements" — cuantificaciones Weight (energía cinética/desaceleración), Time (aceleración), Space (producto interno de tangentes), Flow, Shape Directional (curvatura); correlaciones con CMA 81/77/93/67%
- ✅ https://inria.hal.science/hal-02899999 — Garcia & Ronfard (MOCO 2020), "Recognition of Laban Effort Qualities from Hand Motion" — abstract verificado vía HAL/API: features equi-afines discriminantes, HMMs por qualities vs. por action verbs
- ✅ https://www.mdpi.com/2076-0752-15/7/157 — Ek, Visi & Froneman (2026), "Real-Time Detection of Laban Effort Factors in Music Performance Using Machine Learning", Arts 15(7):157 — Effort + Effort Phrasing anotados por experta y usados como training data para regresión en tiempo real (texto completo capturado vía browser)
- ✅ https://andreasaristidou.com/publications/papers/Emotion_Recognition_for_Exergames.pdf — Aristidou et al., "Emotion Recognition for Exergames using Laban Movement Analysis" — Effort como impulso interno (framing de Laban), features de aceleración/jerk/velocidad
- ✅ https://dl.acm.org/doi/10.1145/3473041 — Kim, Neff & Lee (2022), "The Perceptual Consistency and Association of the LMA Effort Elements", ACM TAP 19(1) — consistencia perceptual imperfecta; Light el peor; co-ocurrencia indirect↔free, light↔free
- ✅ https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.00572/full — Tsachor & Shafir (2019), "How Shall I Count the Ways?...", Frontiers in Psychology 10:572 — método de cuantificación de variables LMA (motifs, prevalencia) para análisis estadístico
- ✅ https://pmc.ncbi.nlm.nih.gov/articles/PMC5005399/ — Broughton & Davidson (2016), "An Expressive Bodily Movement Repertoire for Marimba Performance...", Frontiers in Psychology 7:1211 — Effort-Shape analysis por observadores expertos de performance musical
- ✅ https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.01201/full — Broughton et al. (2014), "Action and familiarity effects on ... Laban effort-shape analyses ...", Frontiers in Psychology 5:1201 — expertise-dependencia de la observación Effort-Shape
- ✅ https://pubmed.ncbi.nlm.nih.gov/8888304/ — Dittrich, Troscianko, Lea & Morgan (1996), "Perception of emotion from dynamic point-light displays represented in dance", Perception 25 — 63% reconocimiento desde point-light (abstract recuperado vía EuropePMC REST API)
- ✅ https://pubmed.ncbi.nlm.nih.gov/11716834/ — Pollick, Paterson, Bruderlin & Sanford (2001), "Perceiving affect from arm movement", Cognition 82 — dimensión de activación correlacionada con cinemática; pleasantness en relaciones de fase (abstract recuperado vía EuropePMC REST API)
- ✅ https://www.sciencedirect.com/science/article/abs/pii/S1071581903000508 — Camurri, Lagerlöf & Volpe (2003), "Recognizing emotion from dance movement...", IJHCS 59 — comparación espectadores vs. técnicas automáticas (abstract)
- ✅ https://openaccess.city.ac.uk/id/eprint/4467/5/towards_a_sensorimotor_Calvo-Merino_et_al_2008_CC_AuthorCopy.pdf — Calvo-Merino, Jola, Glaser & Haggard (2008), "Towards a sensorimotor aesthetics of performing art", Consciousness and Cognition 17:911–922 — fMRI, corteza premotora derecha y respuesta estética a danza (manuscrito aceptado)
- ✅ https://openaccess.city.ac.uk/id/eprint/4521/ — Christensen & Calvo-Merino (2013), "Dance as a Subject for Empirical Aesthetics", PsychAesthCA 7(1):76–88 (registro + abstract)
- 📊 https://academiccommons.columbia.edu/doi/10.7916/gsaw-ee85/download — Merolla (2020), "Rudolf von Laban's Sacred Geometry: An Exploration of Harmonic Movement" (tesis, Barnard College) — citas de *Choreutics* sobre escalas/órdenes de tensiones balanceadas; analogía contrapunto Bach; caveat "Laban no leía música"
- 📊 https://chorosjournal.com/docs/choros5/2_CHOROS_05_KIKI_SELIONI.pdf — Selioni, "Laban–Aristotle: Movement for Actors and in Acting", Choros International Dance Journal 5 — "effort rhythms... resultado de su actitud interna"; citas de *The Mastery of Movement* ("man moves in order to satisfy a need")
- ✅ https://www.dancenotation.org/labanotation-fundamentals/ — Dance Notation Bureau: estructura del pentagrama Labanotation (columnas=partes del cuerpo, forma=dirección, sombreado=nivel, longitud=duración, compases alineados a la música)
- 📊 https://papers.cumincad.org/data/works/att/lasg_whitepapers_2016_092.pdf — Burton (Living Architecture Systems Group white paper, 2016), "The Value and Use of Laban Movement Analysis in Observation and Generation of Affective Movement" — "Effort describe la actitud interna hacia el uso de energía"; Bartenieff y Effort/Shape como sistema completo
- ✅ https://www.jstor.org/stable/3333410 — Brooks, "Harmony in Space: A Perspective on the Work of Rudolf Laban", The Journal of Aesthetic Education 27(2):29–41, 1993 (registro bibliográfico; texto tras paywall)
- ✅ https://philpapers.org/rec/LABTMO — registro de Laban & Ullmann, *The Mastery of Movement* (libro fuente del framing de effort como actitud interna)
- ✅ https://www.amazon.se/-/en/Carol-Lynne-Moore/dp/0773447776 — registro editorial de Moore, *The Harmonic Structure of Movement, Music, and Dance According to Rudolf Laban* (Edwin Mellen Press, 2009)
- ✅ https://link.springer.com/article/10.1186/s13640-017-0202-5 — EURASIP JIVP (2017), "Laban movement analysis and hidden Markov models for dynamic 3D gesture recognition" — >92% reconocimiento con features LMA+HMM
- ⚠️ https://arxiv.org/html/2504.21154v1 — Turab et al. (preprint 2025), "Emotion Recognition in Contemporary Dance Performances Using Laban Movement Analysis" — 96.85%, keypoints 3D + XAI
- ⚠️ https://arxiv.org/html/2504.21166v1 — Turab et al. (preprint 2025), "Dance Style Recognition Using Laban Movement Analysis"
- ✅ https://arxiv.org/html/2006.06071v1 — Samadani et al., "Affective Movement Generation using Laban Effort and Shape and HMM-based Data Representation" — 72% reconocimiento de emoción en movimiento generado
- ✅ https://pmc.ncbi.nlm.nih.gov/articles/PMC11548666/ — Kim, Vette, Ottes & Wahl (2024), "Bridging Biomechanics and Laban Movement Analysis", Sensors — integración LMA-biomecánica (golf swing)
- ✅ https://www.tandfonline.com/doi/full/10.1080/19443927.2023.2184854 — Chambers-Coe (2023), "Exploring Rudolf Laban's flow effort: new parameters of touch", Theatre, Dance and Performance Training (metadatos verificados vía Crossref; texto tras botwall)
- 📰 https://www.theatrefolk.com/blog/laban-movement-the-eight-efforts — Espeland, "Laban Movement: The Eight Efforts" (divulgación para teatro; usos de los 8 efforts en entrenamiento actoral)
- 📊 https://saralaoui.com/2015/03/effortmodeling/ — Fdili Alaoui, "Modeling Laban Effort qualities" (página de autora con resumen de su línea de trabajo)

**Fuentes citadas por referencia secundaria (no recuperadas directamente en esta corrida):** Laban & Lawrence, *Effort* (1947/1974, MacDonald & Evans / Princeton Book) ✅-biblio; Laban & Ullmann, *The Mastery of Movement* (1960/1971) ✅-biblio (registro philpapers); Bartenieff & Lewis, *Body Movement: Coping with the Environment* (1980) ✅-biblio (vía referencias de Wikipedia/Longstaff); Hackney, *Making Connections* (1998) ✅-biblio; Dell, *A Primer for Movement Description* (1975) y *Space Harmony* (1977) ✅-biblio; Davis (1987) "Steps to achieving observer agreement: the LIMS reliability project" ✅-biblio (vía Bernardet et al.); Chi et al., "The EMOTE model for effort and shape" (SIGGRAPH 2000) ✅-biblio (vía Wikipedia LMA ref. 11 y CHI 2017 ref. 7); Bouchard & Badler (IVA 2007) ✅-biblio (vía CHI 2017); Mentis et al. (Kinect Effort→eventos musicales) ✅-biblio (vía CHI 2017); Pietrowicz et al. y Maranan et al. "EffortDetect" (acelerómetro único) ✅-biblio (vía CHI 2017); Camurri et al., "Multimodal analysis of expressive gesture in music and dance performances" (2004, Eyesweb) ✅-biblio (vía CHI 2017 ref. 6).
