---
project: harmonic-weaver
title: "CROSS-REPORT — Consonancia del movimiento como control musical"
type: cross-report
tags: [research, movement-consonance, cross-report, laban, hit, detuning, metrics, harmonic-weaver, harmocap]
date: 2026-09-24
confidence: high
---

# CROSS-REPORT — Consonancia del movimiento como control musical

> ⚠️ ENMENDADO 2026-09-27 por `ADDENDUM-f1-2-grid.md` (aclaraciones de Nicolás):
> la regla ±50% aterriza en la serie armónica de f1/2 (el detuneo máximo es
> intervalo JUSTO, no desafinación); la disonancia se redefine como desvío
> intencional de la inercia del impulso en curso; el snap tiene dos destinos
> (d=0 serie de f1 / |d|=1 impares de f1/2). Las secciones §A.6, §B (prioridad
> de métricas), §D, §G riesgo#1 y §H de este archivo se leen con el addendum.

> Consolidación de 5 reportes de subagentes, 2026-09-24/27. Formato denso (para recuperación).
> Tags de fuente: [R1] = Laban Movement Analysis · [R2] = sistemas movimiento→música · [R3] = matemática de suavidad/coordinación · [R4] = pitch continuo y desafinación · [R5] = interno HIT + código + diseño baseline.
> Confianza: ✅ primaria/peer-reviewed · 📊 secundaria especializada · 📰 prensa/blog · ⚠️ contestada · ❓ inferencia de diseño (requiere aprobación de Nicolás).

## A. Tesis centrales (cross-report)

1. **El modo consonancia ocupa un hueco real y documentado del espacio de diseño.** Ningún sistema publicado mapea calidad-de-movimiento → desafinación continua de una serie armónica [R2][R4]✅. Los vecinos más cercanos: OtoKin documentó el fracaso del pitch continuo desde danza ("glissando hell") y lo resolvió con anclaje discreto [R2][R4]✅; Adaptun de Sethares desafina en tiempo real pero para MINIMIZAR disonancia (dirección opuesta) [R4]✅; EyesWeb/InfoMus lleva 25 años computando descriptores de cualidad de movimiento (QoM, fluidity, impulsiveness) con validación perceptual [R2]✅. La propuesta beacon —serie fija como ancla + detuneo expresivo por consonancia— combina los dos remedios conocidos (anclaje + cualidad) en un punto no explorado [R2][R4][R5]❓.

2. **La literatura de mapeos predice que este diseño es superior al actual, y lo pide textualmente.** Hunt–Wanderley–Kirk (ICMC 2000, >4000 tests) midieron que los mapeos complejos con derivadas del gesto superan a los 1:1 y siguen mejorando con la práctica, mientras los posición=tecla se estancan y se viven como "confusing, frustrating"; su recomendación textual para la siguiente generación de instrumentos es usar derivadas del input relacionadas con la energía del performer [R2]✅ — que es exactamente la tesis de este modo. El teclado-virtual actual (bands/pads) es el piso 1:1 canónico de la taxonomía [R2]✅.

3. **"Consonancia del movimiento" tiene definición HIT rigurosa y operacionalización candidata.** HIT: consonancia = logro relacional de acople estable, `Consonance = F(ratio, constitución, medio, régimen de acople, receptor, contexto)` — no propiedad de un ratio aislado [R5]✅(manuscrito L343,L365-367). Traducción al modo: dos procesos oscilatorios (cinemática del cuerpo + campo armónico del instrumento) alcanzan acople estable con baja carga correctiva; el detuneo es el registro AUDIBLE de la carga correctiva por articulación [R5]❓. La intuición de Nicolás ("energía 100% aprovechada") es la noción del Cap.8 (recurrencia informativa → reducción de carga correctiva) y el placer visual como criterio es instancia fenoménica de H5 (sensibilidad funcional biológica a la organización consonante) [R5]✅.

4. **Coordinación = phase-locking = la misma matemática de la consonancia armónica.** Kuramoto/PLV/HKB son estructuralmente idénticos al lock de parciales armónicos [R3]✅. Las lenguas de Arnold dan la analogía operativa directa: un acople más fuerte ensancha el rango de desafinación tolerado sin perder el lock [R3]✅ — el parámetro de snap del diseño ES un ancho de lengua de Arnold [R3][R5]❓. Evidencia musical directa: el acople de balanceo corporal en cuartetos predice la "bondad" percibida de la ejecución (Chang et al. 2017 PNAS) [R3]✅.

