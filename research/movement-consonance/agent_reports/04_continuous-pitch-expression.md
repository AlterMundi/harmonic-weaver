---
project: harmonic-weaver
title: "Pitch continuo y desafinación expresiva — síntesis, percepción y motores (R4)"
type: research-report
tags: [research, movement-consonance, pitch-bend, detuning, dissonance, sethares, plomp-levelt, additive-synthesis, supercollider, csound, snap, quantization, harmonic-weaver]
date: 2026-09-24
confidence: high
---

# 04 — Pitch continuo y desafinación expresiva

> Carril R4 del pack movement-consonance. Pregunta central: si cada joint del cuerpo
> desafina continuamente "su" armónico de la serie (F0 = 40 Hz, 13 bandas / 32 voces),
> con límite ±50% del salto al vecino y snap configurable hacia el modo afinado,
> ¿qué predicen la psicoacústica y el estado del arte de la síntesis?
>
> Leyenda de confianza (idéntica al MANIFEST): ✅ primaria/peer-reviewed/docs oficiales ·
> 📊 secundaria especializada · 📰 prensa/blog · ⚠️ contestado · ❓ inferencia del agente a verificar.
> Las citas numéricas `[n]` remiten a `## Sources` al final.

## 0. TL;DR

1. **La teoría Sethares/Plomp-Levelt SÍ predice el efecto buscado, con un detalle cuantitativo importante**: la rugosidad máxima entre dos tonos puros ocurre cuando su diferencia de frecuencia es ≈ ¼ del ancho de banda crítica [2][8]✅. Para la serie de 40 Hz eso cae en Δf ≈ 18–27 Hz según la frecuencia base (cálculo propio con la parametrización de Sethares, Sección 3) — y el tope de ±50% del gap en Hz (±20 Hz, la regla del MANIFEST: "40 puede ir de 20 a 60") aterriza **justo sobre el pico de rugosidad** para los armónicos bajos-medios. El recorrido afinado→desafinado barre todo el continuo de Helmholtz: batidos lentos (<15 Hz, percibidos como vibrato/ondulación agradable) → rugosidad máxima (~¼ CB) → separación en dos alturas distintas [8][39]✅.
2. **La aritmética de cents está verificada y hay una ambigüedad de diseño que resolver**: octave = 1200.0 cents exactos; quinta 80→120 Hz = 1200·log2(3/2) = 701.955 ≈ 702 cents; ±50% = ±600 / ±351 cents, como afirma el brief ✅. PERO "±50% del gap" admite dos lecturas — espacio-cents y Hz-lineal — con consecuencias muy distintas (Sección 3.3): en Hz-lineal (±20 Hz siempre) la desviación en cents es enorme abajo (h1: −1200/+702 c) y pequeña arriba (h13: ±65 c); en cents la regla simétrica **deja huecos de cobertura** y sólo la regla asimétrica (−50% hacia el vecino inferior, +50% hacia el superior) mosaica el continuo sin huecos ni solapes (verificado numéricamente, error 0.000 Hz). La regla del MANIFEST (Hz-lineal) también mosaica perfectamente.
3. **Modulación de frecuencia por parcial a 30–60 Hz es totalmente factible** en los dos motores: SuperCollider con bancos `SinOsc`/`DynKlang` (freq modulable en tiempo real, `a.setn`/`a.mapn` desde buses de control) [1][4][35]✅ y Csound con `adsynt` (tablas de frecuencia por parcial escritas a k-rate con `tablew`) [40]✅. El costo CPU de 13–32 senos es despreciable; el verdadero trabajo de ingeniería es la **continuidad de fase** al cambiar frecuencia por bloque (acumulador de fase + interpolación de freq), no el DSP ❓(inferencia de ingeniería, estándar en síntesis aditiva).
4. **El snap debe ser una atracción continua, no un imán binario**: Melodyne corrige con intensidad 0–100% y a niveles bajos sólo toca las notas muy desafinadas [43]✅; el Continuum cuantiza con "amount y duration controlables en tiempo real" [24]✅; Berdahl muestra que detentes (pozos de potencial) mejoran la precisión sin impedir glissandi [15]✅. La percepción categórica de intervalos (Siegel & Siegel) explica por qué: dentro de la categoría la desviación se asimila; cerca del borde se percibe como salto [26]✅. Recomendación operativa: snap proporcional con histéresis/deadband, preservando la modulación rápida y corrigiendo sólo la deriva lenta — exactamente la separación drift/vibrato que hace Melodyne [43]✅.
5. **Hallazgo de riesgo perceptual**: a desviación completa (±20 Hz), el parcial desafinado **se segrega del complejo y se oye como otra nota** — los umbrales de segregación de armónicos desafinados son ~0.5–4% de la frecuencia [39]✅, y ±20 Hz es 25% en h2, 10% en h5, 3.8% en h13. Para que el desafinado se sienta "expresivo" (batido/rugosidad/coro, parcial fusionado) y no "otra nota equivocada", la excursión útil de los armónicos medios está más cerca de ±(1–4)% ≈ ±15–70 cents que del tope completo. El snap y el límite por armónico deberían calibrarse contra este umbral (Sección 4.4).
6. **Prior art directo de movimiento→desafinación: casi inexistente**. Lo más cercano: sonificación de ángulo de rodilla→pitch continuo en rehabilitación de marcha [30]✅; OtoKin, que documenta el fracaso del mapeo continuo de pitch desde danza ("glissando hell") y lo reemplaza por intervalos discretos derivados de la postura [36]✅; Adaptun de Sethares, que desafina en tiempo real pero para MINIMIZAR disonancia (dirección opuesta: aquí se desafina para EXPRESARLA) [16]✅. El modo consonancia de harmonic-weaver ocupa un hueco real: la serie fija ancla las notas (evita glissando hell) y el cuerpo modula la afinación dentro de la serie.

---

## 1. Pitch bend y control continuo de altura en síntesis e instrumentos

### 1.1 MIDI pitch bend: resolución, rangos y por qué los rangos grandes son difíciles

- El mensaje Pitch Bend de MIDI 1.0 es de **14 bits** (0–16383), con centro en 8192 (2000H) [13]✅. La sensibilidad no está fijada por el mensaje: es función del receptor y se configura con **RPN 00 00**, donde el MSB son semitonos y el LSB cents [13][11]✅.
- La convención por defecto en la práctica es **±2 semitonos** [11]📊. La especificación soporta hasta ±24 semitonos; la propuesta MPE usa ±48 como default (±96 máximo) [11]📊. MIDI 2.0 sube el pitch bend a **32 bits** y agrega pitch bend por nota, eliminando el "stepping" audible en controles continuos [28]✅.
- Aritmética de resolución (cálculo propio): con ±2 st, cada paso = 200 cents/8192 ≈ **0.024 cents**; con ±48 st, cada paso = 9600/8192 ≈ **0.586 cents**. Es decir, estirar el rango degrada la resolución de control en ~24×.
- **Por qué los rangos grandes son difíciles de controlar**: (a) el mismo recorrido físico del controlador mapea a más cents → menos precisión motora por cent; (b) desaparecen las referencias táctiles intermedias — la literatura de NIME trata la selección de pitch en rango continuo como problema motor de primer orden [15]✅; (c) la percepción categórica hace que dentro de un intervalo musical el oyente/ejecutante tenga poca resolución de "sharp vs flat" (Sección 4.3) [26]✅. Para el beacon esto importa poco (el control es OSC→motor, no MIDI), pero explica por qué **ningún estándar de control musical asume desviaciones de cientos de cents como gesto fino**: ±351–600 cents está muy fuera de todo rango de pitch bend convencional.

### 1.2 El "problema theremin": instrumentos de pitch continuo y su tocabilidad

