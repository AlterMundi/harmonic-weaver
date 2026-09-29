Añadir Grabar/detener sin convertirlo en un paso obligatorio. Presets y exploración siguen funcionando sin grabación. Esta issue no bloquea las primeras sesiones de LAB-08.

## Trabajo

- Guardar video fuente + audio final escuchado, con opción de composición del Lissajous. Alinear timestamps de captura y sample clock; indicar offset/latencia y frames faltantes.
- Usar tap después del limitador si se promete identidad con audio emitido. El tap actual de Shaper es anterior: resolver la diferencia, no renombrarlo.
- Guardar preset inicial, calibración, eventos de cambios, marcas y versiones. Una sesión modificada no se reproduce a partir del preset final solamente.
- Writer/codificador fuera del callback, buffers acotados, límites/progreso/cancelación y errores de disco visibles. No bloquear interpretación ni audio al exportar.
- No grabar automáticamente cámara ni habilitar buffer retrospectivo oculto. «Guardar últimos segundos» queda fuera hasta implementarlo como opción explícita.

## Aceptación

Clip con cambios de configuración conserva audio y eventos correctos; cierre normal/anticipado produce un archivo interpretable o un error explícito. Disco lleno/cancelación no detiene el instrumento. Verificar sincronía con estímulo de prueba, no únicamente duración igual.

Documentar formato/exportación y dependencias opcionales. Mantener datos personales fuera de git; el paquete reproducible público se prepara con selección explícita posterior.