5. **El anclaje canónico Laban legítimo NO es Effort: es Space Harmony (Choreutics).** Laban construyó su teoría espacial con metáforas musicales explícitas (escalas coreúticas ~ escalas musicales, "ley de los acordes de dirección espacial", Harmonielehre, "false position" ~ nota falsa) sobre icosaedro/octaedro/cubo de la kinesfera [R1]✅. Effort mide la INTENCIÓN interna hacia la energía (actitud), no la cinemática; su confiabilidad inter-observador es la más débil (Krippendorff α=0.46) y Flow requiere EMG (tensión muscular) que la cámara no ve [R1]✅. Consecuencia práctica: los `laban_*_proxy` de HarMoCAP son práctica estándar honesta del campo (todos los papers dicen "proxy/correlato"), y el disclaimer del schema es correcto — pero la narrativa del proyecto debería anclarse en Choreutics, no en Effort [R1]✅❓.

6. **La regla ±50% de Nicolás es psicoacústicamente certera pero necesita límite por armónico.** El tope ±f1/2 (±20 Hz en la serie de 40) cae justo sobre el pico de rugosidad de Sethares/Plomp-Levelt (≈¼ de banda crítica → Δf≈18-27 Hz para armónicos bajos-medios) [R4]✅: el recorrido afinado→máximo barre batido lento → rugosidad máxima → segregación. PERO a tope completo el parcial se segrega y se oye como OTRA nota (umbrales de segregación ~0.5-4%; ±20 Hz es 25% en h2, 3.8% en h13) [R4]✅. La banda "fusional-expresiva" es bastante menor que el tope: ±(1-4)% ≈ ±15-70 cents para armónicos medios. Recomendación: límite configurable por armónico, no global [R4]❓.

7. **La aritmética de la regla está verificada y reproduce exactamente los ejemplos de Nicolás.** `f'(n,d) = n·f1·(1 + d/(2n))`, d∈[−1,1]: n=1 → [20,60] ✓, n=2 → [60,100] ✓ [R4][R5]✅(verificado numéricamente por dos agentes independientes). Simétrico en Hz (±f1/2 siempre), asimétrico en cents (−1200/+702 en H1 a −112/+105 en H8) — consecuencia logarítmica, no bug [R5]✅. La lectura Hz-lineal mosaica el continuo perfectamente (error 0.000 Hz); la lectura en cents simétrica dejaría huecos [R4]✅. Con f1 real del shaper (40.40 Hz): ±20.2 Hz [R5]✅.

8. **El hueco de implementación es UNO SOLO y está identificado con precisión quirúrgica.** El motor de audio del shaper YA puede modular frecuencia por voz por bloque con fase continua (audio_engine.py L242, L268-270) [R5]✅, pero las voces por envolvente están fijadas a `f1·N` (state.py L385) y NO existe capability de detuneo en el contrato OSC (24 capabilities auditadas) [R5]✅. beacon.scd tiene frecuencias horneadas en el SynthDef (L98) → el detuneo debe vivir en el shaper, no en el spatializer [R5]❓(decisión). Trabajo: capability de wire + handler + store + bump de contrato + safety default + slew [R5]❓.

9. **"Suave = bello" está empíricamente contestado — la consonancia NO debe medir suavidad cruda.** En danza, perfiles de velocidad VARIADOS pero predecibles se juzgan MÁS placenteros que los uniformes (Orlandi, Cross & Orgs 2020, Cognition) [R3]✅; en arte opera la heurística del esfuerzo ("efecto Cirque du Soleil": lo difícil de reproducir gusta más) [R3]📊. La fluidez de procesamiento (Reber et al. 2004) rige acciones cotidianas, no virtuosismo [R3]✅⚠️. El constructo a medir es coordinación/eficiencia/predecibilidad, no smoothness [R3]✅ — coherente con la intuición de Nicolás (eficacia + sensualidad, no lentitud).

10. **El experimento baseline es ejecutable HOY con los repos existentes, sin escribir motor nuevo.** Video → `run_realtime.py --source video.mp4 --record` → .jsonl → script de métricas offline (~200 líneas, nuevo) → Spearman ρ contra ratings ciegos 1-7 de ≥3 evaluadores [R5]✅(comandos verificados contra parsers). Trampa documentada: el gate de replay del weaver exige escrituras `arp_*` (weaver_runtime.py L741-744) — una escena consonance sin rutas arp fallaría [R5]✅.

## B. Métricas candidatas de consonancia (síntesis R3+R5)

