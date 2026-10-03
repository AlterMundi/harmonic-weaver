# R12 · Mediciones, tarea y eficiencia: protocolo inicial

Fecha: 2026-10-02. Issue #26. Software descriptivo implementado; no mediciones
humanas realizadas, ni una demostración de eficiencia/HIT. Esta línea no impone
un protocolo al instrumento cotidiano. Evaluación siempre opcional.

## Qué podemos medir y qué hace falta

| Variable/pregunta | Entrada/sensor o método | Unidad | Incertidumbre/dependencia | Estado software |
| --- | --- | --- | --- | --- |
| Frecuencia cardíaca durante un intento | Exportación de dispositivo con timestamps; futuro adapter BLE Heart Rate Service | bpm | Contacto/calidad, método de estimación y reloj; latencia propia. No determina calorías o trabajo | Import declarado, cobertura y media temporal; sin adquisición BLE |
| Resultado útil de la tarea | Objetivo acordado antes de comparar: ciclos válidos, tiempo o error, con método de conteo explícito | Declarada por tarea | Criterio de éxito, anotación independiente, variabilidad | Outcome separado por intento; no ranking automático |
| Trabajo mecánico externo de un sistema definido | Potencia externa medida y calibrada, o fuerzas y velocidades métricas en puntos de aplicación | W → J | Instrumentación, ejes, escala, definición de sistema y calibración. Pose2D no sustituye fuerzas | Import de potencia declarada, integración sólo en soporte válido |
| Energía metabólica | Medición apropiada de intercambio gaseoso y protocolo/estimador documentado; importar potencia derivada externamente | W → J | Instrumentación y competencia experimental; baseline/ventana/estado fisiológico importan | Import de potencia declarada y calibración; no estimator desde HR ni pose |
| Esfuerzo/fatiga percibidos | Autoinforme con escala y pregunta fijadas | dimensionless | Método, momento, participante; no sustituye fisiología | Canal reported_effort; promedio no es escala clínica ni umbral |
| Error de tarea | Método de error explícito y normalización documentada | dimensionless | Es específico de tarea; no implica patología o eficacia general | Canal task_error, sin convertirlo a energía |
| Preferencia/agencia/experiencia | Protocolo R10, marcas R03 y respuestas independientes | Escala declarada | Participantes y aceptación/escucha reales pendientes | Mantener separadas de mediciones R12 |

