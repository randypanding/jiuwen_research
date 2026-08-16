#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."

KERNEL=swarm-kernel
overall=0

step() {
  local name="$1"; shift
  echo "=== GATE: $name ==="
  "$@"
  local rc=$?
  echo "--- $name exit=$rc"
  return $rc
}

expect() {
  local want="$1"; shift
  local name="$1"; shift
  "$@"
  local rc=$?
  if [ "$rc" -ne "$want" ]; then
    echo "FAIL: $name expected exit $want got $rc"
    overall=1
  else
    echo "OK: $name exit=$rc"
  fi
}

step "kernel test suite" python3 -m pytest "$KERNEL/tests" -q || overall=1

expect 0 "gates/good" swarm-kernel gates run \
  --instance "$KERNEL/fixtures/instances/good" \
  --oracle "$KERNEL/fixtures/oracle" \
  --spec "$KERNEL/fixtures/spec/spec.json" \
  --out /tmp/gates-good \
  --group "$KERNEL/fixtures/instances/good" "$KERNEL/fixtures/instances/good2"

expect 1 "gates/bad(H3)" swarm-kernel gates run \
  --instance "$KERNEL/fixtures/instances/bad" \
  --oracle "$KERNEL/fixtures/oracle" \
  --spec "$KERNEL/fixtures/spec/spec.json" \
  --out /tmp/gates-bad \
  --group "$KERNEL/fixtures/instances/bad"

expect 1 "gates/secret(H6)" swarm-kernel gates run \
  --instance "$KERNEL/fixtures/instances/secret_bad" \
  --oracle "$KERNEL/fixtures/oracle" \
  --spec "$KERNEL/fixtures/spec/spec.json" \
  --out /tmp/gates-secret \
  --group "$KERNEL/fixtures/instances/secret_bad"

expect 1 "gates/drift(H7)" swarm-kernel gates run \
  --instance "$KERNEL/fixtures/instances/drift_bad" \
  --oracle "$KERNEL/fixtures/oracle" \
  --spec "$KERNEL/fixtures/spec/spec.json" \
  --out /tmp/gates-drift \
  --group "$KERNEL/fixtures/instances/drift_bad"

expect 1 "drift/scan-stale" swarm-kernel drift scan \
  --spec "$KERNEL/fixtures/spec/spec.json" \
  --root "$KERNEL/fixtures/instances/drift_bad"

expect 0 "drift/scan-clean" swarm-kernel drift scan \
  --spec "$KERNEL/fixtures/spec/spec.json" \
  --root "$KERNEL/fixtures/instances/good"

if [ "$overall" -ne 0 ]; then
  echo "ALL GATES: FAIL"
  exit 1
fi
echo "ALL GATES: PASS"
exit 0