- El theremin es el caso canónico de instrumento sin feedback táctil: pitch continuo controlado por la posición de la mano en un campo eléctrico; "cada matice del gesto se refleja en el sonido" y su dificultad es notoria [14]✅.
- La **"Theremin Hypothesis"** (Berdahl et al.): "si un instrumento musical no provee ningún feedback háptico, probablemente sea más difícil de tocarlo con precisión" [14][15][27]✅. Berdahl añade detentes hápticos programados en las posiciones del temperamento igual para asistir la selección de pitch en rango continuo, permitiendo aún así glissandi, caídas y scoops; los tests preliminares confirman mejora de precisión [15]✅.
- Contra-evidencia matizada: la autoetnografía de 3 años de Xiao (DIS 2024) muestra que la ejecución precisa y musical sin tacto SÍ se alcanza, apoyada en **feedback auditivo continuo, propiocepción e imaginación auditiva** ("pre-imaginar la próxima nota") [14]✅. Conclusión de diseño: la tocabilidad del pitch continuo no la da el hardware sino el cierre del loop percepción-acción — relevante para el beacon, donde el cuerpo entero ya está en un loop propioceptivo-auditivo natural.
- El **Continuum Fingerboard** (Haken) es el instrumento comercial de referencia: superficie continua con resolución de **0.1 cent**, respuesta 0.33 ms, 16 voces, y — clave para nosotros — una función de **"rounding" por software que cuantiza el pitch a temperamento igual, escala justa u otra, con cantidad y duración del rounding controlables en tiempo real** [24]✅. Es exactamente el "snap configurable" que el brief pide, ya productizado.
- ROLI Seaboard: superficie continua ("5D touch") donde Glide (pitch bend) y Slide (Y) tienen **faders de sensibilidad** que gradúan cuán "pianístico" o continuo se siente el instrumento [42]✅ — otra confirmación de que la expresividad continua se administra con parámetros de respuesta, no con on/off.

### 1.3 Portamento / glide: implementación

- Portamento = deslizamiento de altura de una nota a otra (término vocal, s. XVII; también "glide" en sintes y steel guitars) [38]📰.
- En MIDI 1.0 se controla con **CC 5** (portamento time) y **CC 65** (portamento on/off; ≤63 off, ≥64 on); CC 84 es detune coarser [22]📊.
- En motores de síntesis, la implementación estándar es un glide exponencial o lineal de la frecuencia del oscilador entre nota y nota (SuperCollider: `Lag`/`VarLag`/`Slew` sobre la señal de frecuencia; `VarLag` permite formas de curva — linear, sine, welch, exponencial — y está diseñado para "suavizar señales de control") [7]✅. Para el beacon, la transición desafinado→afinado (snap) es un portamento hacia el múltiplo entero: la forma de curva elegida (S-shaped vs lineal) cambia el carácter percibido del snap ❓.

### 1.4 Detuning expresivo en la práctica musical real

- **Cuerdas**: la entonación de un violinista no es fija — debe ser **adaptativa** al contexto armónico (tocar "en tune" con el bajo, con la cuerda al aire, con el temperamento del ensemble); los instrumentistas de cuerda ajustan sistemáticamente terceras y séptimas según función armónica [34]📰. El vibrato de cuerda tiene tasa ~5–6 Hz y excursión menor que la vocal [20]📊.
- **Voz — vibrato**: norma clásica 50–120 cents pico-a-pico (±25–60 desde el centro); por debajo de ~20 cents se percibe como tono recto, por encima de ~150 como excesivo [20]📊. Datos multicéntricos (Nix et al. 2016): sopranos 106 c, tenores 98 c pico-a-pico habituales [20]📊; mediciones de cantantes líricos profesionales en Prame 1997 (JASA) [19]⚠️. **El ±50% del gap en Hz del beacon equivale a ±400–1200 cents en h1–h3: 3–10× el vibrato vocal más ancho.** La desviación expresiva humana "normal" vive en la banda de decenas de cents, no de cientos.
- **Voz — drift y just intonation**: en canto a capella SATB los cantantes tienden a entonación no-igual-temperada y el centro de pitch **deriva necesariamente** al modular; Howard concluye que "el pitch drift es potencialmente una parte necesaria de mantenerse afinado" [29]✅. Es decir: desafinar levemente el sistema de referencia es el comportamiento afinado real de los humanos.
- **Barbershop / "expanded sound"**: los acordes "ringing" ("bell tones", "expanded sound") resultan de **just intonation + acordes de séptima de dominante + voicing cerrado + oído entrenado** [6]✅. Los cuartetos ajustan deliberadamente: la séptima armónica (7:4) se canta ~968.8 cents sobre la fundamental, **31 cents más grave** que la séptima menor del temperamento igual [25]✅. En el repertorio tradicional 35–60% de los acordes son dominantes, y los cantantes experimentados ajustan automáticamente hasta que el acorde "lockea" — el cerebro detecta cuándo el acorde se traba [33]📰. **Precedente cultural exacto del modo consonancia**: performers que negocian continuamente cents individuales contra una estructura armónica fija para maximizar el "ringing". La física del ringing (parciales reforzándose por coincidencia) es la misma que la curva de disonancia de Sethares predice (Sección 2.4) ❓(conexión inferida, bien fundada).

---

## 2. Serie armónica y parciales desafinados

### 2.1 Just intonation vs temperamento igual para la serie armónica

- Los parciales de una cuerda ideal están en múltiplos enteros exactos fn = n·f10; la coincidencia de parciales entre tonos cuyas fundamentales guardan razón 2:1 explica la consonancia de la octava [2]✅.
- La **just intonation** usa razones enteras simples (3:2 = 701.955 c, 5:4 = 386.31 c, 7:4 = 968.83 c); el **temperamento igual** las aproxima (quinta 700 c, tercera mayor 400 c vs 386.3 c justa — diferencia 13.7 c, cálculo propio) [25][8]✅.
- Sethares (principio de consonancia local): los mínimos de la curva de disonancia de un timbre armónico caen en las razones simples 1:1, 2:1, 3:2, 4:3, 5:4, 5:3 — es decir, **la escala justa emerge de la psicoacústica del timbre armónico**, y el temperamento igual es "un compromiso aceptable" porque el oído es poco sensible a pequeñas desviaciones [8]✅. Para el beacon: la serie 40·n ES la escala; desafinar un parcial es moverse fuera de los mínimos locales de la curva de disonancia.

### 2.2 Inarmonicidad en instrumentos reales: piano, Railsback

- Las cuerdas reales tienen rigidez: los parciales salen **agudos** respecto de los múltiplos enteros, y el desvío crece con n² (modelo α: fn ≈ n·f1·(1+αn²)) [2][9]✅.
- Los afinadores **estiran** la afinación (agudos arriba, graves abajo) para que los parciales de las notas bajas coincidan con las fundamentales de las altas; la curva de Railsback (medida en los 1930s) es el promedio empírico de esa desviación en pianos bien afinados [9]📰/✅.
- **Giordano 2015 (JASA, open access)**: usando espectros medidos de un Steinway M + el modelo de disonancia de Plomp-Levelt parametrizado por Sethares, la afinación que minimiza la disonancia sensorial **reproduce cuantitativamente la curva de Railsback** [2]✅. Esto es central para harmonic-weaver por dos razones:
  1. Demuestra que el pipeline "espectro de parciales → curva de disonancia computable → configuración óptima" funciona contra datos perceptuales reales de técnicos humanos.
  2. Implica que **el punto "consonante" del beacon no tiene por qué ser la serie entera exacta**: si los parciales tuvieran inarmonicidad (o si se quisiera emular el estiramiento), el mínimo de disonancia se desplaza. Con senos puros ideales el mínimo SÍ es la serie entera exacta ❓(inferencia directa del modelo: senos armónicos perfectos ⇒ mínimos en razones n/m).
- Efecto de la inarmonicidad en la percepción de altura y en la afinación subjetiva confirmado experimentalmente (tonos de piano inarmónicos producen curva de afinación tipo Railsback en oyentes) [2]📊(referencia cruzada del abstract PubMed visto en búsqueda; no leído completo) ⚠️.