Las 5 candidatas de [R3]§6 y la composición de [R5]C.2 convergen. Fórmulas en unidades de torso T, ventanas causales heredadas de HarMoCAP (120/200/300 ms — NUNCA derivadas frame-a-frame [R3][R5]✅):

| # | Métrica | Qué captura | Fórmula núcleo | Mapeo a d | Patología principal |
|---|---|---|---|---|---|
| i | SPARC ventaneado por articulación | continuidad/intermitencia del gesto | arco espectral de V̂(ω) con ωc adaptativo | SPARC∈[−3.5,−1.4] → d∈[−1,1] | castiga la pausa coreográfica (que NO es disonancia) [R3]❓ |
| ii | PLV articulación vs beat_phase global | acople rítmico (el análogo directo del lock armónico) | \|⟨e^{i(φ_j−φ_B)}⟩\| ventana 6s | d = 2·PLV−1 | articulación quieta no tiene fase → gatear por amplitud; probar contra 2×beat (octava) [R3]❓ |
| iii | Estabilidad de fase relativa en pares (muñecas, tobillos, ipsilaterales) | coordinación interarticular HKB | R_jk = \|⟨e^{iφ_rel}⟩\|; S=√(−2lnR) | d = 2R−1 | transiciones de fase legítimas divergen (disonancia transitoria deseable); 2D puede falsear anti-fase [R3]✅❓ |
| iv | Continuidad de transferencia de energía (cadena cinética proximal→distal) | eficiencia balística (patada/golpe/kata) | orden de picos de ‖v_i‖² + xcorr con lag estable | combinación convexa w₁·orden+w₂·R_xcorr+w₃·suavidad | sólo aplica a gestos balísticos → gatear por régimen [R3]📊❓ |
| v | Error de predicción de modelo armónico simple por articulación | consonancia como baja sorpresa (codificación predictiva) | residuo de regresión armónica a la frecuencia del beat | normalizado | [R3]❓ |

**El discriminador freno/bomba de Nicolás** (la pieza semántica central que distingue detuneo bajo de alto) [R5]❓:
```
P_j(t) = ⟨a⃗_j(t), v⃗_j(t)⟩   (potencia mecánica firmada)
P_j < 0 → FRENADO por resistencia → d_j < 0 → detunea GRAVE
P_j > 0 fuera de fase → BOMBEO disonante → d_j > 0 → detunea AGUDO
```

**Composición propuesta** [R5]❓:
```
C_j = clip( w_P·(1−brake_j) + w_φ·PLV_j + w_s·straight_j + w_m·smooth_j , 0, 1 )
d_j = clip( k·(brake_j − pump_excess_j) + m·errφ_j , −1, +1 )
```
Los pesos w NO se fijan a priori: se calibran contra ratings humanos — ESE es el experimento baseline ("medirle la matemática" a la consonancia percibida) [R5]❓.

**Ruido a 30fps — cuantificado y verificado por dos agentes** [R3][R5]✅: 1 px de jitter → ×30 por orden de derivada sin filtrar (30 px/s vel, 900 px/s² acel, 27000 px/s³ jerk — inutilizable). Con ventanas HarMoCAP: ~0.9 px/s → 27 px/s² → 810 px/s³ (usable). En unidades de torso (σ≈0.01T): segunda diferencia frame-a-frame da ~22 T/s² de ruido vs 1-10 T/s² de señal real. LDLJ falla a SNR 45 dB; SPARC aguanta hasta 15 dB [R3]✅(Refai 2021, comparación de 32 métricas). Reglas duras: nunca derivar posición cruda; métricas sólo sobre frames OBSERVED (held da suavidad falsa [R5]✅); invalid si <70% observed en ventana [R5]❓; Nyquist 15 Hz → las métricas describen el régimen rítmico (0.5-5 Hz), no transientes balísticos [R5]❓.

**Minimum-jerk NO aplica al caso de uso** [R3]✅: el modelo de Flash & Hogan es para alcances discretos; el movimiento rítmico continuo (danza, artes marciales) no es minimum-jerk (Sternad/Schaal) — y el beacon es exactamente movimiento rítmico continuo. Consecuencia: segmentar por beat/ciclo antes de cualquier métrica de suavidad.

## C. Mapeo anatómico articulación→armónico (R5 C.1, pendiente de aprobación)

