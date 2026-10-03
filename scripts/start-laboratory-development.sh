#!/usr/bin/env bash
# Compatibility spelling; one development profile owns defaults and validation.
set -euo pipefail
lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$lab_root/scripts/start-laboratory-dev.sh" "$@"
