# Authenticated laboratory web control

The selected entry is https://compaii.dmn.homes/harmonic_lab/ in Apps. The alias
uses the existing Home service route and shared sign-in. It provides real
per-receiver status, individual start, start-all and ordinary interface links
only while the corresponding HTTP readiness check succeeds. There are no native
URI links in this web flow. Loading or polling the panel never starts services.

## Existing services, one receiving writer

The Home HTTP service uses its existing deployment capability and access checks;
Nicolas's selected instance is available to his existing paired-human audience.
Its private `STATE_DIR/control.json` contains only operator-selected receivers.
An HTTP caller cannot supply a machine address, user, credential, command, port
or file path. Each entry has `id`, `label`, `resource`, `address`, `user`, `key`
and `knownHosts`; credentials stay in private bounded service state, never the
package, Git or browser. Another pair deploys this same source through its own
Home capability and own resource bindings. Do not point Sai/Ani at Nicolas's
resource or assume that a daimon VM owns their workstation's devices.

The receiving Linux agent is a fixed executable, called through a new dedicated
SSH service identity. The selected key is restricted to the gateway address,
forced to this agent, and cannot forward, request a PTY or obtain a shell.
The only sudo grant runs that root-owned agent as the actual local operator,
with no arguments. Existing human administrative keys, SSH configuration and
broad sudo rules are preserved. `backend/install_transport.py` is an explicit
operator installation tool: public key plus a private receiving JSON with
`operator` and `gateway_address`. It does not start at skill read or create a
browser identity, login or pairing system. Non-Linux installation remains with
the receiving operator's actual native route; the script refuses before mutation.

The agent exposes only `status`, `start` and `configure` with closed validation.
It imports the existing `scripts/open-harmonic-lab.py` service functions; no URI
registration is required. It reuses the existing finite controller, Spatializer
and body launchers. The body component contains Weaver, HarMoCAP and its managed
Shaper. Camera/tracking is chosen later inside that interface. Missing or
unselected guitar/audio components do not block the other selected services.
A ready component is reused without restart. Host readiness is not physical
camera, motor, USB wiring, listening or tracking acceptance.

`start` creates one bounded receiving job and returns acceptance separately from
readiness. The UI updates actual service state and shows receiving failures.
One latest job, two fixed lock files and a 32-request idempotency ledger bound
control state; retries of a retained ID do not launch another job. Existing
component sessions retain their eight-hour maximum, owned-only Ctrl+C cleanup
and one 1 MiB latest log tail per component. No global Stop or model wakeup is
part of this operation. Control-job state expiry is not an excuse to stop an
unrelated or user-owned process.

## Audio and optional instruments

The receiving profile remains `~/.config/harmonic-lab/launch.json`. The panel
edits selected instruments and the existing native/JACK/auto output configuration
for **future starts**, without restarting or retuning an active performance.
No receiving device names are baked into the shared package. Reuse actual
PortAudio/CoreAudio/JACK inventories and preserve personal presets/calibration.
The three exact Linux JACK ports or the native CoreAudio device names remain
explicit. Never silently substitute another camera/microphone or infer hardware
from an accessible static UI. Body uses the host camera; Rostro uses the visiting
browser's camera. Model selection still uses the existing explicit `--checkpoint`
route; this panel does not claim a model selector.

The interface links intentionally target the selected receiver's localhost;
open them from that receiver's browser. The authenticated web control endpoint
can be reached elsewhere, but this does not proxy the instrument UIs onto another
computer or a phone. Open is disabled while readiness is absent. A disconnected
receiver cannot be started through an unavailable transport; the panel reports
that condition rather than inventing success or opening a closed port.

## Source, deployment and recovery

`laboratory-control/index.html` and `app.js` are the single frontend source;
`backend/main.js` is the Node24 HTTP adapter; `backend/agent.py` is the receiving
operation writer. The deployable Home bundle flattens the frontend beside the
Node entry with the existing closed `service.json` package contract. Use the
normal `daimon-home publish` and `daimon-home-service --request` route, exact
predecessor and private audience. Do not package receiving configuration or keys.
The public alias delegates to that authenticated route, never an unauthenticated
local-write or administrative SSH endpoint. Retain one current and one previous
package plus the exact deployment receipt; bounded service storage is enforced
by the existing receiver capability.

Code rollback preserves receiving profiles and live instruments. Removing the
transport later withdraws only its dedicated account/key, fixed agent and narrow
sudo fragment after its own job has finished; it must not alter any pre-existing
human login. Restoring UI code does not stop a motor/camera/audio operation.

Observed selected Linux receiving evidence is retained in the owning Harmonic
Lab work record: HTTP stopped-to-ready Spatializer/body startup, guitar reuse,
actual interfaces, dedicated operation/forwarding denials and unchanged admin
login hashes. Shared sign-in enforcement and browser verification are separate
from hardware and human acceptance. Mac, Sai workstation and other receiving
installations remain distinct unfinished adoption work, not implied by source
publication or a GitHub invitation.

## Retired first attempt

The initial static page used `harmonic-lab://` links. Nicolas rejected them;
terminal CLI/OS registration was not proof of a usable web click. That approach
was removed from the web flow. Retain its useful local service functions, but do
not reintroduce native protocols as substitutes for these real web operations.

## Headless Linux receivers

A server such as MEDUSA is distinct from its paired human's workstation. Without
an audio interface/camera/guitar, the supported Weaver routing engine may run
independently as `router` on loopback8767. It uses the existing Stage factory,
keeps no report/recording writer, and its session expires after8h with a single
1MiB log. This is the real router/patchbay, not body tracking, synthesis output
or physical audio acceptance. Uninstalled/unselected devices stay separate.

Reuse the existing own Home `web` service and its current per-pair audience.
The operator may select `proxies: {"router":8767}` in a receiver entry. This maps
only that fixed loopback service to `interfaces/<receiver>/router/`; no browser
input can choose a port/host. HTTP and WebSocket requests retain the existing
shared-auth gate, and cookies/authorization are not forwarded to the instrument.
Stage links/API/WebSocket URLs support the same relative prefix. Other receivers
keep their existing local-interface links unless explicitly configured otherwise.
Do not add MEDUSA to Nicolas's host list or route Sai through his credentials.
Use each receiving pair's existing slot/resource binding. Loading the panel
starts no instrument; optional service failures do not stop other components.

The per-receiver audio profile also accepts `BEACON_VOICE_INPUT_PORT` for an
explicit clean microphone mixed beside the guitar. R24capture_FR is input2.
The Spatializer route writer verifies its direct playback links independently
of the filtered guitar and preserves other microphone consumers. This path has
no13-band/spatial filters and creates no recording; input gain is the R24preamp.