COCO-17 no tiene pelvis ni ombligo [R5]✅(schema.py L40-45). Resolución propuesta ❓: `hip_mid = (left_hip+right_hip)/2` como F0/H1 + puntos virtuales interpolados hacia `shoulder_mid` (⅓ = "bajo el ombligo" H2, ⅔ = ombligo H3). Principio: línea media sube por la serie; extremidades se ramifican por DISTALIDAD (los segmentos distales portan el contenido cinemático rápido como los parciales altos portan el detalle del timbre); pares simétricos comparten armónico (precedente: bands-v1) [R5]❓.

| Armónico | Zona | Fuente COCO-17 |
|---|---|---|
| H1 (F0) | Pelvis | `hip_mid` (virtual) |
| H2 | Bajo el ombligo | virtual ⅓ hip_mid→shoulder_mid |
| H3 | Ombligo/abdomen | virtual ⅔ |
| H4 | Hombros/esternón | `shoulder_mid` + L/R shoulder |
| H5 | Cabeza | `nose` (cluster con ojos/oídos ponderado por confianza) |
| H6 | Rodillas | L/R knee |
| H7 | Tobillos | L/R ankle (raíz de cadena cinética en AA.MM.) |
| H8 | Codos | L/R elbow |
| H9 | Muñecas | L/R wrist (máximo distal = parcial más alto) |

9 armónicos ≤ N_BANDS=32 del shaper y ≤ N_HARMONICS=32 del weaver [R5]✅. Alternativa documentada (C): cadena cinemática pura desde pelvis (rodillas=H2, tobillos=H3) — respeta el flujo suelo→pelvis→extremidades de las artes marciales pero interlea piernas y columna [R5]❓. **DECISIÓN PENDIENTE de Nicolás.**

Nota de convergencia [R1][R5]❓: la asignación por distalidad tiene eco en el anclaje Choreutics — la kinesfera se organiza por alcance desde el centro (Laban), y el "counterbalance" de tensiones espaciales es el constructo labaniano más legítimo para un escalar de consonancia [R1]✅.

## D. Regla de detuneo + snap (R4+R5, aritmética verificada)

```
f'(n,d) = n·f1·(1 + s·d/(2n))     d∈[−1,1] drive por articulación, s∈[0,1] snap global
s=0 → modo TUNED (serie exacta, d ignorado)   s=1 → modo CONTINUUM completo
```
- Límites: H1 [20,60] Hz (−1200/+702 c), H2 [60,100] (−498/+386 c), H3 [100,140] (−316/+267 c), H8 [300,340] (−112/+105 c) [R4][R5]✅ verificado numéricamente ×2.
- ±f1/2 constante en Hz = mosaico perfecto del continuo (la promesa de Nicolás "todo el continuo de frecuencias" se cumple aritméticamente) [R4]✅.
- Batido a tope: ~20 Hz contra vecino = plena zona de roughness Plomp-Levelt — el detuneo máximo suena claramente áspero, que es la intención semántica [R5]✅(citando HIT L353).
- **Riesgo de segregación**: a tope completo el parcial se oye como otra nota en armónicos medios [R4]✅ → límite configurable por armónico, calibrado contra umbral de fusión (~1-4%) [R4]❓.
- **Snap**: atracción continua proporcional (patrón Melodyne 0-100%), NO imán binario [R4]✅; deadband θ≈15-25 cents con histéresis h≈5-10 c [R5]❓; implementable SIN transforms nuevos: `gate` (threshold+hysteresis), `pad_dwell` (debounce), `slew_limiter` ya existen en el compiler del weaver [R5]✅(compiler.py L554-568, L631-643, L579-583).
- Percepción categórica (Siegel & Siegel): correcciones de decenas de cents cerca del modo afinado son imperceptibles = se sienten expresivas [R4]✅.

## E. Viabilidad de síntesis (R4)

- FM por parcial a 30-60 Hz de control: factible y barata en SuperCollider (SinOsc/DynKlang + bus de control + mapn), Csound (adsynt+tablew) y Python (acumulador de fase + interpolación por bloque) [R4]✅. 13-32 senos: costo CPU despreciable; el trabajo real es la continuidad de fase al cambiar freq por bloque [R4]❓(estándar).
- Latencia estimada OSC→audio: 45-55 ms [R4]❓ — dentro del ≤~10 ms audible... NO: por encima del umbral de Wessel & Wright para control íntimo [R2]✅. Mitigación: el detuneo es parámetro lento (no trigger percusivo), tolerante a latencia mayor que el gating [R4][R5]❓; documentar como riesgo de performance.
- El shaper YA modula freq por bloque con fase continua [R5]✅(audio_engine.py); falta el wire (ver A.8).

