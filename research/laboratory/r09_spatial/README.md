# R09 · Observaciones espaciales y sincronización

Primer corte: `spatial_observations.py` define streams con dimensión, marco,
unidades, proveedor, slot de sujeto, calibración y reloj originales explícitos.
Mapeo de reloj afín t_común=offset+rate*t_fuente, incertidumbre no negativa y
método declarado. Sincronización medida exige referencia de evidencia; esto no
verifica por sí mismo la evidencia ni convierte una suposición en medición.

Pose de imagen es 2D normalizada; profundidad monocular debe permanecer inferred.
Metros y multivista requieren ID de calibración; el contrato no prueba exactitud
ni resuelve extrínsecos. Missing conserva causa y no admite posición/confianza.
Gaps permanecen gaps; no interpolación, identidad biométrica ni escala inventadas.

Validación: dos tests pasaron (0,13 s), con reloj afín, roundtrip, gaps/missing y
rechazo de coordenadas no finitas, dimensión incorrecta, profundidad presentada
como observada, escala sin calibración y sincronización medida sin evidencia.

Pendientes: adaptador de HarMoCAP 2D, importación configurable/API/UI, evaluación
de ambigüedades con clips, calibraciones realmente verificadas, multivista y
proveedores monoculares. No se instalaron modelos, compraron sensores ni
reconstruyeron videos privados. Este contrato no es un benchmark 3D ni evidencia
sobre HIT. Comparar cámaras/IMUs requiere medir sincronización, escala, deriva y
error contra referencia independiente; reproyección baja no demuestra profundidad.

## Corte 2 · Adaptador de observaciones existentes

`spatial_adapter.convert` recibe MotionFrames congelados, person_id explícito y
Clock. Mantiene camera_isotropic/frame_height (x puede superar 1 por aspect);
no los normaliza como [0,1] ni estima profundidad/metros. Conserva sequence/time,
confianza soportada y held como held. Produce 17 etiquetas; missing borra posición
residual y distingue persona ausente, articulación no presente y missing de origen.
No selecciona otra persona ni transfiere calibración. Fuente/stream, geometría,
unidades/dimensión y timestamp_origin deben ser homogéneos; gaps no se rellenan.

Cuatro tests contrato/adaptador pasaron (0,14 s): unidades reales, held/missing,
slot ausente, gaps, repetición sin mutación y rechazo de fuentes/geometrías/relojes
mezclados o 3D. Fixtures sintéticos del contrato, no tracking privado nuevo.
Pendiente API/UI/importación/persistencia y validación de clocks/cámaras reales.

## Corte 3 · API de conversión/validación

POST `/api/research/r09/convert` recibe el Request del adaptador y devuelve inputs,
stream espacial, cobertura por observed/held/inferred/missing y tiempos comunes
calculados con el reloj declarado. Verifica resultado finito. POST
`/api/research/r09/validate` valida un Stream externo y devuelve
`validation: contract_only`: no autentica source, calibración ni sincronización.
Ambas rutas son stateless y no crean un archivo de datos corporales ni cambian live.

Cinco tests contrato/adaptador/HTTP pasaron (0,75 s): cobertura exacta, clocks,
roundtrip y rechazo de slot booleano, reloj inválido, paths extras y metros
incompatibles. Pendiente UI/importación por fuente autorizada, persistencia
reproducible y medición real de calibraciones/relojes. Validación de esquema no
presenta observaciones monoculares como reconstrucción 3D verificada.
