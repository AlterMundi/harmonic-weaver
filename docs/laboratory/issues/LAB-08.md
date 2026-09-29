Entregar un launcher y recorrido cotidiano completo que Nicolás pueda explorar. La aceptación incluye feedback humano, no solo que los tests pasen.

## Integración

- start-laboratory.sh inicia/supervisa solo servicios necesarios; localhost por defecto y salida de audio seleccionable. Puertos ocupados fallan claramente sin matar procesos ajenos.
- Preservar el launcher aislado previo. No iniciar MIDI/ECG/espacializador ni auto-captura por herencia de start-live-stack.
- Conectar transporte, caches, algoritmos, controles y voz/figura. Telemetría de estado operativo y errores recuperables.
- Video con tracking cacheado responde a controles sin reinferir ni render previo. Cámara fresca bajo sobrecarga, sin buffer creciente.
- Configuración estructural se prepara sin frenar audio; CPU/GPU/trabajos de UI no comparten el callback sonoro.

## Medición

Registrar p50/p95 y jitter para control→audio, captura→audio y audio→visual por separado. Metas iniciales <50 ms y <100 ms respectivamente donde corresponda; comprobar límites del host, no inferir latencia de FPS. Si se usa loopback físico para medición, documentar método. Reducir costo visual/percepción con estado visible antes de acumular cuadros atrasados.

## Sesión de aceptación

Abrir video y cámara, ajustar ventanas/modelos/ruteos/macro, observar seis voces, marcar hallazgo, guardar, reiniciar y reaplicar sobre otra toma. Capturar notas voluntarias de placer, legibilidad y confusión; registrar presets/versiones sin filmar automáticamente. Sesión de al menos 10 minutos para detectar deriva/backlog, además de smoke tests.

Pruebas end-to-end de UI, missingness, seek/loop, cambio de fuente/persona, reconexión y cierre sin voces colgadas. Publicar qué fue automatizado, escuchado y aún pendiente. La aceptación de instrumento no es demostración de HIT ni eficiencia.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10), [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11), [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12), [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13), [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14), [LAB-07 · #15](https://github.com/AlterMundi/harmonic-weaver/issues/15).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-08 -->
