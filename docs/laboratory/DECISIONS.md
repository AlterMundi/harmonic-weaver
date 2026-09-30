# Decisiones vigentes — laboratorio corporal

2026-09-29. Estas decisiones posteriores prevalecen sobre propuestas anteriores.

1. Primera etapa: exploración en tiempo real local, archivo/cámara, controles y
   ruteos modificables durante reproducción. La investigación no exige exportar.
2. Cache persistente de tracking junto al video o biblioteca. Content hash,
   extractor, pesos y parámetros determinan validez; reprocesamiento forzado.
   Cambiar sonido o filtros posteriores no reinfiere pose.
3. Presets portables: independientes de fuente, calibración e historia.
4. Seis voces iniciales. Componentes PCA/SVD y voces son cantidades independientes.
5. Preservar la suma polifónica, no el aspecto viejo del visualizador. Rediseñar
   para precisión y legibilidad; todos los armónicos activos participan.
6. Centros de despliegue variables, eventos múltiples, no un core obligatorio.
   Los candidatos cinemáticos no prueban intención, causalidad ni eficiencia.
7. Interferencia: distinguir oposición, refuerzo y variación; mapeo sonoro editable.
8. Bitácora ligera automática. Cámara/tracking/audio sin registro por defecto.
   El tracking de archivos solicitado sí se persiste como cache.
9. Segundo milestone: presets × fuentes, evaluación reproducible y publicación.
10. Agenda R01–R13 conserva teoría, cuerda/3D, medios físicos, experiencia,
    OpenBCI/SNR, corazón, energía/trabajo y transferencia. No se implementan
    sensores ni inferencias fisiológicas por anticipado.
11. Tareas separadas por contratos para colaboración paralela; no asignar ni
    contactar personas automáticamente.

El plan largo conserva antecedentes; consultar este registro y la agenda al
convertirlos en tareas. No heredar el viejo orden que posponía organización
colectiva fuera del primer milestone.

12. Segunda iteración: el comparador usa el runtime live con reloj lógico,
    ejecución separada y solicitudes congeladas. Métricas descriptivas sobre
    soporte común; sin PCM ni afirmación de eficacia/predicción. Ver EVALUATION.
13. No sobrescribir presets por su nombre: el 01c guardado puede haber sido
    editado. Referencias nuevas tienen IDs nuevos; la configuración local actual
    se conserva. Ajustar controles compatibles preserva historia de ruteo.
14. CPU es recuperación explícita. El cache distingue dispositivo efectivo;
    fallar/cancelar una generación no borra la anterior válida. CUDA sigue bajo
    investigación; cambiar a CPU no prueba resuelta su causa.
15. El aporte independiente de Oliva (#36, para #35) se revisa y contrasta sin
    modificar su territorio ni hacer merges automáticos. Incorporar precauciones
    de cobertura/causalidad no equivale a validar las hipótesis de HIT.

16. La selección explícita de cuerpo en video es una preferencia local ligada a
    media hash, clave de cache y generación; no viaja en presets ni restaura
    calibración. Sin elección guardada, seleccionar mayor cobertura observada
    o primero de la lista, configurable en Fuente; reproducción automática
    configurable cuando el cache está listo. Una generación nueva elige su
    propio default; la ausencia del cuerpo elegido nunca selecciona otro.
