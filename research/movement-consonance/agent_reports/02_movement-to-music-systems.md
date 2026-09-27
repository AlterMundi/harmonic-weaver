---
project: harmonic-weaver
title: 'Sistemas movimiento→música: estado del arte y teoría de mapeos'
type: research-report
tags: [research, movement-consonance, mapping, NIME, dance-sonification, EyesWeb, theremin-problem, hyperinstruments, kinect, mediapipe, harmonic-weaver]
date: 2026-09-24
confidence: medium-high
---

# 02 — Sistemas movimiento→música: estado del arte y teoría de mapeos

> Carril R2 del pack movement-consonance. Pregunta central: ¿qué dice la
> literatura (NIME/ICMC/Computer Music Journal, 1983-2026) sobre sistemas que
> traducen movimiento corporal en música, y qué predice para el nuevo modo
> "consonancia del movimiento" de harmonic-weaver (cualidad de movimiento →
> detuning de armónicos de la serie)?
>
> Leyenda de confianza (idéntica al MANIFEST): ✅ primaria/peer-reviewed/docs
> oficiales · 📊 secundaria especializada · 📰 prensa/blog · ⚠️ contestado ·
> ❓ inferencia del agente a verificar. Las citas numéricas `[n]` remiten a
> `## Sources` al final.
>
> Alcance: la psicoacústica de detuning/consonancia (Sethares, Plomp-Levelt,
> cents, umbrales de segregación, snap) está cubierta en el reporte hermano
> `04_continuous-pitch-expression.md` — aquí NO se duplica; sólo se referencia.
> LMA en profundidad: `01_laban-movement-analysis.md`. Matemática del modo:
> `03_movement-consonance-math.md`.

## 0. TL;DR

1. **El mapeo posición→teclado-virtual que usa hoy el beacon es el "one-to-one" canónico, y la literatura lo trata como piso, no como techo**: Hunt–Wanderley–Kirk (ICMC 2000) midieron en >4000 tests que los mapeos *complejos* (many-to-many con derivadas del gesto) dan mejor performance en tareas difíciles **y** mejora sostenida en el tiempo, mientras los 1:1 se estancan y se viven como "confusing, frustrating" [1]✅. Su recomendación textual: usar cross-coupling + *derivadas del input relacionadas con la energía del performer* en la próxima generación de instrumentos [1]✅ — exactamente la tesis del modo consonancia.
2. **Existe prior art directo de danza→pitch y su fracaso documentado**: OtoKin (Dahlstedt & Skånberg Dahlstedt, NIME 2019) constata que el pitch continuo desde movimiento cae en **"glissando hell"** y lo reemplaza por intervalos discretos derivados de *postura* de brazos (seis comparaciones de coordenadas, suma aditiva sobre fundamental fija, actualización sólo cuando la aceleración cruza un umbral) [5]✅. Es el antecedente más cercano al modo consonancia y valida sus dos decisiones de anclaje: serie fija + modulación por energía.
3. **La línea EyesWeb (Camurri et al., Computer Music Journal 2000 → InfoMus hoy) demuestra que los descriptores de cualidad de movimiento — Quantity of Motion, Contraction Index, fluidity (inverso de la integral del jerk), impulsiveness — son computables en tiempo real desde video y controlan rendering musical expresivo con correlato perceptual validado** [8][9][10][11]✅. HarMoCAP ya emite features de esta familia (`qom`, `smoothness`, proxies Laban): el beacon trabaja sobre infraestructura conceptual validada por 25 años de investigación.
4. **El "problema theremin" también aplica a thereministas humanos**: Ward et al. (NIME 2008) usan Laban Movement Analysis sobre video de dos thereministas y muestran que la fase de **Recuperation** del effort-phrasing (recuperar tras la Exertion) es esencial para una ejecución satisfactoria; proponen que el diseño de DMIs parta del *movimiento del ejecutante*, no del controlador [12]✅. Para un sistema sin tacto como el beacon, la referencia de control debe venir del cuerpo entero + el oído (loop propioceptivo-auditivo), no de referencias externas.
5. **Criterios de diseño instrumentales consolidados (Wessel & Wright)**: "low entry fee with no ceiling on virtuosity" (fácil de empezar, techo infinito — las interfaces simples "parecen de juguete tras un uso breve"), **latencia audible ≤ ~10 ms y baja varianza**, y metáforas de control generativas en vez de "un gesto → un evento" [4]✅.
6. **Modos de fallo recurrentes en 40 años de sistemas movimiento→música** (§4): latencia/varianza [4][14]✅; glissando hell del pitch continuo [5]✅; opacidad del mapeo cuando el performer no puede predecir el resultado [1][3]✅; sobrecarga cognitiva del bailarín que debe pensar consecuencias sonoras mientras baila [13]📊; falta de repetibilidad en mapeos generativos/aleatorios [5]✅; fragilidad del éxito escénico ligada a la robustez del sistema [13]📊; y el "toy-like character" de los 1:1 simples [4]✅.
7. **La generación 2019-2026 (depth cameras, MediaPipe/YOLO-pose, ML) repite el péndulo 1:1→cualidad**: Kinect 2011-2012 hacía posición→MIDI [14]✅; Con Moto (NIME 2026) — cámara de profundidad 30 fps + pose estimation 3D CUDA + features cinemáticas (posición, velocidad de limbs, proximidad) piloteando un transformer MIDI — muestra experimentalmente que **el nivel de abstracción del mapeo configura la agencia**: control fino de una voz = "instrumento tocable"; mapeo abstracto a energía de género = "partner creativo autónomo" [15]✅.
8. ❓ (inferencia de diseño, desarrollo en §5): para harmonic-weaver el mapeo consonancia→detuning debe ser (i) *energético* (derivadas del gesto: aceleración, frenado, iniciativa — no posición), (ii) *repetible* (mismo movimiento → mismo detuning; matriz fija como en OtoKin), (iii) *anclado* (la serie armónica actúa de "detente cognitivo" que evita glissando hell — convergencia con [4-report]✅ sobre snap), y (iv) con curva de aprendizaje sin techo (low entry fee / no ceiling [4]✅). La literatura predice que este punto del espacio de diseño está poco explorado: calidad-de-movimiento→*afinación* casi no existe como mapeo publicado.

---

## 1. Taxonomía y teoría del mapeo

### 1.1 La taxonomía canónica (Hunt–Wanderley–Kirk / Rovan et al.)

Texto de referencia: Hunt, Wanderley & Kirk, *"Towards a Model for Instrumental Mapping in Expert Musical Interaction"* (ICMC 2000; York Music Technology Group + IRCAM) [1]✅. Definiciones textuales:

- **Mapping** = "la liaison o correspondencia entre *control parameters* (derivados de acciones del performer) y *sound synthesis parameters*" [1]✅. Excluye explícitamente pre-procesamiento (segmentación, scaling, limiting) [1]✅.
- **Estrategias básicas**: considerando dos conjuntos de parámetros — **one-to-one**, **one-to-many**, **many-to-one**; su combinación es **many-to-many** [1]✅.
- Los términos **convergent** (many-to-one) y **divergent** (one-to-many) vienen de Rovan, Wanderley, Dubnov & Depalle 1997, *"Instrumental Gestural Mapping Strategies as Expressivity Determinants in Computer Music Performance"* [1][7]✅. En NIME posterior, **"complex mapping"** pasó a designar el many-to-many con cross-coupling [1][5]✅. El brief llama "complex" a esta cuarta categoría; la fuente primaria la describe como combinación de las tres básicas [1]✅.
- **Modelo de dos capas** (ESCHER, Wanderley–Schnell–Rovan 1998): dividir el mapping en (a) gesto → *capa de parámetros abstractos* (perceptuales o definidos por el compositor) y (b) abstractos → variables de síntesis. Así el mismo controlador puede pilotear síntesis distintas y viceversa cambiando una sola capa [1]✅. Garnett & Goudeseune extienden con generación automática de espacios perceptuales ("timbre rover") [1]✅.
- Antecedentes de la taxonomía: Ryan 1991 (analogías euclídeas punto/línea/curva, STEIM) [1]✅; Bowler et al. 1990 (mapear N articulaciones a M parámetros por interpolación, para síntesis aditiva en tiempo real — ¡relevante directo para el shaper aditivo del beacon!) [1]✅; Choi et al. 1995 (manifold interface: control space → phase space por celdas) [1]✅.
- Organología de DMIs: Paine (NIME 2010, encuesta TIEM) propone clasificar interfaces por sensado/gesto/mapping en vez del esquema Hornbostel-Sachs; Birnbaum et al. usan 7 ejes (rol del sonido, expertise requerida, control musical, grados de libertad, modalidades de feedback...) [31]✅.

### 1.2 Por qué los mapeos 1:1 tipo "posición = tecla" se sienten limitados

Evidencia experimental directa (York; Hunt & Kirk 1999, resumida en [1]✅): tres interfaces para recrear señales de audio de dificultad creciente (pitch, volumen, timbre, panning) — mouse-sliders (1:1), sliders físicos (1:1) e interfaz *multiparamétrica* (un único 1:1 para panning; resto many-to-many; **el sonido sólo existe mientras hay movimiento**: volumen ∝ velocidad del mouse):

- En tests complejos la multiparamétrica obtenía scores **mucho más altos**; las 1:1 sólo ganaban en el test más simple [1]✅.
- **Sólo la multiparamétrica mostró mejora sostenida a lo largo de las sesiones** (curva de aprendizaje); las 1:1 se estancaban [1]✅.
- Cualitativo: la 1:1 de sliders resultaba "confusing, frustrating or at odds with their way of thinking" — exigía "descomponer mentalmente el sonido en parámetros" (sobrecarga cognitiva); la multiparamétrica resultaba "fun" y la gente quería seguir usándola fuera del test [1]✅.
- Conclusión textual: "complex mappings (using cross-coupling of input parameters to synthesis parameters, **and derivatives of input parameters related to the performer's energy**) be utilised widely in the next generation of electronic performance instruments" [1]✅.
- Complemento: Rovan et al. 1997 mostraron que para el mismo controlador y la misma síntesis, **la estrategia de mapeo es determinante de la expresividad** (ej. biasing tipo embouchure de clarinete en síntesis física) [1][2]✅. Wanderley 2001 añade el criterio sensor→parámetro: un sensor preciso pero inexacto puede servir para loudness pero su inexactitud se notará si pilotea pitch [2]✅ — criterio para decidir qué feature de HarMoCAP puede pilotear afinación.

Corolario para el beacon ❓: un pad/band donde la posición de muñeca selecciona un armónico es 1:1 (o divergente si una zona dispara varios parámetros): predecible, de entrada baja, pero con techo bajo — la literatura predice estancamiento y "toy-like character" [4]✅ tras la novedad.

### 1.3 Criterios de diseño instrumental

De Wessel & Wright [4]✅ (paper CNMAT; demo gemela NIME 2002 [16]✅):

- **"Low entry fee with no ceiling on virtuosity"**: los instrumentos acústicos "no son fáciles al principio pero permiten desarrollar alta musicalidad"; muchas interfaces simples de computadora "tras un uso breve tienen un carácter de juguete y no invitan a seguir" [4]✅.
- **Latencia**: "colocamos el límite superior aceptable de la reacción audible de la computadora al gesto en 10 milisegundos" [4]✅; y la **varianza** de la latencia importa tanto como su valor medio ("reactive low latency variance systems" como condición de control intimacy) [4]✅.
- **Metáforas de control**: contra el paradigma "one gesture → one acoustic event", "driving o flying en un espacio de procesos musicales" — el gesto pilotea procesos generativos que evolucionan en el tiempo [4]✅.
- Programación **clara y simple** de la relación gesto→resultado como criterio explícito de diseño [4][16]✅.

De Hunt–Wanderley–Kirk [1]✅:

- **Nivel del usuario**: principiantes se benefician de mapeos simples/directos; músicos expertos aprovechan los complejos [1]✅. → El snap configurable y los "modos" del beacon deberían poder graduarse por performer.
- **Continuo macro↔micro**: el mapeo define el nivel de interacción, de fraseo/ritmo (macroscópico) a control fino de timbre (microscópico) [1]✅.
- **Energía física como parte del mapeo**: el sistema debe requerir gasto energético para sonar; eso ancla la agencia [1]✅. OtoKin lo formula como ideal de diseño: "el sonido de salida debería ser de alguna manera proporcional a la cantidad de movimiento, momentum o aceleración... el sistema debería estar en silencio cuando estás quieto", pero aclara: un enfoque sólo de *motion* pierde la **energía potencial** (también es effort) y no permite "high-energy still states" [5]✅ — matiz importante para la definición de consonancia del beacon (un cuerpo quieto-pero-tenso).
- **Diseño del mapeo como proceso creativo**: West–Caramiaux–Wanderley (NIME 2020) observan a 12 diseñadores NIME creando mappings T-Stick→sinte: alternan "difuse exploration" y "directed experimentation", deciden por intuición inmediata y abandonan lo que no funciona al instante [32]✅. Implicación: el modo consonancia necesita una consola/herramienta de re-mapeo en vivo para ser explorado artísticamente, no sólo un mapping hardcodeado ❓.

Sobre la terminología del brief: la frase "the problem of the opaque interface" **no aparece** en los textos de Hunt/Wanderley que pudimos fetchear [1][2][3]⚠️. Lo que sí está documentado con evidencia: (a) mappings por redes neuronales/genéricos se discuten como no-explicit y por tanto menos diseñables [1]✅; (b) la usabilidad colapsa cuando el performer no puede descomponer/predecir el resultado (§1.2) [1]✅; (c) Bergsland & Wechsler (citados en [5]✅) desplazan el criterio: "lo importante no es si el mapping es simple, complejo, 1:1 o many-to-many, sino **cómo el entorno evoluciona en el tiempo: cómo se guía al usuario entre procesos 'causal-ordered-predictable' y 'intuitive-improvised'**; cualquiera de los dos en exclusión del otro pierde interés rápidamente" [5]✅. Tratar "opaque interface" como paráfrasis del problema de impredecibilidad, no como cita textual.

### 1.4 Descriptores gestuales vs sónicos

