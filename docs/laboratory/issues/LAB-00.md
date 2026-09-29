El baseline usado por Nicolás no está disponible íntegro en main. La rama local `feat/geometry-activation`, HEAD `7aaa8c0`, contiene siete commits por delante del ancestro compartido y modificaciones relevantes sin commit. Main remoto `726f3bf` tiene además los fixes de tests portables de PR #5. Ver BASELINE_INVENTORY.json: enumera revisiones y hashes de los archivos locales relevantes, sin incluir grabaciones.

## Trabajo concreto

- En el workspace original, comparar el inventario con el estado actual; registrar cualquier evolución antes de copiar. Preservar solo el baseline y sus dependencias, no todos los untracked de reports/rehearsal.
- Publicar una rama revisable del baseline existente, incluidos live_controls, plucks y web; distinguir recuperación de trabajo ya hecho de implementación del laboratorio.
- Reconciliar con main en checkout aislado conservando los tests portables. No resetear ni limpiar la rama del usuario.
- Identificar dependencias exactas de HarMoCAP/Shaper y publicar el mínimo que les falte por sus repos propietarios. No sustituirlas con shims silenciosos.
- Correr regresiones pertinentes y registrar commit reproducible del controlador actual, sus defaults y diferencias contra v1 original. Preservar seis zonas y sonidos raw/plucks.

## Salida

Una sesión ajena puede obtener el baseline por GitHub y correr los tests sin acceder a archivos locales privados. Registrar PRs/commits y comandos en la issue madre. Las grabaciones, pesos y evidencia privada se referencian por manifest apropiado, no se suben a git.

## Aceptación

- [ ] Baseline publicado con procedencia y cambio local preservado.
- [ ] Cambios de tests de main conservados; pruebas relevantes verdes.
- [ ] Repos hermanos y revisiones declarados; no confundir pruebas sin audio con escucha.
- [ ] El launcher aislado previo sigue disponible.

Es el prerrequisito de integración del laboratorio; investigación y diseño de contratos pueden avanzar leyendo el inventario, pero no asumir que main ya contiene el instrumento.
