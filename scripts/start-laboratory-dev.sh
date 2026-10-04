#!/usr/bin/env bash
# Compatibility alias: one evolving laboratory, with the same ports and data.
set -euo pipefail
lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$lab_root/scripts/start-laboratory.sh" "$@"
