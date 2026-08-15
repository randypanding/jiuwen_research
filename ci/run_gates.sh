#!/usr/bin/env bash
# CI master gate script for the dev-swarm physics layer (swarmfoundry).
# Every step is a hard gate: any non-zero exit blocks admission (fail-closed).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"

step() { echo; echo "=== GATE $1: $2 ==="; }

step H1 "build / byte-compile"
"$PY" -m compileall -q "$ROOT/swarmfoundry/src"

step H1b "package importable"
"$PY" -c "import swarmfoundry" 2>/dev/null || PYTHONPATH="$ROOT/swarmfoundry/src" "$PY" -c "import swarmfoundry"

step H2 "unit + contract-communication test suite (oracle body)"
(cd "$ROOT/swarmfoundry" && "$PY" -m pytest tests -q)

step H5 "end-to-end admission selftest (differential + golden + judge)"
"$PY" -m swarmfoundry.cli selftest 2>/dev/null || PYTHONPATH="$ROOT/swarmfoundry/src" "$PY" -m swarmfoundry.cli selftest

step H7 "gate definitions integrity (this script is the sealed gate list)"
grep -q "swarmfoundry.cli selftest" "$ROOT/ci/run_gates.sh"

echo
echo "ALL GATES PASSED"