### 2.3 Qué pasa cuando un parcial se aleja del múltiplo entero: batidos, rugosidad, banda crítica

- **Helmholtz**: dos tonos casi iguales producen batido audible; al acercarse, el batido se ralentiza y desaparece en la coincidencia. "Los batidos lentos se perciben como vibrato agradable; los rápidos como rugosos y molestos. La disonancia es causada por el batido rápido de componentes senoidales; la consonancia es la ausencia de tales batidos" [8]✅.
- **Plomp & Levelt 1965** ("Tonal consonance and critical bandwidth", JASA 38:548–560): midieron la consonancia de pares de senoides; la disonancia depende de Δf = f2−f1 Y de la frecuencia inferior; la conclusión de los datos es que la diferencia entre intervalos consonantes y disonantes está relacionada con los **batidos de parciales adyacentes** [41]✅. Su curva: disonancia 0 en el unísono, máximo en Δf0, y decae suavemente hacia separaciones mayores [2]✅.
- **Δf0 ≈ ¼ del ancho de banda crítica** [2]✅. Números concretos para nuestra serie (cálculo propio con la parametrización de Sethares, d2 = e^(−b1·s·Δf) − e^(−b2·s·Δf), s = s*/(s1·f1+s2), b1=3.5, b2=5.75, s*=0.24, s1=0.021, s2=19 [2]✅):

| f inferior | Δf de rugosidad máxima | Equivalente en cents sobre f |
|---|---|---|
| 40 Hz | 18.2 Hz | +651 c |
| 80 Hz | 19.0 Hz | +369 c |
| 120 Hz | 19.8 Hz | +264 c |
| 200 Hz | 21.3 Hz | +175 c |
| 400 Hz | 25.2 Hz | +106 c |
| 520 Hz | ~27 Hz | ~+87 c |

  El gap lineal entre armónicos vecinos es siempre 40 Hz, así que **el pico de rugosidad cae al 45–68% del gap** según el armónico: la regla ±50%-en-Hz pone el tope del desafinado prácticamente en el máximo de disonancia para h1–h5, y ligeramente antes del máximo para los armónicos altos (cálculo propio) ❓verificable re-ejecutando el modelo.
- **Regímenes perceptuales al barrer el detune desde 0** (síntesis de [8][2][39]✅, armado propio ❓):
  1. **0–~4 Hz de desvío**: batidos lentos audibles como pulsación/vibrato de amplitud — "agradable", efecto coro.
  2. **~5–15 Hz**: batidos rápidos → rugosidad creciente (zona Helmholtz "annoying").
  3. **~¼ CB (18–27 Hz en nuestra serie)**: rugosidad máxima.
  4. **> ~½ CB**: los dos tonos se separan perceptualmente; deja de haber fusión/rugosidad y el parcial desafinado empieza a escucharse como **entidad independiente con su propia altura** [39]✅.
- **Segregación de armónicos desafinados (Hartmann, McAdams & Smith 1990, JASA)**: en un complejo periódico, un armónico desafinado se oye como tono separado a partir de umbrales de ~0.5–4% de desafinación (dependiendo del número de armónico, nivel y duración); el umbral es aproximadamente constante en % para armónicos 2–11 y sube para 12–14; la fundamental desafinada se detecta "porque suena desafinada" más que como entidad separada [39]✅. Traducción a nuestra serie con tope ±20 Hz: h2 = 25%, h5 = 10%, h13 = 3.8% — **todo el rango alto del detune está por encima del umbral de segregación**. La fusión se mantiene sólo en la primera porción del recorrido (~±1–4% ≈ ±17–70 cents en h2).
- Advertencia teórica: la consonancia simultánea percibida es **compuesta** — interferencia (rugosidad), periodicidad/armonicidad y familiaridad cultural; el modelo de sólo-rugosidad explica una parte [37]✅. Para el beacon esto juega a favor: la desafinación afecta la componente de interferencia (inmediata, pre-lingüística) sin requerir familiaridad cultural — exactamente lo que se quiere de un feedback corporal.

### 2.4 La curva de disonancia computable de Sethares

- Sethares encapsula la curva de Plomp-Levelt en una función explícita de dos parciales (fórmulas arriba) y define la disonancia total de dos tonos complejos como suma sobre pares de parciales ponderada por amplitudes: D = ½ ΣΣ Bij·d2(f1i, f2j), con dos variantes de peso (producto de amplitudes; loudness del componente más débil) [2]✅. Es la misma familia de modelos que evalúa y compara sistemáticamente Harrison & Pearce (su modelo "Sethares" es la configuración default de rugosidad) [37]✅.
- **Propiedades de las curvas de disonancia** [8]✅: el unísono es el mínimo global; la curva de un timbre de n parciales tiene ≤ 2n(n−1) mínimos locales, y hasta la mitad caen en razones fi/fj entre parciales del propio timbre — por eso la serie armónica "se auto-afina": cada armónico vecino define un mínimo local donde el sonido se fusiona.
- Para timbres armónicos de 6–9 parciales con amplitudes cayendo 0.88, los mínimos caen en 1:1, 2:1, 3:2, 4:3, 5:4, 5:3... = la escala justa [8]✅. **Predicción para el beacon**: con la serie 40·n completa (13–32 parciales), cada posición afinada n·40 es un mínimo local profundo de la curva; alejar un parcial de ahí aumenta monótonamente la disonancia hasta ~¼ CB y luego la meseta de segregación. El claim del equipo ("entre modos afinados y desafinados se activa el continuo de frecuencias") es correcto en Hz, y además barre el continuo psicoacústico completo fusión→batido→rugosidad→separación.
- **Validación numérica propia** (cálculos ejecutados con la parametrización de Giordano/Sethares [2]✅; tabla completa en el Anexo A):
  - Auto-disosonancia (disonancia intrínseca) de la serie armónica pura (40–520 Hz, amps 0.88^n): D ≈ 1.09. Desafinar UN armónico al tope ±20 Hz cambia D total sólo ±2–8% (0.94–1.08×): la disonancia agregada se mueve poco porque la serie ya tiene auto-disosonancia basal.
  - Pero la **rugosidad por pares contra el vecino** sí barre el rango completo: p.ej. h2 (80 Hz) contra h3 (120 Hz): d2 = 0.128 afinado → 0.181 a +20 Hz (100 Hz); contra h1 (40 Hz): 0.122 → 0.063. La suma contra ambos vecinos tiene máximo plano alrededor de +11 Hz (91 Hz) con D_pair = 0.251 vs 0.250 afinado — la rugosidad total es casi plana en la mitad exterior del rango porque al alejarse de un vecino se acerca al otro ❓(resultado del cálculo; sensible a las amplitudes asumidas).
  - Consecuencia de diseño: **la disonancia agregada NO es buen parámetro de feedback para este sistema** (cambia poco); lo que el oído sigue es la rugosidad local del parcial desafinado contra sus vecinos y su eventual segregación. Si R5 quiere un número escalar "consonancia del cuerpo", conviene computarlo sobre pares (parcial desafinado ↔ vecinos) o sobre la curva completa incluyendo amplitudes reales del harmonic-shaper, no sobre D total de la serie.

---

## 3. Cuánta desafinación es perceptible / musical

### 3.1 Difference limens (DLF) para frecuencia