- El framing corresponde al modelo de dos capas (§1.1): la capa intermedia idealmente usa **parámetros perceptuales** (timbre space de Wessel 1979; triángulo vocálico de formantes) en vez de frecuencias/amplitudes/fases de parciales sueltas [1]✅. El beacon ya tiene su "capa abstracta" natural: los descriptores de cualidad de HarMoCAP (`qom`, `smoothness`, proxies Laban) son descriptores *gestuales*; los armónicos de la serie con su detuning son descriptores *sónicos* perceptualmente anclados (consonancia/rugosidad) — una instancia limpia del modelo ESCHER ❓.
- **Motion vs gesture**: Schacher (NIME 2010) distingue *motion* (trayectoria medible) de *gesture* (unidad percibida con intención expresiva) y sostiene que el mapeo debe operar sobre gestos de alto nivel; su sistema combina visión computacional (contorno corporal por hull Voronoi/Delaunay → 5 puntos cardinales + centroide → velocidad, aceleración, body span, contracción/expansión) con wearables (pulseras 5-DOF: acelerómetro+giroscopio a >100 Hz por extremidad) para obtener "higher-level expressive gestures"; la bailarina asume rol de **instrumentista Y directora** sobre una composición modular no-lineal [3]✅.
- **Invariantes perceptuales**: Giomi & Leonard (NIME 2020) buscan "action-based perceptual invariants" que relacionen *gesture qualities* con *sound features* mediante síntesis físicamente basada (masa-interacción): el movimiento no dispara samples, **excita modelos físicos** — marco de 3 niveles donde los dos primeros reflejan propiedades objetivas de sonido y movimiento [6]✅.

---

## 2. Sistemas concretos (sensor → mapeo → salida → uso escénico)

### 2.1 Very Nervous System — David Rokeby (1983→1990s)

- **Sensor**: cámara de video + procesamiento de imagen (activación de celdas por diferencia de frames); nada en el cuerpo [17]✅.
- **Mapeo**: el espacio se segmenta en celdas/regiones; el movimiento en cada región dispara o transfiere entre capas de procesos sonoros generativos. Rokeby lo diseñó contra los sesgos de la computadora: "porque la computadora es puramente lógica, el lenguaje de interacción debe aspirar a ser intuitivo; porque la computadora te remueve de tu cuerpo, [la interacción] debe reencarnarte" [17]✅.
- **Salida**: paisajes sonoros generativos (síntesis + sampling).
- **Uso**: instalación en galerías, espacios públicos y performances; PetroCanada Media Arts Award 1988; Prix Ars Electronica Award of Distinction 1991; derivó en el software **softVNS** usado por decenas de artistas; Winkler documenta su uso para danza interactiva [17][18]✅.
- **Teoría propia ("The Harmonics of Interaction", MusicWorks 1990)** [19]✅: la instalación y la persona forman un **feedback loop** cuyo delay mínimo es ~1/30 s; como el feedback acústico de una sala, el loop "refuerza aspectos particulares del sistema y de la persona, produciendo resonancias — los **armónicos de la interacción**, únicos para cada combinación instalación/individuo" [19]✅. Dos observaciones que valen oro para el beacon: (1) "había un sonido que sólo podías encontrar si caminabas como si cargaras 40 libras de peso" — **calidad de movimiento descubre contenidos sonoros** [19]✅; (2) la prueba que la gente le hace al sistema es "si hago el mismo movimiento dos veces, ¿obtengo el mismo sonido?" — la **repetibilidad es el primer test de controlabilidad** que aplican los interactores, y aun en piezas determinísticas la gente "casi invariablemente obtiene un sonido distinto al cuarto gesto" porque cambia su actitud corporal [19]✅.
- **Legado**: ancestro directo del beacon en el árbol "cámara → sonido generativo espacial" ❓; y nombre profético: el beacon mapea consonancia a *armónicos* de una serie, Rokeby llama *armónicos* a las resonancias del loop cuerpo-sistema [19]✅❓.

### 2.2 Hyperinstruments — Tod Machover, MIT Media Lab (1986→)

- **Concepto** (página oficial del autor [20]✅; Wikipedia/Tod Machover [21]📊): instrumentos "hiper"-extendidos — sistemas de sensores + señal + software que miden e interpretan la expresión del ejecutante y expanden el instrumento acústico/eléctrico (guitarras, teclados, percusión, cuerdas, dirección orquestal). Lanzados en el MIT Media Lab en 1986 [20]✅; usados por Yo-Yo Ma, LA Philharmonic, Peter Gabriel, Penn & Teller [21]📊.
- **Trayectoria**: del virtuosismo experto (hypercello, viola hiper) a instrumentos para no-profesionales (desde 1992: "Drum-Boy", "Joystick Music"; **Brain Opera** 1996 — hyperinstruments para que cualquiera toque, instalado en la House of Music de Viena desde 2000) [21]📊.
- **Mapeo**: sensores de ejecución (arco, presión, señal acústica, gestos) → expansión expresiva del instrumento; la filosofía declarada es "medir e interpretar la expresión y el sentimiento humanos" [21]📊.
- **Relevancia beacon**: prueba histórica de que la *instrumentalidad* se logra **extendiendo** un instrumento existente (allí el cello; aquí el cuerpo) con capas de interpretación, no sustituyéndolo por un teclado ❓. Nota: hyperinstruments.org no fue fetcheable (bloqueo de red interna del extractor); se cita la página de Machover en media.mit.edu [20]✅ y material secundario [21]📊.

### 2.3 Lady's Glove — Laetitia Sonami (1991→, cinco generaciones)

- **Sensor** (auto-documentado en su sitio) [22]✅: glove #1 (1991, Ars Electronica con Paul DeMarinis): guantes de goma de cocina con 5 transductores Hall en las puntas de los dedos. Glove #3 (lycra dorada): tiras resistivas (bend sensors extraídos del Mattel Power Glove) a lo largo de dedos y muñeca con tap central → **dos streams de datos por tira**; pad de presión en el índice; **transmisor ultrasónico en la palma + receptores en brazo derecho y pie izquierdo** (distancia entre manos, altura de la mano sobre el suelo — "interpretar los gestos de modo distinto según la distancia de la mano al cuerpo y al suelo"); todo vía **STEIM Sensorlab**. Gloves #4-5 (construidos por Bert Bongers, patrocinio STEIM, 1994 y ~2001): + switch de mercurio, acelerómetro de velocidad de mano; #5 añade dos acelerómetros en banda de muñeca, más Halls, sensor de luz, switches extra, LEDs, micrófono miniatura.
- **Mapeo**: señales → Sensorlab → Max/MSP; **el mapeo y el material sonoro cambian en cada composición**; controla sonido y a veces motores, luces, video (Jitter) [22]✅.
- **Uso**: performance en vivo durante 30+ años; "ha devenido un instrumento fino que desafía las nociones de tecnología y virtuosismo" [22]✅.
- **Lecciones**: (a) el instrumento es la pareja hardware+mapeo, no el hardware [22]✅; (b) notable que una artista sostenga 30 años de repertorio con control *propioceptivo-táctil* (el guante se siente) — el beacon no ofrece esa vía y debe compensar con anclajes perceptuales (serie armónica, snap) ❓.

