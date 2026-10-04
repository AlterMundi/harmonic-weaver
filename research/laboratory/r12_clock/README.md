# R12 · Sensibilidad al reloj declarado

Banco de software, 2026-10-03. No adquisición ni mediciones humanas.

En web: Investigación → R12 → **Sensibilidad del reloj R12**. Declarar una lista
JSON de deltas en segundos del reloj común, incluyendo cero (2–9 valores únicos,
±60 s). Cada delta se suma al offset vigente; rate, timestamps originales,
valores/exclusiones, canales y ventanas de intentos permanecen congelados.
La incertidumbre declarada no genera una distribución ni una grilla automática.
El default del control nuevo es `[-0.1,0,0.1]`, una propuesta editable de
perturbaciones, no una incertidumbre medida. Defaults del instrumento intactos.

Para cada condición se muestran cobertura/media originales y pareadas. El soporte
pareado es la intersección de intervalos observados válidos de **todos** los offsets
y canales seleccionados para soporte común. Se recorta por intento. Canales extra
mantienen además su propia validez, por lo que no se afirma que todos tengan igual
cobertura. No se rellenan gaps, extremos ni soporte vacío. Trapezoides sólo dentro
de pares adyacentes válidos. Comparar cambios con la misma unidad y soporte;
no elige un offset ganador ni convierte HR a calorías/eficiencia.

Los hashes de soporte pareado representan intervalos unidos (independientes de
su partición por muestras). Los hashes nativos conservan el contrato histórico de
pares observados; no comparar ambos como si fueran la misma representación.

**Guardar sensibilidad R12** publica request/result/manifest locales bajo
`research/r12-clock-sensitivity/` del data-dir. Reintentar el mismo request es
idempotente; reapertura recomputa bajo código/entorno coincidentes y conserva
lecturas históricas como integridad sola cuando cambian. No sustituye adquisición,
calibración o sincronía físicas. El vínculo EVAL se valida al inspeccionar/guardar;
una carga de archivo no demuestra que el medio permanezca disponible hoy.

Configuración export/import incluye únicamente deltas. Resultados y requests
incluyen datos/contexto humanos si se importaron: permanecen locales. Reabrir un
resultado no aplica su protocolo al editor. Cambiar el protocolo durante una
respuesta demorada impide que el resultado anterior se aplique.

## Reproducir

Desde Weaver con su venv:

```sh
PYTHONPATH=src .venv/bin/python -m research.laboratory.r12_clock.experiment --output /tmp/r12-clock-new
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.physiology_sensitivity_run --request /ruta/local/request.json --output /ruta/local/carpeta-nueva
```

Carpetas de salida nuevas, sin sobrescribir. La receta pública construye dos casos,
repite cada uno dos veces y verifica manifests/resultados por recomputación.
[Evidencia pública](evidence-2026-10-03.json) contiene sólo datos sintéticos:

| Caso | Soporte pareado | Medias HR para deltas −0.5/0/+0.5 | Resultado |
| --- | --- | --- | --- |
| HR lineal, potencia constante | [0.5,3.5] s | 85/80/75 bpm | Una perturbación temporal cambia la media aun con soporte idéntico; potencia parcial 6 J en las tres |
| Falta la muestra central de HR | Vacío | null/null/null | Los intervalos válidos desplazados no tienen intersección positiva; no se convierte ausencia a cero |

Son resultados construidos para comprobar el mecanismo. No establecen cuál es el
reloj correcto ni propiedades de personas. Mediciones reales, evidencia del reloj,
calibración, tarea/resultado útiles y participantes siguen pendientes en
[R12](../R12_MEASUREMENT_PROTOCOL.md).