## F. Lecciones de sistemas para el diseño (R2)

- Criterios Wessel & Wright: "low entry fee, no ceiling on virtuosity"; latencia ≤10 ms y baja varianza; metáforas generativas [R2]✅.
- Repetibilidad (Rokeby): mismo movimiento → mismo sonido; el experimento de York muestra que los mapeos complejos se APRENDEN y mejoran con el tiempo [R2]✅ → el modo consonancia debe ser determinista (matriz fija como OtoKin) [R2]❓.
- Problema theremin extendido: sin referencia táctil, el control continuo requiere loop propioceptivo-auditivo — el oído ES el feedback [R2]✅; para un bailarín esto funciona mejor que para un thereminista porque el cuerpo entero provee la referencia [R2]❓.
- Sobrecarga del performer (Senturk): el bailarín no debe pensar consecuencias sonoras mientras baila → el mapeo debe ser aprendible por el cuerpo, no por el intelecto [R2]📊❓. Convergencia HIT: el Jpsh! como liberación de organización latente sin reescribirla [R5]✅.
- Con Moto (NIME 2026): el nivel de abstracción del mapeo configura la AGENCIA — control fino = instrumento; abstracto = partner autónomo [R2]✅. El modo consonancia, con snap y límites, se ubica deliberadamente en "instrumento tocable por el cuerpo entero" [R2][R5]❓.

## G. Riesgos y preguntas abiertas

| # | Riesgo/pregunta | Fuente | Mitigación propuesta |
|---|---|---|---|
| 1 | Segregación del parcial a detuneo completo (se oye otra nota) | [R4]✅ | límite por armónico configurable + snap; calibrar en el baseline |
| 2 | Jitter de cámara inutiliza jerk crudo | [R3][R5]✅ | ventanas HarMoCAP + filtro zero-phase; nunca derivar crudo |
| 3 | Pausa coreográfica castigada como disonancia por SPARC | [R3]❓ | detección de arrestos/exclusión; PLV gateado por amplitud |
| 4 | 2D pierde profundidad: cadena cinética hacia cámara se comprime | [R3][R5]❓ | normalizar por torso; cámara ~frontal en el corpus; preferir métricas de fase (timing) sobre amplitud |
| 5 | Gate `arp_*` del replay del weaver rompe escena consonance | [R5]✅ | relajar el gate o incluir ruta arp dummy en la escena |
| 6 | Latencia OSC→audio 45-55 ms > umbral 10 ms de control íntimo | [R2][R4] | parámetro lento, no percusivo; medir en vivo; documentar |
| 7 | Flow/Weight Laban no medibles desde cámara (requieren EMG) | [R1]✅ | NO llamar "Laban" a los proxies; anclarse en Choreutics + eficiencia |
| 8 | "Suave=bello" contestado: virtuosismo incluye explosividad | [R3]✅⚠️ | consonancia = coordinación+predecibilidad+eficiencia, no suavidad cruda |
| 9 | ¿hip_mid como F0 o cadena cinemática pura (tobillos bajos)? | [R5]❓ | DECISIÓN DE NICOLÁS |
| 10 | Peso relativo de los 5 términos de C_j | [R3][R5]❓ | el baseline existe precisamente para calibrarlos contra ratings humanos |
| 11 | Rubato/tempo no estacionario desancla el PLV | [R3]❓ | ventana 6s = la del estimador de tempo; gatear por tempo_conf |
| 12 | Cuerpo quieto → tempo invalid → PLV indefinida | [R5]✅ | excluir tramos; congelar d anterior |

## H. Checklist de decisiones pendientes (todas de Nicolás)

- [ ] Tabla C.1 de mapeo anatómico (hip_mid=F0 + distalidad vs cadena cinemática) [R5]❓
- [ ] Límite de detuneo: global ±f1/2 vs por-armónico calibrado a umbral de fusión [R4]❓
- [ ] Snap: valor inicial de s y deadband θ [R4][R5]❓
- [ ] Composición de C_j y d_j: ¿P_j firmada entra con signo propio o modula el bombeo? [R5]❓
- [ ] Corpus del baseline: quiénes performan (¿la bailarina/artista marcial son de la tribu? rope-flow de Nicolás ya está nominado como candidato consonante [R5]✅HIT-L900) y consentimiento [R5]❓
- [ ] Destino del detuneo: shaper confirmado, beacon-spatial descartado (freq horneadas) [R5]❓
