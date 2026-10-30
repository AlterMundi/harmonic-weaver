# Recording setup and destinations

The **Grabar** tab is beside **Captura**. It configures the next quick take;
the Grabar / Detener y guardar controls remain beside the camera. This surface
reuses CaptureSession and CaptureExports. It does not change instrument tuning,
voice mappings or listening volume.

## Composition

- Sound in the exported video is optional. Original PCM remains in the existing
  capture archive because its sample clock aligns the video. No microphone is
  added by this feature.
- The body overlay uses observed joints and the existing projection/identity/gap
  rules. No interpolated pose is manufactured.
- The optional harmonic figure uses the recorded pre-shape/limiter oscillator
  state and the initial visual configuration. It is a geometric representation,
  not physical cymatics.
- Solo video y música disables both overlays and includes instrument sound.
- Quick takes remain bounded to 300 seconds. MP4 is the convenient preview;
  MKV retains uncompressed audio when sound is included. Both can be copied.

Settings persist privately under `DATA_DIR/recording/preferences.json`. They
are machine-local, not a portable preset: destination IDs refer to local grants.
Capture/export profiles in Captura remain available for advanced operation.

## Native folder and Google Drive adapter

The existing desktop system Python runs `recording_desktop.py`, using GTK 3
and GIO through PyGObject. A native chooser grants a destination. The HTTP API
accepts an opaque registered destination ID, not a caller-supplied filesystem
path or upload URL. The picker appears on the computer running the laboratory.
Library recording/download remains available on hosts without this desktop.

An operator may configure `DATA_DIR/recording/desktop.json` with only DISPLAY,
XAUTHORITY, DBUS_SESSION_BUS_ADDRESS and XDG_RUNTIME_DIR references when the
service does not inherit its desktop environment. Do not store credential values
or copy Xauthority/keyring contents into this file. Private files use mode 0600.

`DATA_DIR/recording/provider.json` selects the expected Google account using an
`account` field. There is no default personal or institutional account in shared
source. The application opens the existing Google Online Accounts settings only
when a human clicks Conectar Drive. Authentication stays in the desktop keyring;
ChatGPT connector login is a separate capability and supplies no app token.
Enable Files for the selected account, refresh the connection and choose a folder.
A Drive selection must have the exact expected `google-drive://user@host` account.
No other cloud provider or another Google account is silently substituted.

GIO and GTK contracts: [Gio.File](https://docs.gtk.org/gio/iface.File.html),
[GTK file chooser](https://gnome.pages.gitlab.gnome.org/gtk/gtk3/iface.FileChooser.html),
[GNOME GVFS schemes](https://wiki.gnome.org/Projects%282f%29gvfs%282f%29schemes.html).

## Delivery and interruption

A selected destination receives a copy of confirmed export artifacts. The
existing archive and original camera/pose/configuration data stay in place.
The destination grants and delivery receipts remain in the private recording
folder. No new Google sharing permissions are created.

Each output filename includes its export ID and delivery nonce. Copying never
overwrites a differing file. The adapter reads the destination back and verifies
both its byte count and SHA-256 before reporting success, including for Drive.
A timeout, uncertain acknowledgement or interrupted worker remains unconfirmed;
Verificar guardado checks the same planned file without replaying the copy.
Identical active/completed requests return their retained job. A distinct busy
request returns 409 before creating a job or writing bytes; the UI may wait and
retry this known rejection. Other failures are not automatically replayed.

Keep the page open until Video listo and, when a destination is selected, its
verified-copy status. If the page is closed early, originals remain and explicit
preparation/copy can be resumed in Tomas. A receiving login, a real destination
selection and physical audiovisual acceptance must be qualified separately from
synthetic API/media tests. No maximum-duration performance guarantee follows
from the configured five-minute bound.