### 2.4 The Hands — Michel Waisvisz / STEIM (1984)

- **Sensor** (HCI Museum + CMJ 2016) [23]📊: par de controladores MIDI worn sobre marcos de madera: switches, potenciómetros, **tilt sensors y rangefinders ultrasónicos**; manos/brazos/inclinación → MIDI, un año después del estándar (1983). Evolucionó en varias iteraciones y originó el STEIM **SensorLab** (1989) [23]📊.
- **Filosofía**: alternativa física directa al paradigma teclado-mouse; Waisvisz: "el tacto es crucial para comunicarse con las nuevas tecnologías electrónicas de performance" [23]📊.
- **Uso**: innumerables performances y colaboraciones (Laurie Anderson, Steve Lacy, Peter Brötzmann); documentado en Torre, Andersen & Baldé, *Computer Music Journal* 2016, "The Hands: The Making of a Digital Musical Instrument" [23]📊; archivo fotográfico/video en crackle.org [23]📊.
- **Lección**: aun **con** referencia táctil (el marco se toca y se siente), el virtuosismo de Waisvisz fue posible pero *personal e idiosincrático* — décadas de práctica corporal [23]📊❓. Los sistemas sin tacto heredan el problema amplificado (ver §4.2).

### 2.5 EyesWeb — Camurri, Hashimoto, Ricchetti, Ricci, Suzuki, Trocca, Volpe (Computer Music Journal 2000; InfoMus Genova)

- **Sistema**: plataforma modular abierta para análisis de movimiento y gesto en tiempo real desde video, "con foco particular en el entendimiento del afecto y el contenido expresivo del gesto" [8]✅ (CMJ 24(1):57-69, DOI 10.1162/014892600559182; 246 citas según Semantic Scholar [8]✅).
- **Descriptores expresivos** (documentados en la librería sucesora "Analysis of Expressive Gesture: The EyesWeb Expressive Gesture Processing Library" [9]✅): features extraídas en varios niveles, "de la cinemática de un single joint a features expresivas globales inspiradas en psicología y teorías humanísticas: **contraction index, fluidity, impulsiveness**"; capa de abstracción por dictionary learning → SVM para reconocimiento de emoción en tiempo real; input de Qualisys óptico o Kinect/Kinect2 [9]✅. Raíz conceptual explícita en Laban (& Lawrence, *Effort*) [9]✅.
- **Mapeo musical documentado** (Castellano–Bresin–Camurri–Volpe, NIME 2007) [10]✅: full-body desde video → **QoM** (Quantity of Motion, "correlacionada con la energía del usuario") y **CI** (Contraction Index, "espacio ocupado por el usuario") → **tempo y sound level** del rendering expresivo (motor pDM): "la performance se vuelve más rápida con movimientos más rápidos (QoM alto) y más fuerte cuando el usuario expande su cuerpo (CI bajo)"; **articulación** legato↔staccato según emoción detectada de baja/alta energía; + feedback visual (color de la silueta proyectada) [10]✅.
- **Herramienta derivada**: **modosc** (Visi & Dahl, NIME 2018) [11]✅: librería Max/odot+OSC de descriptores de movimiento en tiempo real — velocity/acceleration/jerk (diferenciadores IIR de Skogstad para reducir ruido), **Fluidity Index = inverso de la integral del jerk** (Flash & Hogan; Piana et al.), QoM, centroid/center-of-mass, descriptores de grupo; caso de uso de sonic interaction design con ML [11]✅.
- **Relevancia beacon**: es prácticamente un gemelo académico del feature-set de HarMoCAP (`qom`, `smoothness` ≈ fluidity, `contraction`/`expansion` ≈ CI) [11]✅. Valida que cualidad→parámetro musical tiene correlato perceptual estudiado (dataset de bailarines profesionales anotado por expertos: la sincronización intra-personal distingue rigidity/fluidity/impulsivity [9]✅), y da fórmulas estandarizadas para la capa de "consonancia" ❓.

### 2.6 Kinect-era (2011-2013): el pico del "posición = tecla"

- **Yoo, Beak & Lee (NIME 2011), "Creating Musical Expression using Kinect"** [14]✅: skeleton data (posición Y velocidad de cada joint) → **conversor Kinect-a-MIDI** (tabla predefinida) → Max/MSP y un generador de adlib. Mapeo notable por cualidad: la "tensión" de la pose — distancia relativa de 5 end-joints (cabeza, puntas de dedos, pies) respecto a una pose normal — selecciona la **escala** del adlib: pose contraída → escala disminuida; cuanto más separados los joints, escalas "más tensas" [14]✅. Raro caso Kinect de cualidad-de-postura→cualidad-armónica.
- **Crossole (NIME 2012)**: interfaz gestual para composición/improvisación con Kinect [24]✅ (índice NIME). **Non-invasive sensing para percusión hiper con Kinect (NIME 2012)** [25]✅. **Motion and Synchronization Analysis of Musical Ensembles with the Kinect (NIME 2013)** [26]✅.
- **Dance Jockey + Xsens MVN (NIME 2012)**, **LoopJam (NIME 2012: la pista de baile como mapa instrumental colaborativo)**, **Sensemble (NIME 2006: sensores inalámbricos multiusuario para danza)** [27]✅ (localizados en índice NIME).
- Patrón: la mayoría usó posición→nota/evento (1:1 o divergente); los que dejaron huella artística introdujeron cualidad (tensión de pose, energía) [14]✅❓.

### 2.7 Generación pose-estimation / ML (2019-2026)

