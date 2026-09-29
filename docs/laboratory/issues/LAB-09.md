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

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10), [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11), [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12), [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-09 -->
