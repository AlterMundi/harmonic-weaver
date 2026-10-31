# Choose a USB camera or integrated webcam

Open **Fuentes** in the top toolbar, then **Cámara en vivo**. Choose a named device and press
**Usar esta cámara**. The image and tracking warm up together. Connected hardware,
a live image and an observed body are separate states shown in the panel.
Place the body in frame when the image is live but no person has been detected.

The Fuentes dialog is available in Explore, Performance and the movement tutorial.
It contains both live-camera controls and Cargar video; opening/closing it keeps
the current source, view and musical settings running. The camera list lives in
the dialog above the visualizers, with its own scroll. It does not depend on the
legacy Fuente tab being visible. Advanced video paths, tracking, calibration and
perception controls remain in explicit disclosures.

The camera belongs to the computer **running the laboratory**. For a camera
connected to another computer, run the laboratory there. Opening a remote web
page does not move camera inference to the browser's webcam. Browser recording
copy destinations remain separate and belong to the viewing computer.

## Detection and persistence

Linux detection queries V4L2 capabilities without starting a stream or a model.
Capture nodes are listed by card name; metadata/output nodes are excluded.
The list refreshes while Fuente is open, on page focus, and through
Actualizar cámaras. Plugging a camera in does not start it or switch the source.
A remembered missing camera stays selected and unavailable until reconnected or
explicitly replaced; it never falls back silently to a different webcam.

The selection is remembered by opaque device ID in browser localStorage. A
V4L by-id alias is preferred, with by-path as a physical-port fallback. On start,
the backend resolves the selection against the current inventory and passes
the device alias into the existing HarMoCAP capture worker. It does not rely on
the numeric index remembered by an old browser inventory. Device numbers can
change after reconnect/reboot. Two identical devices without serial identifiers
may depend on their USB ports; verify the picture after changing connections.

The native index remains available under Elegir cámara por índice · avanzado
for platforms without Linux named discovery. Enumeration does not probe random
OpenCV indices or open camera streams. Directory names, raw serial identifiers
and device paths are not returned by the public inventory endpoint.

Changing or closing the camera is blocked during an active capture. Stop the
recording first. A lost start acknowledgement is not retried automatically;
read the live state before an explicit retry. A warm or ready stream already
using the selected device disables a redundant start. A stale/error stream can
be reconnected with an explicit click. Existing perception settings, six voices,
volume, calibration rules and recording controls remain in use.

## API compatibility

- GET `/api/cameras`: `{supported, scope: "laboratory_host", cameras, streaming_started:false}`.
  Each row has `{id,label,index,available,reason}`.
- POST `/api/sources/camera`: `{device_id,perception}` resolves a current named
  device. Unknown/unplugged/unavailable IDs are rejected before source mutation.
- Existing `{index,perception}` requests remain supported for explicit advanced use.
- Camera snapshots add `index` and opaque `device_id`; existing stream/frame fields
  keep their prior meaning. Closing clears the selected active identity.

The standalone worker accepts a numeric camera index or a local V4L2 camera path;
network URLs and arbitrary filesystem paths are rejected. No browser camera
permission, microphone, browser video transport, new model or driver is introduced.

## Validation boundaries

Synthetic inventory tests cover metadata filtering, permissions, stable alias
renumbering, missing-device rejection, active-capture guards, worker path routing
and legacy numeric requests. Browser fixtures cover selection/reload, no automatic
activation, hotplug/removal, lost acknowledgement, state messages and narrow layout.
Actual receiving enumeration can be qualified without acquiring private images.
Physical image continuity, body tracking and hearing remain human acceptance.

Primary contract: [Linux VIDIOC_QUERYCAP](https://www.kernel.org/doc/html/latest/userspace-api/media/v4l/vidioc-querycap.html).

## Horizontal and vertical cameras

In **Fuentes → Cámara en vivo**, select **Horizontal** or **Vertical**.
**Dar vuelta** adds180° when a sideways-mounted camera would otherwise show the
person upside down. The selected orientation is a draft until **Usar esta cámara**
or **Aplicar orientación** is pressed; the panel separately shows the orientation
currently in use. Applying a different orientation reopens that same camera and
starts fresh person/calibration history. Recording blocks camera/orientation changes.

The worker rotates measured pixels before pose inference. Preview, source dimensions,
COCO frame-height-normalized coordinates and recorded camera previews share that
oriented frame. Uploaded videos keep their existing display-rotation metadata;
this camera setting does not rotate them again. Mirror display is independent.
Preview dimensions are bounded by960px on either axis for both orientations.
Export uses its selected canvas/layout, fitting the upright source within it.

Orientation is remembered per camera in the viewing browser; it never activates
hardware on its own. Runtime telemetry reports the applied rotation and perception
settings. Changing only orientation retains the active camera's other processing
settings. Horizontal0° remains the default for existing configurations.