- **OtoKin (Dahlstedt & Skånberg Dahlstedt, NIME 2019)** [5]✅: Kinect v2 (25 joints, 30 fps) → vvvv → Nord Modular G2 (DSP sample-by-sample, latencia mínima; feedback como elemento de diseño). El escenario se subdivide en sub-espacios 3D → crossfade entre *sound engines*; propiedades centrales: **posición** (crossfading + "paredes" con campana de aviso, zona silenciosa cerca del piso, "cielo" con motor especial), **postura** (mecanismo aditivo de pitch, §1.2 de este TL;DR), **esfuerzo/aceleración** (volumen y filtros), **toque entre cuerpos** (motor *Together*, detección confiable de contacto parte-con-parte). Mapeo de timbre: matriz many-to-all fija (coeficientes generados aleatoriamente en diseño, rango (-1,1)) que "preserva el contorno y magnitud gestual pero modula todos los parámetros de modo acoplado... no es aleatorio en ejecución: es **repetible**, y direcciones o posturas interesantes pueden explorarse" [5]✅. Usado en performances, workshops e instalaciones, incl. pieza noh-teatral con masks [5]✅.
- **Vrengt (Erdem, Schia, Jensenius — NIME 2019)** [28]✅: instrumento *compartido* músico-bailarina; dos Myo armbands (EMG) en brazo y pierna de la bailarina + micrófono de respiración; diseño participativo usando **sonificación como herramienta de exploración** del cuerpo ("matriz espacio-temporal", foco en micro-interacción sónica); explora la frontera standstill↔motion / silence↔sound.
- **Joakinator (NIME 2023)** [29]✅: wearable (sEMG + sensores de fuerza) + ML → sonificación de **tono muscular y fuerza**; investiga alterar la percepción corporal (proyecto ERC BODYinTRANSIT). Cualidad fisiológica → sonido, no posición.
- **Body Fragmented (Kirby, Frontiers in Computer Science 2025)** [30]✅: pose estimation (clase MediaPipe) → notación basada en movimiento para composición instrumental; pregunta guía "what does that movement express and how could that sound"; proceso no-lineal compositor-performer. Es pose→*partitura*, no pose→sonido en tiempo real.
- **Con Moto (Chen, Lei, Huang — NIME 2026)** [15]✅: cámara de profundidad estereoscópica 30 fps → motion capture → **pose estimation 3D humana acelerada por CUDA** → análisis de movimiento → features cinemáticas (posición de bailarín, velocidad de limbs, proximidad) → steering en inferencia de transformer MIDI en tiempo real (pitch range, instrumento, género vía token steering; timbre/velocity/articulación vía MIDI CC) → Max/MSP + Ableton Live → 8 canales espacializados. Hallazgo central: **agencia configurable por nivel de abstracción del mapeo** — control fino de una voz individual = sistema como "instrumento tocable"; mapeo abstracto a energía de género = sistema como "partner creativo autónomo" [15]✅. Contexto que cita: sistemas RAVE+IMU y autoencoders video→audio son reactivos pero "carecen de complejidad estructural"; los diffusion-models ricos corren offline por latencia [15]✅.
- **Human-in-the-Loop (NIME 2026)**: alineamiento crossmodal IA entre espacios latentes de movimiento y audio para sonificación expresiva [33]✅ (índice NIME). **From Improvised Movement to Musical Improvisation (NIME 2026)**: ML para instrumentos personalizados desde movimiento improvisado [34]✅ (índice NIME). **Role-Separated Live Movement Sonification (NIME 2026)**: toolkits como mediadores de agencia distribuida [35]✅ (índice NIME).

### 2.8 Intermedia de danza: Palindrome, Troika Ranch, Digital Dance Project

(Revisión de casos en Senturk 2011 [13]📊 + Rovan–Wechsler–Weiß [18]✅.)

- **Palindrome Dance Company** (Robert Wechsler, desde 1974 con "cajas" fotosensibles; computadoras desde 1995 con Frieder Weiß): sistema **EyeCon** — "video-based motion sensing system which allows performers to generate or control music and projected images through their movements and gestures in space" [13][18]📊✅.
- **Seine hohle Form** (Rovan/Wechsler/Weiß, Crossings 1997) [18]✅: caso de estudio de mapeo danza→síntesis en tiempo real; el proceso arranca identificando los **"decisive parameters"** de la danza en cada escena; prioriza la **correlación perceptual** del mapeo "a través de niveles variables de abstracción"; documenta el ida-y-vuelta compositor-coreógrafo (la coreografía puede rediseñarse para lograr frases musicales) y la "notable falta de comunicación entre los dos campos" como límite expresivo [18]✅.
- **Troika Ranch** (Mark Coniglio & Dawn Stoppiello, 1994): desarrollan **Isadora**, software de performance en vivo donde la imagen de los bailarines controla audio y video; manifiesto de Coniglio: la música grabada "thwarts" al bailarín — si sostiene un balance espectacular, "la música corre adelante y la frase siguiente sufre"; la interactividad libera el tempo de la danza [13]📊.
- **Digital Dance Project** (Wayne Siegel, Aarhus): postura de acompañamiento — "la tarea del compositor era crear software que produjera sonidos para acompañar la coreografía"; la danza narra, la música acompaña [13]📊.
- **MotionComposer** (Wechsler & Bergsland, NIME 2015) [36]✅: dispositivo video+sensor 3D para personas con discapacidad; piezas de danza interactiva para bailarines profesionales; filosofía declarada de **transparencia e intuitividad (causalidad clara)** en la relación interactiva [36]✅.

---

## 3. Sonificación de danza: cualidad de movimiento → sonido

Sistemas donde la **cualidad** (no la posición) pilotea el resultado musical:

1. **EyesWeb / InfoMus (§2.5)**: QoM→tempo, CI→nivel, emoción-detectada→articulación [10]✅; descriptores contraction/fluidity/impulsiveness con validación perceptual sobre bailarines profesionales [9]✅; modosc estandariza las fórmulas (fluidity = 1/∫jerk) [11]✅. Es LA referencia de "effort-like quantities computadas en tiempo real desde video" que pide el brief ✅.
2. **SoniMime (Fox & Carlile, NIME 2005)** [37]✅: dos acelerómetros 3D → Pd → síntesis **tristimulus** de timbre; filtrado en tres bandas (high-pass = jerks/impactos, low-pass = tilt, derivada de tilt = jerk) + detector de inmovilidad → 20 streams OSC. Hallazgo textual: "los mapeos directos de tilt y jerk a parámetros de síntesis resultan **más exitosos que los esquemas de pattern-matching comparativos basados en memoria**"; propiedad emergente: el tristimulus suena como formantes vocálicos controlables [37]✅.
3. **Schacher (NIME 2010) (§1.4)**: gesto de alto nivel (no motion crudo) → composición modular no-lineal; bailarina = instrumentista + directora; herramientas de mapeo con splines y teselación Delaunay/Voronoi sobre los puntos del cuerpo (los pads virtuales del beacon son parientes de esto) [3]✅.
4. **OtoKin (§2.7)**: effort-based mapping como ideal declarado — "moverse en el espacio debería sentirse como tocar un instrumento: un espacio rico de posibilidades, con repetibilidad, aprendibilidad y control íntimo del sonido (tomando el término de David Wessel)"; aceleración→volumen y filtros; corrección: incluir energía potencial (posturas sostenidas, levantar una pierna) porque "un enfoque sólo de movimiento pierde la idea de energía potencial, que también es effort" [5]✅.
5. **Giomi & Leonard (NIME 2020)**: invariantes perceptuales acción-sonido + síntesis físicamente basada (masa-interacción): el gesto *excita un cuerpo resonante virtual*; el conocimiento somático del performer orienta el diseño [6]✅.
6. **Thereministas + LMA (Ward et al., NIME 2008)** [12]✅: análisis cualitativo LMA de Lydia Kavina y Clara Rockmore en video: Kavina alterna "Passive Weight + Shape Flow" con "Recuperación activa de un gesto de kinesfera grande con Free Flow"; Rockmore usa plano sagital, Quickness, Direct Focus y Bound Flow/Carving como sello. Tesis: la fase de **Recuperation** del effort-phrasing (cómo se recupera el cuerpo tras la exertion de tocar) es esencial para la performance satisfactoria; el grado de recuperación influye en la tensión musical percibida; diseñar interfaces considerando temprano la interdependencia realización-del-instrumento / meta-musical / habilidad-del-performer [12]✅. Ward & Torre extienden el método a diseño de DMI completo (**Twister**, NIME 2014): analizar movimiento de violinistas y no-input-mixer con LMA, y dejar que "el tipo de movimiento que queremos que el dispositivo engendre" guíe el diseño físico y el mapeo [38]✅.
7. **Sonificación de cualidad → timbre/afinación en la literatura reciente**: Con Moto usa velocidad de limbs y proximidad (features de cualidad) para steering de generación [15]✅; Joakinator sonifica tono muscular/fuerza [29]✅; Vrengt sonifica EMG + respiración [28]✅. **Mapeo directo calidad-de-movimiento→afinación/detuning: no encontramos ninguno publicado** — el hueco que el modo consonancia ocuparía (§5) ❓. Lo más cercano es OtoKin (postura→intervalos discretos) [5]✅ y Yoo et al. (tensión de pose→escala) [14]✅, ambos en el dominio discreto, no continuo como el detuning del beacon.

