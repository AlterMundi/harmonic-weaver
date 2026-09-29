Agenda: **R08, R09**. Estado: investigación futura preservada; no implementación comprometida en v1.

La pose corporal sola no describe todo rope-flow. Investigar máscara/curva de cuerda, extremos y propagación con anotación asistida y validación manual de fragmentos. Blur, cruces y oclusiones pueden volver el dato no identificable; un cruce en imagen no es un nudo 3D.

Benchmark acotado de 3D monocular (GVHMR y candidato disponible reciente) sobre giros, pies/manos y oclusiones. Marcar inferido; reproyección baja no demuestra profundidad correcta. No instalar modelos grandes sin prueba de viabilidad local.

Elegir cámaras multivista sincronizadas y calibradas después de identificar ambigüedades reales. Evaluar IMUs si resuelven movimiento no observado; documentar deriva/alineación. Mantener la misma interfaz de frames con dimensión, marco, escala y calidad explícitos.

Entregable inicial: clips de dificultad, calidad anotada y decisión basada en evidencia sobre sensores. Compras/instalación se planifican como etapa posterior; no condicionan v1 a disponer de 3D.

Registrar hallazgos como notas fechadas enlazadas a esta issue y a la agenda. No sobrescribir fuentes ni convertir preguntas en afirmaciones demostradas.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Agenda de investigación abierta; no bloquea v1 salvo dependencias explícitas.

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:RES-CAPTURE -->