La definición física de potencia como F·v corresponde a fuerza y velocidad del
punto de aplicación; no a aceleración/velocidad aparentes de pose monocular.
[OpenStax, University Physics 7.4](https://openstax.org/books/university-physics-volume-1/pages/7-4-power).

Bluetooth Heart Rate Service declara frecuencia cardíaca, contacto opcional y
campos opcionales de RR/energía: el transporte no demuestra por sí mismo la calidad
de una estimación energética. Este banco sólo acepta HR como bpm y no convierte
ese canal a calorías. [Bluetooth SIG HRS1.0](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/HRS_v1.0/out/en/index-en.html).

Un estudio experimental de ciclismo compara definiciones de eficiencia mecánica
con potencia externa e intercambio gaseoso. Sirve como antecedente metodológico:
las definiciones y baselines importan. No transfiere resultados a rope-flow.
[Matomäki et al., 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6557926/).

## Experimento pequeño vinculado a EVAL, todavía por realizar con datos humanos

1. Acordar dentro de una persona una tarea, restricciones y resultado útil. Fijar
   fuente/slot, ventanas, orden de condiciones y criterio de exclusión antes de
   leer resultados. No asumir equivalencia entre cuerpos ni transferencia.
2. Congelar presets y segmentos en EVAL. Para feedback prospectivo registrar
   intentos nuevos; transformar un video viejo no cambia retrospectivamente su
   respuesta fisiológica. Replays musicales permiten explorar percepción, no
   efectos físicos de feedback que nunca recibió la persona.
3. Registrar mediciones con timestamps originales, proveedor, contacto/artefactos,
   unidades, calibración/incertidumbre y digest del archivo raw si existe. Exportar
   JSON nativo R12; no inventar samples para el video privado disponible.
4. Declarar transformación afín hacia source_time_s de la evaluación y evidencia
   de sincronización. La incertidumbre permanece explícita; repetir análisis con
   offsets plausibles como sensibilidad, sin presentar alineación asumida como
   sincronización medida. R09 conserva herramientas de clocks/anchors.
5. Vincular hash del manifest de EVAL, índice de corrida y slot. El servidor
   rechaza otro hash/slot y ventanas fuera del segmento. La relación temporal y
   la atribución sensor→slot siguen siendo declaraciones que hay que verificar.
6. Elegir canales para soporte común y gap máximo. Comparar medias, cobertura,
   causas y resultado útil. No interpretar como eficiencia una media de HR menor
   si cambió tarea/resultado/ventana; reportar nulos y pérdidas como evidencia.
7. Guardar request/result/manifest y verificación. Separar descriptivos por intento
   de hipótesis, inferencia causal y aceptación humana. Para costo metabólico o
   trabajo real, incorporar las mediciones de la tabla antes de afirmarlos.

## Semántica implementada

Request versionado: provider synthetic/declared_import, source_id, subject_slot,
task/constraints, clock original→común, canales, samples indexados, trials, gap y
common_channel_ids. Cada null tiene causa. Exclusiones conservan valor raw y causa.
Potencia exige unidades W y evidencia declarada de medición/calibración. Esfuerzo
firmado/dimensionless y trabajo mecánico firmado no se convierten a energía
metabólica ni se recortan silenciosamente a positivo.

Estimador **offline**: interpolación lineal/trapecios sólo entre muestras
adyacentes soportadas, sin extrapolación en extremos. Un salto de índice o gap
mayor que max_gap_s excluye todo ese intervalo; null/exclusión en cualquiera de
sus extremos excluye ese canal. Gap está definido en segundos del reloj de origen.
Ventanas de trials están en segundos del reloj común; la transformación afín
escala duraciones. Los intervalos se recortan al trial. Cobertura, duración válida,
media, hash del soporte y causas se publican. Extremos de trial fuera del stream
aparecen como duración sin soporte, no como ceros. En el agregado se prioriza
index_gap, luego time_gap, luego causa missing/excluded del primer extremo que
la declare; todas las causas originales permanecen en request.

La media común usa la intersección de canales seleccionados y, para cada canal
adicional, su propio soporte. Los seleccionados comparten exactamente intervalo;
canales no seleccionados pueden tener soporte menor. Trials distintos no quedan
pareados por comparar sus medias. Integral en J sólo para W y sólo en intervalos
válidos: una integral parcial no es energía/trabajo total del intento. No calcula
ratios de eficiencia, calorías, fatiga, HRV ni correlaciones con pose/sonido.

Manifests contienen inputs/output/code/environment y límites. Lectura de código
actual recomputa; histórica sólo verifica integridad y vínculo al request, sin
validar resultado contra algoritmos actuales. Hashes no son custodia firmada ni
verificación de hardware. El vínculo EVAL se comprueba al inspeccionar/guardar;
un registro archivado no afirma que el video sigue disponible/inalterado hoy.

Configuración portable sólo guarda gap y selección de canales; no transfiere
cuerpo, reloj, muestras, calibración o ventanas. IDs de canales deben existir en
la nueva entrada; errores no se remapean silenciosamente. El protocolo/observaciones
JSON completo se importa/exporta aparte. No cambia instrumento, presets o R24.

## Dependencias siguientes explícitas

- Una exportación real de sensor, inventario de dispositivo/método/contacto y
  correspondencia consentida con slot; no disponible en esta validación.
- Evidencia de reloj/sincronización y error; BLE adapter/collector, RR y sensores
  adicionales no implementados aquí. Este software no mide HR desde cámara.
- Para mecánica: sistema definido, escala métrica y fuerzas/potencia externa.
- Para metabolismo: equipo/protocolo competente y estimator documentado externo.
- Diseño de intentos nuevos para intervención, outcome y participantes; después
  integrar R10/R13 sin confundir preferencia con costo/eficiencia.
- Evaluación científica formal, sensibilidad preespecificada y métodos de
  emparejamiento entre intentos. No quedan resueltos por este corte descriptivo.