- DLFs para tonos puros de duración adecuada son notablemente pequeños: a 1000 Hz, DLF medio ≈ **1.8 Hz (~3.1 cents)** (Moore 1974, vía [12]✅); entre 500–2000 Hz, DLFs relativos de **0.13–0.15% (≈2.2–2.6 cents)** en los mejores oyentes; la relación es en U — peor por debajo de 500 Hz y mucho peor sobre 2 kHz [12]✅ (tesis doctoral York, revisando Moore 1973 [21]⚠️, Wier et al. 1977, Sek & Moore 1995).
- Músicos clásicos: DLF ~0.13%; no-músicos ~0.86% (**~15 cents**), convergiendo tras 4–8 h de entrenamiento — la diferencia es entrenamiento, no oído "musical" innato [12]✅.
- **Para nuestra serie (40–520 Hz)**: estamos por debajo de la zona óptima de 500–2000 Hz; en 40 Hz el DLF absoluto crece. Estimación: en la banda 40–200 Hz un DLF razonable es del orden de 0.3–0.5 Hz (≈ 5–20 cents según la frecuencia) ❓(extrapolación de la curva en U de [12], no medida en el paper). Aun así: **cualquier detune mayor a ~10–20 cents es claramente audible**; el rango del sistema (cientos de cents) excede el umbral por 1–2 órdenes de magnitud. No hay problema de "demasiado sutil" — el problema es el opuesto (Sección 3.4).

### 3.2 El continuo consonancia-disonancia en función de cents

- No existe una única función "cents→disonancia" porque la rugosidad depende de Δf en Hz contra la banda crítica, que es casi lineal en Hz a bajas frecuencias. En nuestra serie, el eje relevante es Δf en Hz: 0–4 Hz batido agradable, 5–15 Hz rugosidad creciente, ~19–27 Hz máximo, >40 Hz separación/segregación [2][8][39]✅ (zonas: armado propio ❓).
- En cents, el mismo recorrido es no-lineal por armónico: para h2, el pico de rugosidad (+19 Hz) equivale a +369 cents; para h13, +27 Hz ≈ +87 cents. **Un mismo valor en cents significa cosas perceptuales distintas según el armónico** — argumento fuerte para implementar el límite del detune en Hz (o en % del gap lineal), como hace el MANIFEST, y no en cents.

### 3.3 La aritmética de ±50% del gap — VERIFICADA, con dos interpretaciones

Fórmula: cents(f1,f2) = 1200·log2(f2/f1). Cálculos ejecutados y verificados numéricamente (Anexo A):

**Interpretación A — 50% del gap medido EN CENTS** (la que menciona el brief):

| Salto | Gap | ±50% del gap |
|---|---|---|
| 40→80 (octava) | 1200·log2(2) = **1200.0 c** | **±600 c** ✓ (40 → 28.28 / 56.57 Hz) |
| 80→120 (quinta) | 1200·log2(3/2) = **701.955 ≈ 702 c** | **±351 c** ✓ (80 → 65.32 / 97.98 Hz) |
| 120→160 (cuarta) | 1200·log2(4/3) = 498.0 c | ±249 c |
| 160→200 (3ª mayor) | 1200·log2(5/4) = 386.3 c | ±193 c |
| 400→440 (h10→h11) | 1200·log2(11/10) = 165.0 c | ±82.5 c |
| 680→720 (h17→h18) | 1200·log2(18/17) = 99.0 c | ±49.5 c |

  La afirmación del brief (octava=1200, quinta=702, ±50%=±600/±351) es **exacta** ✅(verificación propia).
  ⚠️ **Ojo con la regla simétrica en cents**: si cada armónico puede moverse ±50% del gap en ambas direcciones, la cobertura del continuo tiene HUECOS — h1 sube hasta 56.57 Hz pero h2 sólo baja hasta 65.32 Hz (agujero 56.6–65.3 Hz; cálculo propio, Anexo A). Para mosaico perfecto en cents hace falta la **regla asimétrica**: −50% del gap hacia el vecino INFERIOR, +50% del gap hacia el vecino SUPERIOR. Con esa regla los bordes coinciden exactamente (h1↑ = 56.569 = h2↓; h2↑ = 97.980 = h3↓; ... verificado con error 0.0000 Hz en los 12 pares) y la unión cubre [28.3 Hz, ∞) sin huecos.

**Interpretación B — 50% del gap lineal EN Hz** (la del MANIFEST: "40 puede ir de 20 a 60; 80 de 60 a 100"):

- El gap lineal entre armónicos vecinos es siempre f0 = 40 Hz ⇒ ±50% = **±20 Hz para todos los armónicos** ⇒ h_n ∈ [(n−0.5)·40, (n+0.5)·40]. Los bordes encadenan exactamente (hi_n = lo_{n+1} = (n+0.5)·40) ⇒ cobertura continua de [20 Hz, ∞) sin huecos ni solapes ✅(cálculo propio).
- Equivalencias en cents (asimétricas, porque cents es logarítmico):

| Armónico | Rango Hz | Rango en cents |
|---|---|---|
| h1 (40) | 20–60 | **−1200 … +702 c** |
| h2 (80) | 60–100 | −498 … +386 c |
| h3 (120) | 100–140 | −316 … +267 c |
| h5 (200) | 180–220 | −182 … +165 c |
| h13 (520) | 500–540 | −68 … +65 c |
| h17 (680) | 660–700 | −52 … +50 c |
| h32 (1280) | 1260–1300 | −27 … +27 c |

**Comparación y recomendación**: la interpretación B (MANIFEST) es auto-consistente, mosaica sola, mantiene el pico de rugosidad dentro del rango en todos los armónicos y — crucialmente — da a los armónicos graves (los que el cuerpo siente y los que definen la fundamental) el mayor rango expresivo. La interpretación A asimétrica también mosaica y es más uniforme perceptualmente arriba (todos los armónicos altos quedan en ±50–100 c, dentro del rango "vibrato expresivo"), pero deja a h1 en ±600 c (medio tritono — se oye como OTRA nota, no como la fundamental desafinada). **Ninguna de las dos lecturas está mal; son instrumentos musicales distintos** ❓(juicio de diseño). Sugerencia: parametrizar el límite por armónico (límite en % del gap lineal, con techo opcional en cents) y decidir con escucha — la infraestructura de snap permite experimentar barato.

### 3.4 Cuánto detune es "musical" vs "error"

- Referencia humana de desviación expresiva: vibrato vocal ±25–60 c [20]📊; séptima armónica del barbershop: −31 c respecto del temperamento igual [25]✅; deriva de entonación a capella: decenas de cents acumulados [29]✅; stretch de piano: decenas de cents por octava en extremos [9]📰. **Toda la desviación "expresiva" documentada en música real vive en ±(5–100) cents.**
- El rango del beacon (cientos de cents en Hz-lineal para h1–h5) excede por mucho la banda expresiva humana: no es un defecto, es una decisión estética — es un instrumento de feedback corporal, no un violín. Pero predice el régimen perceptual: detunes grandes = segregación (se oye otra nota + rugosidad contra vecinos), detunes chicos (<~4% ≈ <~20–70 c según armónico) = fusión con coloración (batido/coro/rugosidad) [39]✅. El modo "consonante" debería operar en el segundo régimen; el tope completo del ±50% pertenece al primero.

---

## 4. Snap-to-scale / cuantización: técnicas y psicoacústica

### 4.1 Melodyne (Celemony) — el estándar de facto del snap de pitch

Del manual oficial [43]✅:
- **Correct Pitch Macro**: slider de intensidad 0–100%; por defecto mueve las notas hacia el semitono más cercano; opcionalmente hacia el grado de la escala o del acorde ("Snap to Chord Scale").
- **Corrección proporcional**: "a niveles bajos afecta sólo a las notas muy desafinadas, dejando intactas las que ya están cerca del pitch previsto; al subir el slider, incluso esas son influidas, crecientemente, hasta 100% = todas exactamente afinadas".
- **Separación drift / modulación**: un segundo slider reduce el *pitch drift* — "la ondulación lenta sintomática de mala técnica" — mientras que "fluctuaciones más rápidas como pitch modulation o vibrato permanecen intactas".
- Las notas afinadas manualmente a mano quedan excluidas del macro por defecto (el sistema asume intención).
- Los sibilantes se mueven en pantalla pero no se transponen acústicamente (transponerlos sonaría antinatural).

