# Shared control panel, local receiving services

The shared entry is https://compaii.dmn.homes/harmonic_lab in Apps. It is navigation,
not a remote motor/camera endpoint. Native `harmonic-lab://guitar|audio|body|all`
activation resolves on the visiting computer; ordinary web links use that
computer's localhost. Opening the same panel never operates Legion from another
machine. No author bot, credentials or new login is involved.

On an existing Linux laboratory installation, run
`scripts/install-laboratory-launcher.sh`. This registers only the current user's
URL handler; it creates no startup daemon or recurring job. The local handler
uses the ordinary finite `start-live-stack.sh --guitar-lab` composition and
`--body-only` for an independent body component. Existing ready components are
reused. A foreign port is preserved. Each owned component session has its usual
eight-hour limit, Ctrl+C stop path and bounded latest component logs. Failed
components do not prevent the handler from attempting other selected components.
The first browser activation may ask the user to open the native application.

The handler's single optional local configuration is
`~/.config/harmonic-lab/launch.json`. Preserve a receiving operator's existing
file. The default selects the installed motor panel if present and the body
laboratory if present; Spatializer is off until an input/output profile is
selected. No camera is required just to start the body UI; choose its source
later. A computer without a guitar panel can start the body laboratory alone.
An example **structure**, not an inventory claim or a receiving driver choice:

```json
{
  "services": {"guitar": false, "audio": false, "body": true},
  "environment": {
    "HARMONIC_LAB_AUDIO_BACKEND": "native",
    "HARMONIC_SHAPER_DEVICE": "Exact receiving output device",
    "HARMONIC_LAB_TRACKING_DEVICE": "auto"
  }
}
```

Backend choices reuse existing `native`, `jack` and `auto` support. An empty
`HARMONIC_SHAPER_DEVICE` chooses the existing backend's default/query behavior;
it does not select an input camera or microphone. Use the actual receiving
PortAudio inventory and body UI audio controls to choose and check output.
For macOS Spatializer keep its exact `BEACON_INPUT_DEVICE` and
`BEACON_OUTPUT_DEVICE`. Linux Spatializer may select exact JACK ports with all
three of `BEACON_INPUT_PORT`, `BEACON_OUTPUT_LEFT`, `BEACON_OUTPUT_RIGHT`, or reuse
the existing R24/internal output profiles. Only its own SuperCollider links are
modified. Clock/channel compatibility and actual listening remain receiving
checks. Do not copy Linux device names onto another machine.

Current qualification: Linux activation of the previously stopped motor panel,
reuse without a second process, Spatializer base startup, separate body startup,
ordinary UI build, Shaper API and local interfaces were observed. The motor
panel remained idle and no camera was started. A browser on the publishing host
can inspect this navigation page but cannot prove the visiting Linux desktop's
external-protocol acceptance. Human clicking, listening and source tracking are
separate observations.

macOS has a portable engine handoff in [MACOS](MACOS.md); this Linux desktop
installer intentionally does not claim to register a macOS URL application.
Oliva is retaining that receiving gap with Ani's inventory/access work. Other
receivers need actual installation and selected audio; a shared entry or a GitHub
collaborator grant is not delivery of their local native handler.

Recovery removes only the registered `harmonic-lab.desktop` association/file if
still selected and stops the task-owned sessions through their native terminals.
Preserve original defaults/associations, local configuration, private media and
presets. The panel creates no hardware write merely by opening or restoring
saved form values.
