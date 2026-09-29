# Baseline preservado para el laboratorio corporal

LAB-00 · 2026-09-29 · seguimiento: https://github.com/AlterMundi/harmonic-weaver/issues/8

El instrumento local fue copiado a un worktree aislado antes de reconciliarlo
con main. El workspace original conserva sus cambios sin commit. Esta entrega
recupera trabajo existente; no implementa todavía la mesa del laboratorio.

## Procedencia y dependencias

- Weaver original: `7aaa8c04fe8ffc0497eb6b25290b63f747bba5d1` más los once archivos
  del inventario de la PR #28, copiados con igualdad SHA-256 comprobada.
- Snapshot de esos archivos: `2089ed3`. Reconciliación con main `726f3bf`:
  `18ddec0`; conserva los fixes de rutas portables de PR #5.
- HarMoCAP original: `4503393` más ajustes locales de captura/overlay/tests.
  Snapshot: `7cf8138`; reconciliado con main `bdeebbf` en
  `27b8fc21355e2f0078b6478d71739e2cc9a6e788`, rama
  `feat/laboratory-capture-baseline` de AlterMundi/HarMoCAP.
- Shaper: `c511c6a256711af60c0309e85deced47ac09fb1b`, ya publicado. El baseline
  no depende del vocoder ni de otros cambios locales sin commit de ese repo.

Quedaron fuera grabaciones, reportes nuevos, pesos de modelos y prototipos
locales sin referencia desde el instrumento. Los modelos se instalan mediante
el procedimiento de HarMoCAP. Sus hashes deben registrarse al realizar sesiones.

## Comportamiento congelado

Seis zonas (caderas, hombros, rodillas, codos, tobillos, muñecas), fundamental
40.4 Hz, snap 0 y controles web de sensibilidad/rangos/caída respecto del core.
Modo inicial pluck aperiódico: ataque 80 ms, cola 700 ms, umbral .15; opción de
respuesta continua por velocidad. Quietud no implica drone sostenido por defecto.
La referencia del README a drone sostenido corresponde a una revisión anterior.

El sonido expresa proxies cinemáticos y decisiones musicales. El signo de a·v
no mide potencia física. El baseline se preserva para contrastar; las correcciones
o nuevas interpretaciones se implementan como métodos versionados distintos.

## Uso y validación

Instalar Weaver con extras `test,rehearsal`, HarMoCAP con sus dependencias y
Shaper con audio. Configurar `HARMOCAP_DIR`, `SHAPER_DIR` y sus venvs cuando los
checkouts no estén en las ubicaciones predeterminadas del launcher. El launcher
previo se conserva: `scripts/start-kinetic-consonance.sh --help`.

Desde el checkout Weaver:

```sh
python -m pytest -q
bash -n scripts/start-kinetic-consonance.sh scripts/start-live-stack.sh
```

Desde el checkout HarMoCAP:

```sh
PYTHONPATH=src python -m pytest -q tests/test_capture_wakeup.py tests/test_instrument_overlay.py
```

Weaver: 184 tests y 4 subtests pasan (99.83 s). HarMoCAP: 8 pruebas específicas
pasan (0.31 s). Son verificaciones de software; escucha, cámara física y aceptación
humana del nuevo laboratorio siguen pendientes. LAB-08 las distingue expresamente.