Lecciones transferibles al snap del beacon [43]✅ + ❓(transferencia propia): (1) snap como **porcentaje continuo** de corrección, no on/off; (2) corregir preferentemente las desviaciones grandes (respuesta no lineal: gain bajo cerca del modo afinado, alto lejos); (3) **no tocar la componente rápida** del gesto — si el detune sigue la aceleración del joint, el snap debe actuar sobre la deriva lenta (componente DC/tono-base del detune) y dejar pasar la modulación expresiva; (4) respetar la intención: si un modo del sistema fija un detune deliberado, el snap no debería deshacerlo.

### 4.2 Cuantización con parámetros en tiempo real: Continuum y pitch bend cuantizado

- Continuum: "rounding" a temperamento igual/justa/otra escala, **con cantidad y duración controlables en tiempo real** [24]✅ — precedentes directos de "snap configurable" del brief.
- Berdahl (haptics): detentes tipo pozo de potencial — fuerza de resorte cerca del centro del detent, cero fuera — que mejoran la precisión de selección de pitch manteniendo glissandi/scoops posibles; los detents sensibles a la fuerza permiten "sobrevolar" detents distractores apretando más fuerte [15]✅. Traducción a software: el snap como **campo de fuerzas** (atractor con gradiente local) en vez de redondeo duro ❓.
- En MIDI, el "quantized pitch bend" existe como práctica (bend escalonado a semitonos) pero no como estándar; MIDI 2.0 per-note pitch bend a 32 bits facilita curvas finas [28]✅.

### 4.3 Psicoacústica del snap: ¿cuándo se siente expresivo y cuándo error?

- **Percepción categórica de intervalos (Siegel & Siegel 1977)**: músicos con relative pitch identifican intervalos afinados con >95% de acierto pero "no pueden distinguir confiablemente sharp de flat" DENTRO de una categoría musical; las funciones de identificación tienen fronteras nítidas entre categorías; juzgaron "afinados" el 63% de los estímulos cuando sólo 23% lo eran [26]✅. Implicación: **desviaciones pequeñas dentro del "modo afinado" se asimilan a la categoría** (el armónico sigue siendo "ese armónico"); al cruzar el borde categorial, la percepción salta — el snap que opera cerca del centro se siente natural (nadie percibe la corrección de ±10–20 c) y el que opera cerca del borde se percibe como cambio de identidad ❓(inferencia bien fundada en [26]).
- **Hartmann et al.**: el umbral de segregación (~0.5–4%) marca la frontera física entre "coloración del timbre" y "otra nota" [39]✅. Snap que devuelve el parcial por debajo del umbral de segregación = "se afinó"; snap desde muy lejos cruzando el umbral = "desapareció una nota y apareció la afinada" — potencialmente brusco si el tiempo de snap es corto ❓.
- **Regla práctica (síntesis propia ❓, anclada en [43][24][15][26][39])**: el snap se siente expresivo cuando (a) es proporcional (más rápido desde más lejos, suave cerca del centro — como el macro de Melodyne), (b) preserva la modulación rápida del gesto, (c) usa histéresis/deadband cerca del modo afinado para que el sistema no "tiemble" entre snap y control cuando la señal de movimiento es ruidosa a 30 Hz, y (d) su duración es comparable a un portamento musical (~50–200 ms), no un cuantizado instantáneo. Se siente error cuando es binario, instantáneo, o cuando pelea contra la entrada de control (oscilación snap↔detune).
- **Histéresis**: ningún paper central encontrado que prescriba histéresis para snap de pitch en síntesis (laguna honesta); la práctica es estándar en control (deadband + hold) y Berdahl implementa el análogo físico (resorte local, fuerza nula fuera del detent) [15]✅. En SuperCollider la primitiva natural es `Schmidt`/`InRange` + `VarLag`, o un `Slew` asimétrico ❓(propuesta de implementación).

### 4.4 Recomendación operativa de límites por armónico (nueva, derivada de los datos)

Combinando umbrales de segregación [39]✅ y banda expresiva humana [20][25]📊 (cálculo propio, Anexo A):

| Régimen | h2 (80 Hz) | h5 (200 Hz) | h13 (520 Hz) | Percepción |
|---|---|---|---|---|
| Fusión-corista | < ±0.8 Hz (<17 c) | < ±2 Hz (<17 c) | < ±2.6 Hz (<9 c) | coro/batido lento, "casi afinado" |
| Batido→rugosidad | ±1–19 Hz | ±2–21 Hz | ±3–27 Hz | tensión creciente, Helmholtz |
| Segregación | > ±19 Hz (>4%) | > ±8 Hz | > ±5 Hz | "otra nota" + rugosidad residual |

Sugerencia ❓: mapear el 0–100% de la "consonancia del joint" a un rango por armónico elegido entre ~±4% (todo fusión/rugosidad, modo más "musical") y el ±50%-Hz completo (incluye segregación, modo más "dramático/feedback"), configurable por instalación.

---

## 5. Síntesis aditiva con frecuencia independiente por parcial

### 5.1 Qué soporta cada motor

**SuperCollider (beacon-spatial)**:
- `SinOsc.ar(freq, phase)`: freq **muestreada a audio-rate** — modulación de frecuencia con continuidad de fase por diseño (oscilador de wavetable con interpolación lineal) [35]✅.
- `Klang`: banco de senos eficiente pero **parámetros fijos a init-time** [5]✅ → no sirve para detune por parcial.
- `DynKlang`: "banco de osciladores senoidales... menos eficiente que Klang, es básicamente un wrapper de SinOscs", pero **todos los parámetros cambiables en tiempo real**; el ejemplo oficial de FM por parcial (`[800,1000,1200] + SinOsc.kr([2,3,4.2],0,[13,24,12])`) es exactamente modulación independiente por parcial [1]✅.
- `DynKlank`: idem para resonadores (banco de Ringz), con `a.setn(\freqs, ...)` y **`a.mapn(\freqs, bus, n)` — mapeo de un bus de control a N frecuencias** [4]✅. Patrón recomendado para el beacon: OSC a 30 Hz → un Synth de control escribe 13–32 valores en un bus (`Out.kr(bus, freqs)`) → `mapn` los conecta a `DynKlang`/banco de SinOsc. Esto vive enteramente en el servidor, sin mensajes por nota.
- Suavizado: `VarLag.kr(in, time, curvature, warp)` con formas sine/welch/exp — diseñado para "suavizar señales de control"; warning oficial: en .ar trata la entrada como control-rate, frecuencia máxima segura = mitad del control rate del servidor [7]✅. Con blockSize 512 @ 48 kHz → control rate 93.75 Hz → Nyquist de control ~47 Hz: actualizaciones de 30 Hz OK, 60 Hz al límite ❓(cálculo propio sobre dato de docs).
- Klank/DynKlank vs SinOsc bank: si harmonic-shaper ya es aditivo en Python, la alternativa SC pura es `SinOsc` ×N con gains — 32 senos con lookup+lerp es costo trivial en scsynth ❓(inferencia de ingeniería; consistente con [1] que llama a DynKlang "menos eficiente" sólo en comparación con Klang, no en absoluto).

**Csound (referencia de patrón)**:
- `adsynt`: "síntesis aditiva con número arbitrario de parciales, no necesariamente armónicos"; las tablas de frecuencia y amplitud por parcial "se usan usualmente para generar parámetros en runtime con `tablew`" a k-rate [40]✅ — el equivalente exacto del bus de control de SC, documentado oficialmente.
- `partials`/`pvsftr`/`pvsftw`: pista/resíntesis de parciales con intercambio de datos de frecuencia vía tablas [23][31]✅ (más orientado a análisis-resíntesis que a nuestro caso).

