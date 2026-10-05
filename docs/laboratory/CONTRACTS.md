# Contratos y persistencia v1

LAB-01. Los modelos canónicos viven en `src/harmonic_weaver/lab/contracts.py`;
[schemas y fixtures](contracts/) se regeneran con:

```sh
PYTHONPATH=src python scripts/export-laboratory-contracts.py
```

Los fixtures son sintéticos. El de voces contiene seis osciladores con fases
conocidas; no es una grabación ni una medida de latencia. El preset tiene seis
voces y tres componentes PCA configurables de forma independiente.

Los schemas publicados describen el contrato actual de `/api/schemas`, incluidas
opciones de suavizado/continuidad, soporte colectivo y diagnóstico de audio.
Regenerarlos al modificar el contrato central evita que consumidores rechacen
configuraciones válidas. Los presets históricos v1 siguen cargando con defaults
de campos opcionales; exportar resuelve esos defaults explícitamente.

## Semántica

- JSON versionado, campos extra/versiones desconocidas rechazados, números
  finitos y unidades explícitas. Pose isotrópica usa altura de imagen en ambos
  ejes; confianza nunca ocupa la coordenada Z.
- Preset contiene configuración completa y defaults resueltos. No acepta fuente,
  identidad, calibración ni historia. Calibration y SessionState son objetos
  separados; reiniciar el servicio conserva configuración y biblioteca, pero
  empieza sin fuente, persona ni calibración aplicada.
- Cada destino tiene un escritor final: una ruta con términos combinables. Las
  rutas del laboratorio son una matriz acíclica de señales a voces. No aceptan
  expresiones Python. LAB-03 valida catálogo de señales/unidades y prepara la
  ejecución antes de aceptar una revisión.
- VoiceFrame describe amplitudes/fases efectivas de osciladores antes del
  waveshaping/limitador, con sample index y reloj. No equivale al PCM final.

## Persistencia y API

SessionStore usa SQLite WAL en el directorio de datos del laboratorio.
Configuración y evento se confirman en una transacción; errores de preparación
o revisión dejan activa la configuración previa. Undo/redo afecta configuración,
no transporte, identidad ni muestras. La historia de undo es de esta sesión.

La bitácora registra configuración, presets, calibración y marcas voluntarias.
No recibe ni persiste MotionFrame, FeatureFrame, audio o video live. La cache de
videos será un almacenamiento diferente en LAB-02.

HTTP: `/api/state`, `/api/schemas`, `/api/configuration`, `/api/presets`,
`/api/undo`, `/api/redo`, `/api/macros/{id}`, `/api/calibrations`, `/api/marks`,
`/api/events`. Las modificaciones de configuración requieren `expected_revision`;
el conflicto devuelve 409 con el estado actual. Importar/exportar un preset usa
el mismo formato completo. Duplicar usa un ID nuevo; favoritos son metadatos del
preset. Los nombres pueden contener Unicode, los IDs son independientes del path.

`/ws` transmite snapshots recientes a 30 Hz sin cola histórica por cliente.
Los comandos van por HTTP. La autoridad es el servidor; publicación de telemetría
y aplicación efectiva por tick se conectan en LAB-03. Solo se aceptan Host y
Origin locales, sin abrir el servicio a LAN por defecto.
