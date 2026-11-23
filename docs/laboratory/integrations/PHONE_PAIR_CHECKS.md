# Phone Pair implementation checks — 2026-11-13

The initial experiment was tested against Weaver
`1d5dd8e9f111f14230891ea7974d88fb32aacc32`. Shaper inspected/tested at
`dcebaf84764b47836a4e8d523ec0ef8b4cbccd5d`; Spatializer inspected at
`83db4ecfbdd57271f8d4fd9d3eb5083fa5a72536`.

The GitHub branch uses Weaver base
`dc825aef61dce29f4bccf144c98f9c542beeb3fc`. The laboratory app, runtime, router
and their audio and contract dependencies are identical on those two bases.

## Native checks

Using an isolated Python3.13 test environment and the existing sibling sources:

```sh
PYTHONPATH=src:../harmonic-shaper/src .venv/bin/python -m pytest \
  tests/test_phone_pair.py tests/test_phone_pair_laboratory.py \
  tests/test_lab_routing.py tests/test_lab_runtime.py tests/test_lab_audio.py \
  tests/test_lab_contracts_store.py tests/test_lab_source_binding.py \
  tests/test_guitar_spectrum_source.py -q
```

The November 23 run on the publication base reported **77 passed and 1 failed**,
including all 18 phone integration checks. The failing schema check is also
present on `main`: the published `PerceptionSettings` JSON schema lacks
`camera_rotation_degrees`.

The new tests prove source contracts, real-zero preservation, invalid/flat/gapped
support, independent expiry, ordering/stream replacement, bounded histories,
native guitar handshake/gate/baseline recovery, real encoded UDP addresses,
private browser routes/control, native restart latching and occupied-port refusal.
Laboratory tests prove the same runtime/audio owner, typed phone features,
28-voice scoped preset with unchanged saved six-voice configuration, key revocation
on source replacement, scoped zero-release cut, the existing ShaperOutput HTTP
client into real Shaper LaboratoryInput, and real offline PCM continuity/release.
No PortAudio device is opened.

## Browser and old-prototype reproduction

Seven Chromium journeys passed again on November 23 with virtual phone events. The
fixture used the CURRENT full laboratory application/LaboratoryRuntime, a silent
sink, a separate loopback private edge and the actual two phone sender pages.
Checks include both permission paths, real WebSockets, source-driven diagrams and
control bars,600ms monitor delay with uninterrupted source/controller progress,
pause/resume/cut/Stop,320px reflow, controls within1280x600, and exit while permission
is pending. No page errors occurred. `scripts/check-phone-pair-browser.py` is the
reusable developer journey; use only an isolated silent fixture.

The old Home lease was separately reproduced using the exact `leaseGain` function
from the digital-beacon rehearsal branch's `web/voice-bank.mjs` and real Chromium
OfflineAudioContext. With two renewals600ms apart, a constant unit input measured
RMS1 over100–200ms, RMS0 over450–550ms and RMS1 over700–800ms. Renewals were executed
at the actual offline clock time using suspend/resume, not scheduled prematurely.
This demonstrates code-level lease starvation. No actual participant RTT trace
or live Home sensor injection was used.

## Acceptance boundary

The native source/router/HTTP/kernel and browser checks passed within their
stated scope. The full selected suite retains its known base schema failure.
Mac import, physical phones, selected HTTPS route, actual CoreAudio/output
underflows, guitar input and human listening remain UNOBSERVED. The current
Home tone prototype is unchanged; this packet is a native experimental candidate,
not a Home deployment receipt or completed show installation.
