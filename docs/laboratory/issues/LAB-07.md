Incluir desde v1 una operacionalización exploratoria de organización colectiva y Jpsh!, sin imponer core único. Debe admitir varios centros/eventos o ninguno y distinguir contribución nueva de evaluación posterior de su propagación.

## Implementación inicial

- PCA/SVD causal de velocidades normalizadas, ventana inicial 2 s y hasta tres componentes editables. Features/soporte/unidades declarados. Seis voces iniciales independientes de rango PCA.
- Base calculada solo con pasado; evaluar muestra nueva antes de incorporarla. Alinear bases entre ventanas, manejar degeneraciones y cambios de soporte. No llenar missingness con cero ni comparar subespacios de dimensiones/features incompatibles.
- Emitir subespacio/proyector, amplitudes, residuo y cambio mediante ángulos principales. Una compresión estable no demuestra harmonicidad.
- Candidatos Jpsh! por cambios cinemáticos detectables de cada región, con umbrales/refractario/duración y marcas humanas separadas.
- Estimar centros candidatos mediante precedencia y ganancia predictiva de modelos lineales regularizados con retardos, frente a historia propia del destino. Ajuste/selección en ventana pasada; actualizar fuera del hilo de audio.
- Mostrar múltiples scores y soporte temporal; no forzar clasificación. La propagación que requiere observar respuesta aparece con demora declarada, no como predicción instantánea.
- Interferencia: alineación/oposición con estado previo/predicho, componente en subespacio y novedad transversal. Compatibilidad es conservación de relaciones seleccionadas o respuesta predictiva posterior, no sinónimo de perpendicularidad.

## Sonificación

Publicar señales para el preset editable: oposición→desvío; refuerzo→afinación; variación compatible→fase/gain/timbre. Distinguir región local y organización global; frenado local puede favorecer el conjunto. Nada se etiqueta intención, causalidad, energía transferida ni calidad humana.

## Pruebas

Modo estable, rotación de base sin cambio físico, degeneración, ruido/gaps, propagación iniciada en distintas regiones, dos impulsos simultáneos, quietud sin centro y oposición local/global. Verificar no fuga de futuro y disponibilidad de observaciones en cada salida.

Completar software no cierra [RES-ORGANIZATION · #20](https://github.com/AlterMundi/harmonic-weaver/issues/20) ni #6. La validez científica se investiga en el segundo milestone.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9), [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-07 -->
