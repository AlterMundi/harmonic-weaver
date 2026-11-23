# Experimental phone Pair source

This branch adds an experimental phone source to the existing laboratory
pipeline. The six-voice body preset is still available when using body sources.

```
Phone browser IMU -> private persistent WebSocket edge (Mac:5053)
                     -> current local LaboratoryRuntime (Mac:8765)
                     -> PhonePairSource / Weaver source contracts
                     -> typed FeatureFrame -> PreparedRoutes
                     -> SAME ShaperOutput / owner / latest-frame worker
                     -> existing Shaper /api/laboratory/frame (Mac:8085)
                     -> existing native audio callback

Alternative live guitar control:
PhonePairSource -> WeaverEngine / scene / native contract
                -> existing Beacon Spatializer OSC:57120
Guitar -> existing Spatializer SoundIn(0) / 13-band DSP -> native output
```

The private edge exposes only phone input, feedback and scoped modulation
controls. It does not expose the full laboratory, videos, bank, camera or capture
APIs. Neither the edge nor the panel creates another synthesizer. Shaper is the
additive instrument; the Spatializer processes live guitar. Opening a Home tab
does not route guitar audio or phone controls into a Mac automatically.

## Reuse the current Mac installation

Use the existing Weaver Python >=3.11 environment, not macOS system Python3.9.
Preserve local changes and source/device selections. The additive target needs
the laboratory from this branch already running through its normal launcher.
Do not run a second laboratory or Shaper to add phones. Update/restart through
the existing operator's foreground session when that source is selected.

The laboratory defaults to port 8765 and its Shaper HTTP interface to port 8085.
Use the launcher's native audio and device selection for listening, or run with
`--no-audio` to check controls silently. The integration works with Shaper's
OSC listener disabled. A control ACK confirms receipt of the frame.

From the selected `harmonic-weaver` checkout:

```sh
# Safe default: same phone contracts and laboratory routing, silent sink.
.venv/bin/python -m harmonic_weaver.phone_pair

# Join the EXISTING updated laboratory and its one ShaperOutput owner.
.venv/bin/python -m harmonic_weaver.phone_pair --connect

# Alternative: control the EXISTING live-guitar 13-band Spatializer.
# Uses its exact sibling manifest and genuine native hello/state read.
.venv/bin/python -m harmonic_weaver.phone_pair --target beacon --connect
```

Use only one selected target/receiver at a time. The foreground command reserves
loopback5053 before joining a native instrument; occupied ports fail without
killing their owners. `--port` and `--lab-url` can select existing local routes.
The lab URL must remain loopback. The command prints a private random panel URL.
Its capability is ephemeral and covers this rehearsal, not Home login/identity.

Phones need a same-origin HTTPS route to this Mac's5053 edge, including WebSocket
upgrade. Reuse the receiving operator's selected route; none is created by this
command. Never tunnel the entire8765 laboratory. Open the printed room path
through that selected HTTPS origin, then its A/B links on the phones. Sending
to the old VPS/Home room selects a different receiver. Physical proximity alone
does not select a LAN transport or bypass an Internet tunnel.

The panel works without starting phone sensors. Each phone's **Start** requests
both permission paths from one gesture and then streams finite readings at25Hz
over one socket. Zero is preserved. Reference resets yaw/pitch; Stop, background
or page exit closes its stream. No microphone, camera, ECG, EEG or synthetic
heartbeat is involved. A pending permission cannot resume a stopped page.

## Source and mapping semantics

`phone-a` and `phone-b` declare yaw/pitch/roll, linear acceleration and recent
RMS magnitude. `phone-pair` declares supported correlation and combined energy.
All three use real Weaver source manifests, exact digest/stream gates, sequence
checks, invalid states and expiry. The adapter calls the existing in-process
source API; it does not add a source UDP listener. `source_manifest()` validates
the canonical manifest digest against each checked-in golden sidecar on load.
Changing a manifest requires deliberately regenerating its canonical digest
with `contract_id_from_manifest`, then updating its sidecar and source tests.

No phone measurement is disguised as HarMoCAP joints or a physiological signal.
The typed laboratory feature frame names its phone-IMU algorithm and units.
The additive profile has28 voices: A1–10, B11–20, shared21–28. It reuses the
laboratory's gain/pan mapping, smoothing and atomic voice frame implementation.
Its preset is scoped to the phone controller; the saved body preset, six-voice
default, models and camera calibration are not edited. Selecting another source
closes the phone controller and revokes its old activation key.

This is a conservative FIRST native phone preset. It preserves role registers,
orientation pan, movement drive and supported shared-band correlation, but does
not claim the historical Python/SuperCollider timbre, partner cross-bleed,
whole-field master formula or phase behavior is reproduced exactly. Hearing and
mapping calibration must decide the show version before promotion.

The guitar alternative maps A to bands1–6, B7–12, shared13. It reads the actual
initial band gains/azimuths and restores them on missing input, pause or scoped
modulation cut. It never writes master and does not start guitar DSP. A native
identity/state failure latches modulation off until an explicit new verified
receiver start. Additive pause releases voices; additive cut uses zero release
for the phone controller's voices, without a global Shaper panic.

Correlation uses ONE receiver clock, a2s window,100ms grid, maximum350ms
interpolation gap and at least6 pairs. Flat, missing or insufficient support is
not an observed0% relation. This is not synchronized acquisition clocks,
proximity, emotional/physiological coupling or physical position tracking.

The panel restores orientation arrows, measured motion halos, relation support
and routed target bars. It distinguishes observed input, submitted controls and
fresh Shaper audio telemetry for the current owner. Target bars alone do not
prove audible output. Feedback polling cannot renew audio or keep a stale phone
alive; native laboratory ticks and the existing ShaperOutput own those clocks.
Ctrl+C closes only this receiver's selected phone source. Existing audio and
laboratory processes remain running; their ordinary ownership/lease rules apply.

## Evidence and remaining receiving

Local checks exercise real source contracts, input validation/epochs/expiry,
the actual LaboratoryRuntime/PreparedRoutes, source switching without saved
preset mutation, the existing ShaperOutput HTTP path and real Shaper offline PCM.
They also exercise actual browser senders/WebSockets and the current full
laboratory application through the private loopback edge with virtual sensors.
No physical phone, Mac import, CoreAudio device or human hearing is established.

The earlier digital-beacon Home experiment uses browser synthesis. Its
gain lease holds280ms and reaches zero420ms after a status update, while status
requests are serial. Real Chromium OfflineAudioContext reproduces silence with
600ms status intervals. The reproduction uses a synthetic status schedule.

Receiving must verify the selected HTTPS/WebSocket route, both physical sensor
permissions, fresh A/B visualization, actual native output/device/underflows,
human listening, Stop/background/pause/cut, and finally the live guitar route
with baseline restoration. Keep audio/media local and record the exact receiving
source and device choices. Promote only the selected tested branch normally;
this experimental request authorizes no automatic merge or main replacement.
