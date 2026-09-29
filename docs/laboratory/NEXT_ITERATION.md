# Próxima iteración: instrumento y contraste independiente

2026-09-29. Goals preparados para iniciar en próximas sesiones; esta nota no
declara iniciada su ejecución ni asigna trabajo automáticamente a otra persona.
Programa #7; continuidad de LAB-08, EVAL #18 y agenda R01–R13.

## Estado que debe preservarse

Base revisada: Weaver feat/laboratory-live, commit 0b9766a (PR #30, sobre #29);
Shaper feat/laboratory-telemetry, 8d6de86 (PR #2); HarMoCAP baseline PR #1.
Verificar los heads al empezar. Main todavía no contiene necesariamente todo.
Worktrees originales con cambios de Nicolás quedan intactos.

Nicolás aceptó la sensación de 01c, armónicos sostenidos con intensidad corporal,
y luego la del contraste temporal. No aceptó compresión que eleva todo el audio.
Realce -1..10: 0 neutral, 1 máximo previo, 10 énfasis diez veces mayor antes del
límite. Articulación 0..1 mezcla sostenido con transientes derivados de subidas;
su escucha específica aún no fue confirmada. Seis voces, afinación/ratios estables,
fases continuas. Priorizar controles existentes y explicar los defaults cambiados.

R24 por JACK; launcher documentado en RUNNING. Video local 60 s de 10:00–11:00,
tracking CPU completo, 1.800 cuadros. Ambas muñecas aún tienen pérdidas (8–10%);
confianza no acredita exactitud. Tramo 20:00–21:00 rechazado por oclusión de planta.
Todos los medios, derivados, cache y anotaciones identificables permanecen locales.
CUDA volvió a fallar también en extracción inicial: #31. Modelos no baseline
necesitan calibración, aviso añadido; aceptación auditiva pendiente: #32.

## Lectura de Sai: integrar con alcance

Revisión dirigida de SairaAsua/movimiento-armonico-investigacion, HEAD
f6b96da041bbe95e35ab865d2a07d082d2adba29. Se leyeron índices/síntesis, contratos Q/C,
causalidad, cobertura, marcos, fase y auditorías de integración relevantes.
No se afirma lectura integral de todas las fuentes primarias ni del repositorio.

Fuentes fijadas:
- [Control factorial y marginales](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/LABAN_HIT_FACTORIAL.md).
- [Predicción sin fugas](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/HIT_PREDICCION_SIN_FUGAS.md).
- [Geometría y tiempo](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/GEOMETRIA_VS_TIEMPO_TRAYECTORIA.md).
- [Cobertura y selección](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/COBERTURA_SELECCION_VIDEO.md).
- [Marcos corporales](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/CMU_MARCOS_C_CONTRASTE.md).
- [Contrato Q](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/CONTRATO_Q_LIVE_V0.md)
  y [contrato C](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/CONTRATO_C_LIVE_V0.md).
- [Auditoría histórica de Weaver](https://github.com/SairaAsua/movimiento-armonico-investigacion/blob/f6b96da041bbe95e35ab865d2a07d082d2adba29/research/WEAVER_DRIVER_PRUEBA_AISLADA.md).

Aportes inmediatos: cobertura por señal y duración de gaps, razones de invalidez,
definición de marco/recorrido, separación entre tiempo fuente y disponibilidad,
controles sintéticos y comparaciones sobre exactamente el mismo soporte temporal.
Held o inválido no significa disonancia; una transición puede no admitir fase.
Parte ya existe en nuestros contratos/reset/lease: ampliar pruebas y diagnóstico,
no reemplazar el runtime por la arquitectura histórica de Beacon.

Aportes para banco: recorridos iguales con ritmos distintos; ritmo común frente a
acople; marginales igualados; observaciones segmentarias independientes; prueba
de prefijo causal y reserva por sesión. Un descriptor determinista de entradas
no agrega información sensorial: puede mejorar representación/modelado.
No confundir el R de concentración de fase de Sai con I/R/A de Anni.

Q resume componentes direccionales ponderadas por arco: no es un plano ni un
subespacio Grassmanniano. Puente propuesto por nosotros: comparar tensor completo
de direcciones, sus subespacios y sus diagonales Q, con casos degenerados y marcos
controlados. Es una línea de investigación, no equivalencia ya demostrada.
C depende del recorrido/marco; Sai documenta incluso inversión de signo.

Diferir: Q/C corporales 3D sobre video monocular, soga inferida desde muñecas,
metabolismo/eficiencia y resultados de paper. Las propuestas de Sai no validan
HIT ni una identidad cuerpo→cimática. No importar sus ganancias de bandas Beacon
como si fueran frecuencias de osciladores Shaper.
La auditoría de Sai usa Weaver a4ca91e3 y HarMoCAP bdeebbf5: reproducir antes de
declarar un bug vigente. En particular, distingue fallo del receptor de ejemplo
HarMoCAP de un driver Weaver que sí superó ese control.

Reproducción local independiente: cinco scripts, todos exit 0, Python estándar:
laban_hit_marginales_igualados.py (R=1 frente a 0.077246, fase de eventos R=1 en ambos);
prediccion_relacional_sintetica.py (ventaja frente a lineal pero no frente a la
base no lineal adecuada; guard de futuro y soporte desigual);
geometria_tiempo_sintetica.py (tiempo 0.5/0.32461, arco ~0.5 en ambos);
proyeccion_2d_ambigua.py (misma imagen, recorridos 3D 2.513266/5.690778);
fase_causal_sintetica.py (error -36 grados en aceleración, warmup/expired).
No se reprodujo el banco CMU completo ni se validaron cámaras/estética.

## Goal CompAII: segunda iteración local

Entregar una segunda iteración usable del laboratorio y un primer comparador
reproducible, manteniendo la exploración libre como operación principal.

1. Preservar estado/presets y una referencia explícita de 01c aceptada. Completar
   aceptación de realce/transientes con pruebas de continuidad y controles A/B
   sobre misma fuente, posición y nivel. Corregir el residual de pitch/fase
   saturado como opción separada, nunca reactivarlo en 01c sin elección humana.
2. Hacer legible por qué un modelo suena o no: falta calibración, calentamiento,
   tracking insuficiente, señal no aplicable, mapeo silenciado o audio desconectado.
   Resolver #32 con recorrido de calibración sencillo y prueba de cada modelo.
   No inventar escala ni reutilizar la de otro cuerpo/fuente silenciosamente.
3. Incorporar diagnóstico temporal de cobertura por articulación/señal, gaps y
   segmentos descartados; conservar el registro de intentos. No seleccionar por
   movimiento visual solamente ni presentar confianza como precisión.
   Robustecer #31 con recuperación explícita y reproducible, identidad de cache
   por backend y preservación de generaciones válidas. No repetir GPU fallida sin
   diagnóstico; CPU es una alternativa utilizable.
4. Primer corte de EVAL #18: presets congelados × segmentos de cache, usando el
   mismo núcleo causal live, reloj determinista, resets/preroll explícitos,
   manifest con hashes/versiones/calibración/semillas y comparación sobre soporte
   común. Exportar inicialmente features/targets/métricas/manifest; separar esta
   entrega de PCM offline, figuras renderizadas y evaluación formal restantes.
   Incluir pruebas de paridad live/replay a tiempos equivalentes y rerun.
5. Revisar la PR de Oliva como consumidor, incorporar casos pertinentes sólo
   después de revisar definiciones y resultados. No bloquear el laboratorio si
   ese aporte todavía no existe.

Aceptación: un comando de arranque; mismo preset entre fuentes; explicación
visible de silencios; sesión local de 60 s con seis voces y sin reataques por
actualización; pruebas de resets/cache/audio/UI pertinentes; corrida repetible
de dos presets × dos fuentes sintéticas o locales con manifest y límites.
La escucha humana se informa sólo cuando Nicolás la realiza.
Publicar ramas/PRs y evidencia; no merge automático ni publicar medios privados.

Propiedad de cambios: runtime, UI, routing/presets, store/contracts, percepción/
cache e integración Shaper; comparador bajo src/harmonic_weaver/lab/evaluation/
y tests de integración. Durante trabajo paralelo no editar los directorios
reservados a Oliva abajo. Cambios en contratos se versionan con compatibilidad.
Grabación opcional #17, PCM offline completo, sensores/3D, paper y agenda restante
siguen pendientes explícitos, no se pierden ni bloquean este corte.

## Goal Oliva: banco independiente de contraste

Preparar y publicar un banco reproducible para contrastar organización espacial
y temporal, cruzando Sai con Anni/HIT y nuestros modelos actuales. Entregar código,
fixtures, pruebas y un informe; no sólo otra revisión bibliográfica.

Partir del head de PR #30 en rama/worktree propio. Leer SPEC, DECISIONS, VALIDATION,
AGENDA, propuestas originales de Anni y esta nota. Fijar SHA de Sai y de Weaver.
No necesitar videos privados ni nuevos sensores; usar datos sintéticos. Datos
públicos externos, si se agregan, deben tener procedencia y términos verificados.

1. Reproducir los cinco bancos listados y registrar comandos/resultados/versiones.
   Adaptar mediante implementación atribuida o fixtures con procedencia; revisar
   términos antes de redistribuir código ajeno. No copiar el repo completo.
2. Producir pares controlados: misma geometría/distinto ritmo; mismo movimiento
   marginal/distinta relación; fase compartida artificial; ritmo común sin acople;
   traslación/rotación/marco móvil; ruido/gaps/identidad/seek; plano degenerado.
   Ground truth 3D sintético separado de observación 2D; nunca levantar z=0 y
   presentarlo como reconstrucción corporal. No asumir máximo R = mejor gesto.
3. Emitir MotionFrame 2D compatibles con contratos existentes y un manifest de
   verdad sintética separado. Ejecutar local/relational/angular/collective por
   adaptadores de sólo lectura. Comparar señales y validez antes del audio.
   Distinguir concentración de fase de Sai, I/R/A de Anni, subespacios y Q.
4. Comprobar prefijo causal, soporte idéntico, disponibilidad, unidades, precisión
   numérica declarada y reproducibilidad. Comparar predicción contra persistencia/
   velocidad constante y una base no lineal apropiada cuando se afirme utilidad
   relacional; evitar ventajas producidas por selección o capacidad desigual.
5. Entregar matriz de resultados/contraejemplos: qué distingue cada descriptor,
   qué confunde, qué no puede medir esta captura. Proponer después un puente
   tensor direccional/subespacio/Q, sin imponerlo como nuevo algoritmo live.

Fronteras exclusivas: research/laboratory/sai_bridge/ y
tests/research/test_sai_bridge_*.py. Dentro pueden vivir generadores, fixtures
pequeños, adaptadores, manifest y README con comando único. No editar runtime,
modelos productivos, contratos, presets, UI, cache, launcher, Shaper ni HarMoCAP.
Importar APIs existentes sin cambiarlas; si falta algo, documentar propuesta de
interfaz o bug con reproducción, sin ampliar scope unilateralmente.

Aceptación: un comando genera resultados deterministas; fixtures validadas con
contratos fijados; al menos un control negativo y un contraejemplo informativo;
tests de causalidad/missingness; informe separa esperado, observado, límite y
propuesta. PR revisable contra base declarada, sin datos privados ni afirmación
de validación humana/HIT. No depende del comparador que CompAII aún construirá.