**Faust**:
- `oscillators.lib` provee `os.oscs` (seno por fórmula recursiva) y `os.oscp` (wavetable) con frecuencia como señal de entrada [32]✅; un banco aditivo = N instancias con freq modulada — Faust compila a C++ eficiente, costo comparable a SC ❓(inferencia; no hay benchmark publicado de 32 oscs modulados a kr).
- No existe primitiva "DynKlang" en Faust: se escribe el banco explícitamente (ventaja: control total del acumulador de fase) ❓.

**harmonic-shaper (Python, 48 kHz, bloque 512–1024, 32 voces)**:
- Rate de bloque: 48000/1024 = 46.9 Hz; 48000/512 = 93.75 Hz (cálculo propio sobre hechos del engine dados en el brief). El control OSC a 30 Hz llega más lento que el rate de bloque → cada paquete OSC afecta 1–3 bloques; no hay aliasing temporal del control ❓.
- **Punto crítico**: si la frecuencia de cada voz se actualiza por bloque sin acumular fase, los saltos de frecuencia producen discontinuidad de fase → clicks. La solución estándar (y la que SinOsc/adsynt implementan internamente) es **integrar fase por muestra: phase += 2π·f[n]/fs con f[n] interpolada dentro del bloque** (rampa lineal entre f_old y f_new, o filtro de un polo) ❓(práctica estándar de síntesis aditiva; coherente con [35][40]✅ donde la continuidad de fase es inherente al diseño).
- Con bloque 512 @ 48 kHz y updates de 30 Hz, un paso típico de frecuencia entre updates para un gesto corporal suave es < 1 Hz — la interpolación lineal dentro del bloque lo vuelve inaudible ❓(estimación propia).
- CPU: 32 voces × (1 sin por muestra + acumulador) ≈ 1.5M senos/s — trivial incluso en NumPy vectorizado por bloque; el scaling 1/√N y las envolventes ya existentes no cambian ❓(inferencia de ingeniería).

### 5.2 Costo de scheduling a 30–60 Hz de control

- Patrón recomendado (SC): OSC → sclang (o directo vía OSCFunc a un Synth) → `Out.kr(bus, [f1..f32])` una vez por paquete; el motor de audio lee el bus cada ciclo de control. Costo por paquete: 32 floats — despreciable; **no usar `setn` por mensaje ni Synth por parcial** (overhead de mensajes del servidor) ❓(práctica SC estándar; `mapn` documentado en [4]✅).
- En Python/harmonic-shaper: el loop ya corre a rate de bloque (47–94 Hz) > 30 Hz del control → basta leer el último paquete OSC al armar cada bloque (sample-and-hold con interpolación) ❓.
- Latencia total OSC→audio: 1 paquete (33 ms a 30 Hz) + 1 bloque (10.7–21.3 ms) ≈ 45–55 ms — dentro del rango de "feedback inmediato" para sonificación de movimiento ❓(estimación; la literatura de sonificación de marcha usa loops comparables [30]✅).

---

## 6. Prior art: mapear movimiento a desafinación (en vez de a elección de nota)

Búsqueda específica de sistemas movimiento→detune continuo. Resultado honesto: **no se encontró ningún sistema publicado que mapee cinemática de cuerpo completo al detune por-parcial de una serie armónica** — el modo consonancia es novedoso en esa combinación ❓(afirmación negativa limitada a lo buscado). Los vecinos más cercanos:

1. **Kantan et al. (SoniHED 2022)** — sonificación continua de cinemática de rodilla (ángulo → pitch) para rehabilitación de marcha hemiparética; mapeo directo parámetro-movimiento→frecuencia, validado con fisioterapeutas sobre 15 pacientes [30]✅. Es el precedente más directo de **joint→pitch continuo**, aunque mono-articular y con pitch absoluto (no detune de una serie).
2. **OtoKin (Dahlstedt & Skånberg Dahlstedt, NIME 2019)** — danza improvisada sonificada con mapeo many-to-many de todo el cuerpo; documentación explícita del fracaso del pitch continuo: *"Pitch is a parameter different from all others. If mapped continuously, we end up in an undesirable 'glissando hell'. For the pitch-based engines, we had to design a mechanism that derives discrete pitch values. Simple quantization does not make sense."* Su solución: comparaciones de coordenadas entre joints que habilitan intervalos discretos sumados a una fundamental fija [36]✅. **Lección directa para harmonic-weaver**: la serie armónica fija hace de ancla (como su fundamental fija), y el detune ±50% con snap es exactamente la estructura intermedia que evita el glissando hell sin caer en cuantización simple — la advertencia de OtoKin valida el diseño por contraste.
3. **Adaptun (Sethares, ICMC 2002)** — retuning adaptativo en tiempo real: un algoritmo de gradiente (SPSA) mueve las fundamentales de las notas sonantes para **minimizar** la disonancia sensorial según el modelo Plomp-Levelt/Sethares; introduce "contexto" (parciales inaudibles que anclan el cálculo) para evitar que los pitches vaguen [16]✅. Es el prior art computacional exacto del motor de detune, en dirección opuesta (converger a consonancia). Reutilizable: la misma función de costo puede invertirse — el joint "consonante" minimiza D localmente (snap a la serie), el "dissonant" la maximiza dentro del rango.
4. **CamJam (NIME 2026)** — interfaz musical colaborativa por cámara (MediaPipe); aplica corrección de offset de frecuencia (+1 a +3 Hz escalados) para compensar el detune inherente de su modelo físico Karplus-Strong y mantener cohesión armónica entre módulos [18]✅: detune como parámetro gestionado en instrumentos de cámara en tiempo real.
5. **The Hands (Waisvisz/STEIM)** — control gestural clásico (acelerómetros, ultrasonido) donde el gesto mapea a pitch/timbre continuos; citado como referente de mapeo expresivo movimiento→sonido [44]📊(mención en paper NIME; sistema histórico ampliamente documentado).
6. **Sonificación de error** — familia establecida (golf, remo, ciclismo): el sonido marca la desviación respecto de un gesto objetivo [17]✅(taxonomía: triggers "error-based" como categoría propia en la revisión sistemática de 101 estudios). El detune por disonancia-del-movimiento del beacon puede leerse como error sonification musicalizada: el modo afinado ES el objetivo, la desafinación ES la señal de error — con la ventaja estética de que el "error" suena dentro de una serie armónica y el snap devuelve la resolución [17][30]✅ + ❓(lectura propia).
7. **Continuum + rounding** [24]✅ y **Berdahl detents** [15]✅: el prior art de "pitch continuo con atracción configurable a modos discretos" en instrumentos (no en mapeo corporal).

Síntesis de novedad ❓: los componentes existen por separado (joint→pitch [30]; anti-glissando por anclaje a estructura [36]; detune que minimiza disonancia [16]; snap parametrizable [24][43]); **la contribución del modo consonancia es la inversión semántica** — usar el detune continuo dentro de una serie fija como expresión de la calidad del movimiento, con la disonancia como señal (no como defecto a corregir).

---

## 7. Respuestas directas a las preguntas del brief (a–d)