---

## 4. Modos de fallo documentados

### 4.1 Latencia (y su varianza)
- Wessel & Wright: límite aceptable de reacción audible ~10 ms; la varianza de latencia rompe la "control intimacy" tanto como la latencia alta [4]✅.
- Rokeby: el loop cuerpo-instalación tiene un delay mínimo de ~1/30 s y la percepción del sistema depende de ese loop; aun así la gente entra en resonancia [19]✅.
- Con Moto (2026): "lograr a la vez alta coherencia musical y baja latencia sigue siendo un desafío abierto"; los sistemas diffusion ricos corren offline; MIDI-transformers en tiempo real como compromiso [15]✅.
- OtoKin eligió DSP sample-by-sample (Nord Modular G2) explícitamente por latencia mínima y para poder usar feedback como elemento de diseño [5]✅.
- Para el beacon: HarMoCAP corre YOLO-pose a 30 fps → ~33 ms de base sólo en captura; la literatura dice que la *varianza* (jitter del tracking, frames perdidos) es tan dañina como el valor medio [4]✅. El pipeline completo (cámara→OSC→weaver→shaper→SC binaural) debe auditarse contra estos números ❓.

### 4.2 El problema theremin (control continuo sin referencia táctil)
- Cobertura psicoacústica/háptica completa en `04_continuous-pitch-expression.md` §1.2 (Berdahl, Continuum, Xiao) — no se duplica aquí.
- Aporte específico de este carril: Ward et al. muestran que **ni siquiera los thereministas escapan del problema motor**: la ejecución precisa exige una fase de Recuperation entre esfuerzos, y cada ejecutante desarrolla estilo propio de lograrla [12]✅. Y Waisvisz demuestra el otro extremo: con marco táctil + 20 años de práctica se alcanza virtuosismo, pero personal e intransferible [23]📊.
- Implicación beacon ❓: un detuning continuo piloteado por energía de joints no tiene referencia táctil; sus anclas deben ser (a) la serie armónica fija (el oído sabe dónde "casa" cada armónico), (b) el snap configurable, (c) la propiocepción del movimiento completo (los brazos pesan, se sienten) — y conviene diseñar explícitamente para la Recuperation: que el sistema "perdone" y sostenga sonido en las fases de recuperación del gesto, no sólo en la exertion.

### 4.3 Opacidad / fragilidad / impredecibilidad del mapeo
- 1:1 con descomposición mental de parámetros → "confusing, frustrating"; el performer no puede predecir ni aprender [1]✅.
- Mappings por ML/neural nets: no explícitos, no diseñables directamente (HWK los contrasta con estrategias explícitas) [1]✅.
- Rokeby: la gente testea repetibilidad ("¿mismo movimiento → mismo sonido?") y cuando el sistema responde distinto pierde la sensación de control [19]✅.
- Bergsland & Wechsler: ni lo totalmente predecible ni lo totalmente intuitivo-improvisado sostienen el interés; hay que **guiar al usuario entre ambos regímenes en el tiempo** [5]✅. MotionComposer adopta "transparencia y causalidad clara" como filosofía para poblaciones vulnerables [36]✅.
- Senturk: el éxito de una obra interactiva depende de la **robustez del sistema**; si la tecnología falla en escena, la obra falla [13]📊.

### 4.4 Sobrecarga del performer
- Senturk (citando literatura de danza interactiva): "los bailarines no sólo necesitan concentrarse en sus movimientos corporales sino también pensar en las consecuencias mapeadas a la música. Esto añade otro nivel de complejidad al acto... incluso bailarines profesionales, no entrenados tradicionalmente para tal interacción" [13]📊.
- "Si un bailarín es forzado a hacer un gesto ajeno a la performance, resta foco visual y perturba la expresión visual" — la restricción clave de la danza interactiva vs instrumentos [13]📊.
- El experimento de York muestra la sobrecarga en su forma pura: interfaces que exigen descomponer el sonido en parámetros se viven como frustrantes [1]✅.
- Para el beacon ❓: el modo consonancia debe evitar exigir al cuerpo "poses que suenan bien" ajenas a la danza; la ventaja del detuning es que es un parámetro *global* del sonido (textura/afinación), no eventos discretos que contar.

### 4.5 Falta de repetibilidad y "glissando hell"
- OtoKin: pitch continuo desde movimiento → "glissando hell"; solución: intervals discretos por postura + actualización sólo en cruces de umbral de aceleración [5]✅.
- OtoKin elige matriz many-to-all **fija y repetible** (coeficientes aleatorios sólo en diseño) precisamente para que "direcciones de movimiento interesantes puedan explorarse al encontrarlas" [5]✅.
- Rokeby documenta la repetibilidad como primer test de agencia del interactor [19]✅.
- Con Moto: el nivel de abstracción del mapeo determina si el sistema se siente tocable o autónomo [15]✅ — demasiada generación = pérdida de agencia.

---

## 5. Implicancias para consonancia del movimiento → detuning de armónicos

(La psicoacústica del detuning — Sethares, Plomp-Levelt, umbrales de segregación, diseño del snap — está en `04_continuous-pitch-expression.md`; aquí sólo consecuencias de la literatura de sistemas/mapeos.)

**Lo que la literatura predice que va a funcionar:**

1. **El mapeo energético es el indicado**: HWK recomiendan textualmente derivadas del input relacionadas con la energía del performer [1]✅; OtoKin lo adopta como ideal (aceleración→volumen/filtros) [5]✅; SoniMime encuentra que jerk/tilt directos superan al pattern-matching [37]✅; la línea EyesWeb valida QoM/fluidity/CI como features expresivas robustas [9][10][11]✅. La propuesta HIT (energía cinemática aprovechada → consonancia) está alineada con 25 años de evidencia.
2. **La serie armónica fija es el ancla anti-glissando-hell**: OtoKin demuestra que el pitch pilotado continuo desde danza es injugable y que la solución es anclar a valores derivados de postura/energía [5]✅. En el beacon la serie hace ese papel y además da referencia auditiva (cada armónico "casa" perceptualmente) — ventaja sobre OtoKin, cuyos intervalos aditivos no tienen anclaje perceptual tan fuerte ❓✅.
3. **Repetibilidad como requisito de agencia**: matriz fija de detuning (mismo movimiento → mismo detuning), con la variación reservada a la *entrada* (el cuerpo), nunca al mapeo [5][19]✅.
4. **Energía potencial incluida**: "high-energy still states" — un cuerpo quieto-pero-tenso debe poder sonar consonante/desonante; no mapear sólo cinemática en acto [5]✅. HarMoCAP tiene `contraction`/`expansion` y proxies Laban weight/time/space para esto ❓.
5. **Dos capas ESCHER**: HarMoCAP (gestual) → capa abstracta "consonancia por joint" → harmonic-shaper (sónico) es el modelo de dos capas canónico; permite cambiar el motor de síntesis sin tocar la definición de consonancia y viceversa [1]✅.
6. **Nivel de abstracción = nivel de agencia**: si el detuning responde a cualidades finas (por joint), el cuerpo lo vive como instrumento tocable; si responde a cualidades globales (QoM total), el sistema se vuelve partner/ambiente [15]✅❓. Ambos son modos legítimos — Con Moto sugiere hacer la abstracción **configurable** [15]✅.

