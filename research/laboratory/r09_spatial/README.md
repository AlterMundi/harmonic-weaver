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