- **(a) ¿Sethares/Plomp-Levelt predicen el efecto buscado?** Sí, con matices [2][8][37]✅: alejar un parcial de la serie aumenta la rugosidad contra sus vecinos con máximo en ~¼ de banda crítica (Δf ≈ 18–27 Hz en la serie de 40 Hz), que coincide con el tope ±20 Hz de la regla del MANIFEST. Dos advertencias: la disonancia AGREGADA de la serie cambia poco (±2–8%) — la señal perceptual es la rugosidad local y la segregación; y la consonancia percibida total incluye armonicidad y familiaridad, no sólo rugosidad [37]✅.
- **(b) Aritmética de cents**: verificada — octava 1200.0 c, quinta 701.955 c, ±50% = ±600/±351 c ✅. La regla simétrica en cents deja huecos; mosaica perfecto con regla asimétrica-en-cents o con la regla lineal-en-Hz del MANIFEST (Anexo A).
- **(c) ¿FM por parcial a 30–60 Hz factible y agradable?** Factible sin discusión: SC (`DynKlang`/`SinOsc` + bus de control + `mapn`, control rate 93.75 Hz con bloque 512) [1][35][7]✅, Csound (`adsynt` + `tablew`) [40]✅, Python con acumulador de fase e interpolación por bloque ❓(estándar). Agradable: sí SI el detune se suaviza (VarLag/slew), si la modulación rápida del gesto no se cuantiza, y si los topes por armónico se eligen conscientemente entre régimen de fusión (<±4%) y régimen de segregación (±50% completo) [39][43]✅+❓.
- **(d) ¿Qué recomienda la literatura de snap?** Snap proporcional 0–100% con respuesta no lineal (Melodyne), separando deriva lenta de modulación rápida y preservando esta última [43]✅; cantidad y duración configurables en tiempo real (Continuum) [24]✅; forma de pozo de potencial con histéresis/deadband cerca del centro (análogo a los detents de Berdahl) [15]✅; duraciones tipo portamento musical, no instantáneas ❓; y calibrar el punto de snap contra la percepción categórica — correcciones de decenas de cents cerca del modo afinado son imperceptibles/asiniladas [26]✅.

---

## Anexo A — Aritmética explícita (cálculos propios ejecutados y verificados)

Todas las cifras de esta sección fueron computadas con Python (math.log2, modelo de Sethares con constantes de Giordano [2]✅) durante la escritura de este reporte.

**A1. Fórmula de cents**: `cents(f1,f2) = 1200·log2(f2/f1)`.

**A2. Gaps de la serie 40·n en cents**:
- h1→h2: 1200·log2(80/40) = 1200·1 = **1200.0 c** (octava exacta)
- h2→h3: 1200·log2(120/80) = 1200·log2(1.5) = 1200·0.5849625 = **701.955 c ≈ 702** (quinta justa)
- h3→h4: 1200·log2(4/3) = **498.045 c** (cuarta justa)
- h4→h5: 1200·log2(5/4) = **386.314 c** (tercera mayor justa)
- h10→h11: 1200·log2(11/10) = **165.004 c**
- h17→h18: 1200·log2(18/17) = **98.955 c**
- h23→h24: 1200·log2(24/23) = **73.681 c**; h31→h32: 1200·log2(32/31) = **54.964 c**
- ±50%: **±600 / ±350.98 / ±249.02 / ±193.16 / ±82.50 / ±49.48 / ±36.84 / ±27.48 c** respectivamente. El brief cita ±600/±351: correcto.

**A3. Interpretación A (cents), regla simétrica → huecos** (contraejemplo verificado):
- h1 +600 c = 40·2^(600/1200) = 40·√2 = **56.569 Hz**; h2 −351 c = 80·2^(−351/1200) = 80/√(3/2)^... = **65.320 Hz** → hueco (56.569, 65.320) Hz.

**A4. Interpretación A (cents), regla asimétrica → mosaico perfecto**:
- h1 → [40·2^(−600/1200), 40·2^(+600/1200)] = [28.284, 56.569] Hz
- h2 → [80·2^(−600/1200), 80·2^(+351/1200)] = [56.569, 97.980] Hz
- h3 → [120·2^(−351/1200), 120·2^(+249/1200)] = [97.980, 138.564] Hz
- ... verificado para los 12 pares: borde superior de h_n = borde inferior de h_{n+1} con |diff| = 0.0000 Hz. (Razón: el borde compartido es la media geométrica n·√(n²−1)·f0... numéricamente exacto porque +50% del gap hacia arriba desde h_n y −50% del gap hacia abajo desde h_{n+1} son el mismo punto: f_n·√(f_{n+1}/f_n) = √(f_n·f_{n+1}).)
- Cobertura: [28.28 Hz, ∞) continuo.

**A5. Interpretación B (Hz-lineal, MANIFEST) → mosaico perfecto**:
- gap lineal constante = 40 Hz ⇒ ±50% = ±20 Hz ⇒ h_n ∈ [(n−0.5)·40, (n+0.5)·40]; hi_n = lo_{n+1} = (n+0.5)·40 exactamente.
- Cobertura [20 Hz, ∞). Conversión a cents (asimétrica): h1 [−1200.0, +702.0] c; h2 [−498.0, +386.3]; h3 [−315.6, +266.9]; h5 [−182.4, +165.0]; h13 [−67.9, +65.3]; h17 [−51.7, +50.2]; h32 [−27.3, +26.8].

**A6. Modelo de disonancia (parametrización de Sethares usada por Giordano [2]✅)**:
- d2(f1,f2) = e^(−b1·s·Δf) − e^(−b2·s·Δf); s = s*/(s1·min(f1,f2)+s2); b1=3.5, b2=5.75, s*=0.24, s1=0.021, s2=19.
- Δf de rugosidad máxima (analítico): Δf0 = ln(b2/b1)/((b2−b1)·s) → 18.2 Hz @ f=40; 19.0 @ 80; 19.8 @ 120; 21.3 @ 200; 25.2 @ 400; 27.1 @ 500; 36.0 @ 960.
- Como % del gap de 40 Hz: 45% (h1) → 48% (h2) → 50% (h3) → 53% (h5) → 63% (h10) → 68% (h12–13): **el tope ±50%-Hz barre hasta/pasado el pico de rugosidad en toda la serie**.
- D total de la serie 40–520 Hz (13 parciales, amps 0.88^n): 1.0917. Con un armónico al tope ±20 Hz: rango 1.021–1.178 (0.94–1.08×). Con h2 barre ±20 Hz: 1.079–1.115. Rugosidad por pares h2↔vecinos: 0.250 (afinado) → máx 0.251 (+11 Hz) → 0.244 (+20 Hz) — meseta plana; d2 contra vecino superior individual: 0.128 → 0.181 (+41%).
- N=32 (40–1280 Hz): D = 1.5733; los armónicos altos aportan poco (amps 0.88^31 ≈ 0.019).

**A7. Conversiones psicoacústicas**:
- 1.8 Hz @ 1 kHz = 1200·log2(1.0018) = **3.11 c**; 0.13% = **2.25 c**; 0.86% = **14.82 c** [12]✅.
- ±2 semitonos MIDI en 8192 pasos = 0.0244 c/paso; ±48 semitonos = 0.586 c/paso (cálculo propio).
- 1% de desafinación (umbral bajo de segregación [39]) = 17.3 c en h2 (0.8 Hz), 13.8 c en h5, 9.9 c en h13; 4% = 68 / 55 / 39 c.

---

## Sources

Marcas: ✅ primaria/peer-reviewed/docs oficiales · 📊 secundaria especializada · 📰 prensa/blog/divulgación · ⚠️ contestado/no verificado independiente.