**Lo que va a morder:**

1. **Latencia y jitter del pipeline de visión** (30 fps = 33 ms + inferencia + red + síntesis): auditar contra la meta de ~10 ms de Wessel-Wright [4]✅ o al menos conocer y compensar (predicción, suavizado). Rokeby vivió con ~33 ms de loop y funcionó artísticamente [19]✅, pero para control fino de afinación la varianza es peor que el valor medio [4]✅❓.
2. **La Recuperation**: si el detuning sigue la energía instantánea, las fases de recuperación del gesto (bajas en energía, esenciales para el fraseo [12]✅) producirán "caídas" de sonido no musicales. Diseñar el smoothing/ataque del mapeo de detuning como se diseña un envelope: que respete el fraseo corporal, no sólo la cinemática cruda ❓.
3. **Impredecibilidad del tracking** (oclusiones, jitter de keypoints): un sensor "preciso pero inexacto" puede pilotear loudness pero no pitch [2]✅ — y el detuning ES pitch. Suavizado y confianza-por-joint antes de mandar a afinación ❓.
4. **Sobrecarga del bailarín**: pensar "¿cómo sueno?" mientras se baila añade carga cognitiva [13]📊. Mitigación: low entry fee (moverse ya suena consonante/desonante sin técnica), techo alto vía fine control por joint [4]✅.
5. **Fragilidad escénica**: robustez primero; el éxito de la obra depende del sistema [13]📊.
6. **No hay prior art publicado de cualidad→afinación continua**: no hay recetas probadas que copiar; lo más cercano (OtoKin postura→intervalos [5]✅, Kinect tensión→escala [14]✅) es discreto. El beacon explora terreno nuevo — riesgo de diseño, pero hueco real confirmado en ambos carriles (este y R4) ❓.
7. **Herramienta de re-mapeo en vivo**: los diseñadores de mappings trabajan por exploración difusa + experimentación dirigida con feedback inmediato [32]✅; el modo consonancia necesita una consola (escenas del weaver) para que artistas iteren mappings cuerpo→detuning sin tocar código ❓.

---

## Sources

Marcas: ✅ primaria/peer-reviewed/docs oficiales · 📊 secundaria especializada · 📰 prensa/blog · ⚠️ contestado/biblio-only · ❓ inferencia.

