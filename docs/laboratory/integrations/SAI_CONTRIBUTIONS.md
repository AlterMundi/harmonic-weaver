# Sai contribution adoption — 2026-11-12

This inventory separates shared source, an installed checkout and actual human
use. It covers the inspected laboratory repositories, not every contribution by
Sai to every Beacon project. Author identity in GitHub is `SairaAsua` / saira asua;
later Eko-authored extensions remain attributed separately.

| Contribution | Source evidence in Weaver main | Meaning and remaining check |
| --- | --- | --- |
| Camera identity and orientation | `f745273`, `83cfd09`, `2dbea0f`, `f458558` | Stable USB/integrated selection and accessible source controls; test actual receiving device and permission |
| Movement tutorial and levels | `7388d9a`, `b157154` | Separate viewers/listening controls; human movement and listening remain receiving checks |
| Fullscreen dance | `60b1eb4` | Existing ordinary body frontend, not a separate app |
| Optional body recording | `1cd962c`, `a3c093c`, `e88e5cb` | Overlay/sound, composition and browser destinations; not automatic recording or copying another person's files |
| Facial mirror and research protocol | `a1f1eb9` | Browser-local instrument, later extended by Eko's contour work; not a native Shaper/OSC facial source |

All rows above are ancestors of Weaver `25d380d8bceff2263579851c5792536930e37659`,
also present in the Mac preparation baseline `b01d79246e8ca1f49abf70b79e8fffa7670adc92`.
The ordinary build includes these features through the existing launcher. A Git
checkout does not update an already running browser bundle. The inspected Linux
lab had the shared source but no responding body UI on port 8765 at this check;
no new body session or capture was started by the audit.

## Missing companion found and adopted

HarMoCAP contribution `2d566f1a9370a44eae2b96d3066b3d4e68808021`
([source](https://github.com/AlterMundi/HarMoCAP/commit/2d566f1a9370a44eae2b96d3066b3d4e68808021))
keeps named device paths and URLs on the live read/retry path. The old
`25fda8d74c663a573aab6bc8f540c2c46ef250b9` companion treated every string as a
file. It was omitted from both the Linux companion checkout and handoff 1 for
the Mac. The Linux checkout was fast-forwarded to
`4d56e4d3da534287042e5eb870106ba0c589eb5f` while preserving local files; its two
`tests/test_capture_wakeup.py` tests passed with the existing environment and
imports resolved to that checkout. No camera/audio was activated. The Mac
[cutoff amendment](MACOS.md) includes the same correction; actual installation
and device acceptance there are still pending.

## Scope of the answer

No Sai-authored commits were returned by the inspected main-branch author
queries for harmonic-shaper or beacon-spatial. This is not proof that Sai made
no design/review contributions. Beacon web has separate Sai changes (including
room entry/account and scheduled-session fixes); those belong to the hosted
encounter platform and do not imply a local Mac deployment. Its operational
adoption remains with the existing Beacon service, not a duplicate local web
platform. The open Weaver PR #2 belongs to AnnieScigliano, not Sai; it remains
open and is not reported as integrated.

Further contributions can be reconciled by source revision in this inventory.
Do not infer physical sound, perception accuracy or HIT validation from these
source and regression checks.
