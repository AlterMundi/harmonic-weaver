Una sesión debe poder jugar con el instrumento sin CLI ni edición de código después del arranque. La UI permite usar cámara o dejar un video en loop, variar controles/ruteos y guardar una configuración interesante.

## Implementación

- React/TypeScript en web/lab, servicio FastAPI del laboratorio. Partir de fixtures de LAB-01; integrar LAB-02/03/04 cuando estén disponibles. No esperar a terminar algoritmos avanzados para entregar una pantalla usable.
- Video/esqueleto, figura polifónica, controles y señales explicativas con un transporte común. Modo Operar y modo Performance; segunda ventana local comparte sesión con revisiones.
- Biblioteca de presets: guardar como, duplicar/favoritos, importar/exportar, comparar/restaurar y undo. No exigir generar un experimento ni grabar una toma.
- Controles desde AlgorithmDescriptor con unidades/defaults/ayuda y valor pedido/aplicado. Modelo, ventanas, joints/cadenas, referencias, parámetros de sonido y proyección visual accesibles.
- Matriz fuente→destino con mezcla/curvas y macros asignables. Inspector permite entender de dónde sale una señal y qué voz controla. Bypass, mute/solo claros y reversibles.
- Estado de cache/progreso/reprocesar, persona/cámara, dimensiones correctas y tracking perdido. Calidad avanzada disponible sin saturar la pantalla principal.
- Marca voluntaria «se siente bien» y guardado rápido. Grabación se integra después como acción opcional, no botón obligatorio del flujo.

## Aceptación

End-to-end: abrir archivo, loop, cambiar controles en vivo, guardar preset, reiniciar, abrir otra fuente y reaplicar. Dos clientes no pisan cambios silenciosamente. Navegación por teclado, labels y errores legibles; ninguna acción que parece aplicada queda pendiente sin indicación.

No implementar matemática en el navegador salvo representación visual: cliente consume contratos. No hardcodear tres componentes como tres voces ni suponer que un widget nuevo requiere un endpoint dedicado.