1. ✅ Hunt, A., Wanderley, M. & Kirk, R. (2000). *Towards a Model for Instrumental Mapping in Expert Musical Interaction*. ICMC 2000. PDF fetch: http://recherche.ircam.fr/anasyn/wanderle/Gestes/Externe/Hunt_Towards.pdf
2. ✅ Wanderley, M. (2001). *Gestural Control of Music*. Kassel workshop paper. Fetch: http://recherche.ircam.fr/equipes/analyse-synthese/wanderle/pub/kassel/kassel.pdf (+ índice HTML http://recherche.ircam.fr/equipes/analyse-synthese/wanderle/pub/kassel/)
3. ✅ Schacher, J. (2010). *Motion To Gesture To Sound: Mapping For Interactive Dance*. NIME 2010. Fetch: http://www.nime.org/proceedings/2010/nime2010_250.pdf
4. ✅ Wessel, D. & Wright, M. (2002). *Problems and Prospects for Intimate Musical Control of Computers*. Computer Music Journal 26(2) / arXiv:2010.01570. Fetch: https://arxiv.org/pdf/2010.01570
5. ✅ Dahlstedt, P. & Skånberg Dahlstedt, A. (2019). *OtoKin: Mapping for Sound Space Exploration through Dance Improvisation*. NIME 2019. Fetch: http://www.nime.org/proceedings/2019/nime2019_paper031.pdf
6. ✅ Giomi, A. & Leonard, J. (2020). *Towards an Interactive Model-Based Sonification of Hand Gesture for Dance Performance*. NIME 2020. Fetch: https://www.nime.org/proceedings/2020/nime2020_paper72.pdf
7. ✅ Rovan, J., Wanderley, M., Dubnov, S. & Depalle, P. (1997). *Instrumental Gestural Mapping Strategies as Expressivity Determinants in Computer Music Performance*. AIMI Kansei Workshop — citado y resumido en [1] (biblio secundaria dentro de primaria).
8. ✅ Camurri, A., Hashimoto, S., Ricchetti, M., Ricci, A., Suzuki, K., Trocca, R. & Volpe, G. (2000). *EyesWeb: Toward Gesture and Affect Recognition in Interactive Dance and Music Systems*. Computer Music Journal 24(1):57-69. DOI 10.1162/014892600559182. Fetch (metadatos/TLDR/citas): https://www.semanticscholar.org/paper/EyesWeb%3A-Toward-Gesture-and-Affect-Recognition-in-Camurri-Hashimoto/56834eab8b016f854fc6eb6ad6cdfdb39b9f110c
9. ✅ Camurri et al., *Analysis of Expressive Gesture: The EyesWeb Expressive Gesture Processing Library* (capítulo/paper, vía academia.edu). Fetch: https://www.academia.edu/130275092/Analysis_of_Expressive_Gesture_The_EyesWeb_Expressive_Gesture_Processing_Library
10. ✅ Castellano, G., Bresin, R., Camurri, A. & Volpe, G. (2007). *Expressive Control of Music and Visual Media by Full-Body Movement*. NIME 2007. Fetch: http://www.nime.org/proceedings/2007/nime2007_390.pdf
11. ✅ Visi, F. & Dahl, L. (2018). *Real-Time Motion Capture Analysis and Music Interaction with the Modosc Descriptor Library*. NIME 2018. Fetch: http://www.nime.org/proceedings/2018/nime2018_paper0031.pdf
12. ✅ Ward, N., Penfield, K., O'Modhrain, S. & Knapp, R.B. (2008). *A Study of Two Thereminists: Towards Movement Informed Instrument Design*. NIME 2008. Fetch: http://www.nime.org/proceedings/2008/nime2008_117.pdf
13. 📊 Senturk, S. (2011). *Interactivity in Contemporary Dance and Music* (Georgia Tech review; casos Digital Dance Project, Palindrome, Troika Ranch). Fetch: https://sertansenturk.com/uploads/publications/senturk2011interactivity.pdf
14. ✅ Yoo, M.-J., Beak, J.-W. & Lee, I.-K. (2011). *Creating Musical Expression using Kinect*. NIME 2011. Fetch: https://nime.org/proc/nime2011_yoo/index.html + PDF https://nime.org/proceedings/2011/nime2011_324.pdf
15. ✅ Chen, Z., Lei, H. & Huang, C.-A. (2026). *Con Moto: Embodied Steering of Music Transformers for Live Dance Improvisation*. NIME 2026. Fetch: http://nime.org/proceedings/2026/nime2026_7.pdf
16. ✅ Wessel, D., Wright, M. & Schott, J. (2002). *Intimate Musical Control of Computers with a Variety of Controllers and Gesture Mapping Metaphors*. NIME 2002 demo. Fetch: https://www.nime.org/proc/nime2002_wessel/index.html
17. ✅ Rokeby, D. *Very Nervous System* (documentación oficial de la obra, 1986-1990s). Fetch: https://www.davidrokeby.com/vns.html
18. ✅ Rovan, J.B., Wechsler, R. & Weiß, F. *Seine hohle Form: Artistic Collaboration in an Interactive Dance and Music Performance Environment*. Crossings (TCD). Fetch: https://crossings.tcd.ie/issues/1.2/Rovan/
19. ✅ Rokeby, D. (1990). *The Harmonics of Interaction*. MusicWorks 46. Fetch: http://www.davidrokeby.com/harm.html
20. ✅ Machover, T. — página oficial MIT Media Lab (Hyperinstruments, lanzados 1986). Fetch: https://web.media.mit.edu/~tod/
21. 📊 Wikipedia: *Tod Machover* (redirect de Hyperinstrument; usos por Yo-Yo Ma, Brain Opera 1996, House of Music 2000). Fetch: https://en.wikipedia.org/wiki/Hyperinstrument
22. ✅ Sonami, L. *lady's glove* (documentación de primera mano de las 5 generaciones). Fetch: https://sonami.net/portfolio/items/ladys-glove/
23. 📊 HCI Museum: *The Hands* (Waisvisz/STEIM 1984; referencia a Torre, Andersen & Baldé, CMJ 2016; crackle.org archive). Fetch: https://interfacemuseum.com/exhibits/the-hands/
24. ✅ McNutt, E. (2012). *Crossole: A Gestural Interface for Composition, Improvisation and Performance using Kinect*. NIME 2012 — indexado en https://nime.org/papers/ ; PDF: http://www.nime.org/proceedings/2012/nime2012_185.pdf (no fetcheado — biblio del índice ✅)
25. ✅ *Non-invasive sensing and gesture control for pitched percussion hyper-instruments using the Kinect*. NIME 2012 — índice NIME; PDF: http://www.nime.org/proceedings/2012/nime2012_297.pdf (biblio del índice ✅)
26. ✅ *Motion and Synchronization Analysis of Musical Ensembles with the Kinect*. NIME 2013 — índice NIME; PDF: http://www.nime.org/proceedings/2013/nime2013_304.pdf (biblio del índice ✅)
27. ✅ *Developing the Dance Jockey System...* (NIME 2012, nime2012_182.pdf), *LoopJam* (NIME 2012, nime2012_260.pdf), *Sensemble* (NIME 2006, nime2006_134.pdf) — todos localizados en el índice https://nime.org/papers/ (biblio del índice ✅)
28. ✅ Erdem, Ç., Schia, K.H. & Jensenius, A.R. (2019). *Vrengt: A Shared Body-Machine Instrument for Music-Dance Performance*. NIME 2019. Fetch: http://www.nime.org/proceedings/2019/nime2019_paper037.pdf
29. ✅ Díaz-Durán, J.R., Turmo Vidal, L. & Tajadura-Jiménez, A. (2023). *Joakinator...* NIME 2023. Fetch: http://www.nime.org/proceedings/2023/nime2023_12.pdf
30. ✅ Kirby, J. (2025). *Exploring pose estimation in instrumental composition: the Body Fragmented project*. Frontiers in Computer Science 7. Fetch: https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2025.1570296/full
31. ✅ Paine, G. (2010). *Towards a Taxonomy of Realtime Interfaces for Electronic Music Performance*. NIME 2010. Fetch: https://www.nime.org/proceedings/2010/nime2010_436.pdf
32. ✅ West, T.J., Caramiaux, B. & Wanderley, M.M. (2020). *Making Mappings: Examining the Design Process*. NIME 2020. Fetch: https://www.nime.org/proceedings/2020/nime2020_paper55.pdf
33. ✅ *Human-in-the-Loop: Crossmodal AI Alignment between Movement and Audio Latent Spaces for Expressive Sonification*. NIME 2026 — índice NIME; PDF: http://nime.org/proceedings/2026/nime2026_113.pdf (biblio del índice ✅)
34. ✅ *From Improvised Movement to Musical Improvisation...* NIME 2026 — índice NIME; PDF: http://nime.org/proceedings/2026/nime2026_135.pdf (biblio del índice ✅)
35. ✅ *Role-Separated Live Movement Sonification...* NIME 2026 — índice NIME; PDF: http://nime.org/proceedings/2026/nime2026_146.pdf (biblio del índice ✅)
36. ✅ Bergsland, A. & Wechsler, R. (2015). *Composing Interactive Dance Pieces for the MotionComposer, a device for Persons with Disabilities*. NIME 2015. Fetch: http://www.nime.org/proceedings/2015/nime2015_246.pdf
37. ✅ Fox, J. & Carlile, J. (2005). *SoniMime: Movement Sonification for Real-Time Timbre Shaping*. NIME 2005. Fetch: http://www.nime.org/proceedings/2005/nime2005_242.pdf
38. ✅ Ward, N. & Torre, G. (2014). *Constraining Movement as a Basis for DMI Design and Performance*. NIME 2014. Fetch: http://www.nime.org/proceedings/2014/nime2014_404.pdf
39. ✅ NIME proceedings index (2322 papers parseados; búsquedas de dance/Kinect/sonification/mapping/mocap para localizar [24]-[27], [33]-[35]). Fetch: https://nime.org/papers/
40. ⚠️ *Hunt, A. & Kirk, R. (2000). Mapping Strategies for Musical Performance* (cap. en *Trends in Gestural Control of Music*, IRCAM): ubicado en EARS http://ears.huma-num.fr/ab151b43-92cd-4440-8296-c5edd1212cac.html y ResearchGate, pero el fetch de ambos falló (internal server error / login wall). Se cita sólo lo que [1] y [2] reportan de él. Biblio-only ⚠️.
41. ⚠️ hyperinstruments.org — no fetcheable desde este entorno (bloqueo de red). Sustituido por [20]✅ y [21]📊.
42. ⚠️ *Organised Sound* 7(2) editorial de Wanderley (2002), "Mapping Strategies in real-time computer music" — fetch completo vía SensorWiki: https://sensorwiki.org/isidm/mapping/mapping_-_organised_sound_editorial_text ✅ (contexto del número especial de mapping; lista de los 10 artículos; preguntas de diseño: ¿mapping estático o dinámico? ¿simple o complejo? ¿intuitivo o aprendido?).
43. ❓ Las inferencias de diseño marcadas ❓ en §1-5 son del agente, a validar con el equipo y/o con prototipos.
