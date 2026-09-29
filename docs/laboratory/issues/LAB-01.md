Crear la base que comparten runtime, UI, algoritmos y evaluación futura. Preset guarda configuración, no un instante de una toma. Debe poder aplicarse a otro video o cámara sin heredar identidad, historia de derivadas, PCA ni buffers.

## Entradas y responsabilidad

Revisar StageServer/WeaverEngine, ValueEnvelope/EventRecord y escenas declarativas existentes. Trabajar en el paquete lab propuesto; no duplicar la lógica de revisión/validación si puede reutilizarse. El servidor sigue siendo autoridad. Publicar fixtures pequeños antes de integrar consumidores.

## Implementación

- Definir MotionFrame, FeatureFrame, AlgorithmDescriptor, Preset, Calibration, SessionState, SessionEvent y VoiceFrame conforme a SPEC §4. Esquemas versionados para persistencia; unidades, marco, validez y temporalidad explícitos.
- Presets nombrados: guardar/guardar como, duplicar, favoritos, importar/exportar, defaults resueltos y versiones de plugins. Rechazar versiones no soportadas sin reemplazarlas tácitamente.
- Separar calibración y sesión. Fijar política visible para recalibrar una nueva fuente o seleccionar calibración existente.
- Ediciones atómicas con revisión base; informar conflictos de dos clientes. Undo/redo guarda configuración, no muestras corporales.
- Bitácora ligera de cambios, preset IDs y marcas voluntarias. No grabar tracking/audio/video de cámara. La cache de archivos es persistencia solicitada independiente.
- HTTP para recursos/snapshot y WebSocket para eventos; clientes lentos reciben estado reciente sin bloquear productores.

## Pruebas / salida

Roundtrip de preset completo, reapertura tras reiniciar servidor, importación inválida, conflicto de revisión, independencia de fuente y calibración. Un cambio rechazado deja activa la versión previa. Fixture de seis voces consumible por UI y renderer; número de componentes del análisis independiente.

Entregar registro de operaciones y ejemplos suficientes para LAB-02 a LAB-07. Mantener el protocolo actual y el launcher antiguo operativos; esta tarea no implementa percepción, DSP, algoritmos ni estética.