- ✅ [1] SuperCollider Help — DynKlang: https://doc.sccode.org/Classes/DynKlang.html
- ✅ [2] Giordano, N. (2015). "Explaining the Railsback stretch in terms of the inharmonicity of piano tones and sensory dissonance." JASA 138(4):2359–2366 (open access): https://pubs.aip.org/asa/jasa/article/138/4/2359/900231/Explaining-the-Railsback-stretch-in-terms-of-the
- ✅ [4] SuperCollider Help — DynKlank: https://doc.sccode.org/Classes/DynKlank.html
- ✅ [5] SuperCollider Help — Klank: https://doc.sccode.org/Classes/Klank.html
- ✅ [6] Averill, G. (1999). "Bell Tones and Ringing Chords: Sense and Sensation in Barbershop Harmony." The World of Music 41(1):37–51: https://www.jstor.org/stable/41700111
- ✅ [7] SuperCollider Help — VarLag: https://doc.sccode.org/Classes/VarLag.html
- ✅ [8] Sethares, W.A. "Relating Tuning and Timbre" (texto completo del artículo de Experimental Musical Instruments, base de TTSS): https://sethares.engr.wisc.edu/consemi.html
- 📰 [9] Wikipedia — Piano acoustics (inharmonicity, Railsback curve): https://en.wikipedia.org/wiki/Piano_acoustics
- ✅ [10] (mismo paper que [37], versión PMC — no se llegó a extraer por cookie-wall; se cita la versión MPG) https://pmc.ncbi.nlm.nih.gov/articles/PMC7032667/
- 📊 [11] StudioCode.dev — MIDI Pitch Bend (14-bit, RPN 00, rangos MPE): https://studiocode.dev/kb/MIDI/midi-pitch-bend/
- ✅ [12] Mathias, S.R. (2010). "Individual Differences in Pitch Perception." PhD thesis, University of York (revisión de Moore 1973/74, Wier 1977, Sek & Moore 1995, Micheyl 2006): https://etheses.whiterose.ac.uk/id/eprint/1481/1/Thesis.pdf
- ✅ [13] MIDI.org — Summary of MIDI 1.0 Messages (Pitch Bend Change, RPN 0): https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message
- ✅ [14] Xiao, X. & Fdili Alaoui, S. (2024). "Tuning In to Intangibility: Reflections from My First 3 Years of Theremin Learning." DIS '24, ACM: https://dl.acm.org/doi/fullHtml/10.1145/3643834.3661584
- ✅ [15] Berdahl, E., Niemeyer, G. & Smith, J.O. (2009). "Using Haptics to Assist Performers in Making Gestures to a Musical Instrument." NIME '09: https://www.nime.org/proceedings/2009/nime2009_177.pdf
- ✅ [16] Sethares, W.A. (2002). "Real-Time Adaptive Tunings Using Max." Proc. ICMC: https://sethares.engr.wisc.edu/paperspdf/adaptun2002.pdf
- ✅ [17] Coers, M. et al. (2026). "Movement Sonification Types and Triggers: A Systematic Review." Perceptual and Motor Skills: https://journals.sagepub.com/doi/10.1177/00315125261448460
- ✅ [18] Lorenzen, F. et al. (2026). "CamJam: A Modular Collaborative and Accessible Digital Musical Interface." NIME '26: https://nime.org/proceedings/2026/nime2026_150.pdf
- ⚠️ [19] Prame, E. (1997). "Vibrato extent and intonation in professional Western lyric singing." JASA 102:616–621 — paywall, sólo metadatos verificados: https://pubs.aip.org/asa/jasa/article/102/1/616/557516/Vibrato-extent-and-intonation-in-professional
- 📊 [20] Voice Science Lexicon — Vibrato Extent (normas de Nix et al. 2016 multicenter, Glasner & Johnson 2022): https://www.voicescience.org/lexicon/vibrato-extent/
- ⚠️ [21] Moore, B.C.J. (1973). "Frequency difference limens for short-duration tones." JASA 54:610–619 — paywall; cifras tomadas vía [12]: https://pubs.aip.org/asa/jasa/article-pdf/54/3/610/12065448/610_1_online.pdf
- 📊 [22] Sound StackExchange — MIDI CC5/CC65/CC84 (portamento): https://sound.stackexchange.com/questions/44080/midi-how-to-implement-cc-65-c-5-and-cc-84-and-example
- ✅ [23] Csound Manual — partials (partial tracking): https://csound.com/docs/manual/partials.html
- 📰 [24] Wikipedia — Continuum Fingerboard (resolución 0.1 cent, rounding en tiempo real; datos primarios: Haken Audio): https://en.wikipedia.org/wiki/Continuum_Fingerboard
- 📰 [25] Wikipedia — Harmonic seventh chord (968.826 c, barbershop, 4:5:6:7): https://en.wikipedia.org/wiki/Harmonic_seventh_chord
- ✅ [26] Siegel, J.A. & Siegel, W. (1977). "Categorical perception of tonal intervals: Musicians can't tell sharp from flat." Perception & Psychophysics 21:399–407: https://link.springer.com/article/10.3758/BF03199493
- 📊 [27] Berdahl, E. PhD thesis (Theremin Hypothesis; texto citado vía [14][15]): https://www.cct.lsu.edu/~eberdahl/Papers/berdahl-thesis-augmented.pdf
- ✅ [28] MIDI.org — "The State of MIDI 2.0" (feb 2026; pitch bend 32-bit, per-note pitch bend): https://midi.org/the-state-of-midi-2-0-high-resolution-performance-and-the-rise-of-profiles-update-feb-2026
- ✅ [29] Howard, D.M. (2007). "Intonation Drift in A Capella SATB Quartet Singing With Key Modulation." Journal of Voice 21(3):300–315: https://www.sciencedirect.com/science/article/abs/pii/S0892199705001657
- ✅ [30] Kantan, P.R. et al. (2022). "Designing Sonified Feedback on Knee Kinematics in Hemiparetic Gait." SoniHED 2022: https://vbn.aau.dk/files/519310180/SoniHED2022_Proceedings_Kantan.pdf
- ✅ [31] Csound Manual — pvsftr: https://csound.com/docs/manual/pvsftr.html
- ✅ [32] Faust Libraries — oscillators.lib: https://faustlibraries.grame.fr/libs/oscillators/
- 📰 [33] Nicholas, J. "Four Main Reasons Why Barbershop Singing Sounds Unique" (vía ChoralNet/ACDA): https://choralnet.org/archives/434484
- 📰 [34] Gorski, A. (2022). "Why violinists need an adaptive approach to intonation." The Strad: https://www.thestrad.com/playing-hub/why-violinists-need-an-adaptive-approach-to-intonation-alexandra-gorski/15418.article
- ✅ [35] SuperCollider Help — SinOsc: https://doc.sccode.org/Classes/SinOsc.html
- ✅ [36] Dahlstedt, P. & Skånberg Dahlstedt, A. (2019). "OtoKin: Mapping for Sound Space Exploration through Dance Improvisation." NIME '19: https://www.nime.org/proceedings/2019/nime2019_paper031.pdf
- ✅ [37] Harrison, P.M.C. & Pearce, M.T. (2020). "Simultaneous Consonance in Music Perception and Composition." Psychological Review (open access, MPG): https://pure.mpg.de/rest/items/item_3257902_1/component/file_3257903/content
- 📰 [38] Wikipedia — Portamento: https://en.wikipedia.org/wiki/Portamento
- ✅ [39] Hartmann, W.M., McAdams, S. & Smith, B.K. (1990). "Hearing a mistuned harmonic in an otherwise periodic complex tone." JASA 88:1716–1724 (PDF completo): https://www.mcgill.ca/mpcl/files/mpcl/hartmann_1990_jasa.pdf
- ✅ [40] Csound Manual — adsynt: https://csound.com/docs/manual/adsynt.html
- ✅ [41] Plomp, R. & Levelt, W.J.M. (1965). "Tonal consonance and critical bandwidth." JASA 38(4):548–560 (registro Semantic Scholar con abstract): https://www.semanticscholar.org/paper/Tonal-consonance-and-critical-bandwidth.-Plomp-Levelt/1d3ccc073b1b3f13f95e2392ff81a9eff0e7a4d2
- ✅ [42] ROLI — Seaboard 2 manual (5D Touch, Glide/Slide faders): https://roli.com/us/manuals/seaboard-2
- ✅ [43] Celemony — Melodyne 5 Help: Correct Pitch Macro (documentación oficial): https://helpcenter.celemony.com/M5/doc/melodyneStudio5/en/M5tour_MacroPitch?env=dawsWithAra
- 📊 [44] Nakra, T. (2010). "The GRIP MAESTRO: Idiomatic Mappings of Emotive Gestures" (NIME '10; contexto sobre The Hands de Waisvisz — cita de snippet de búsqueda): https://www.nime.org/proceedings/2010/nime2010_419.pdf
