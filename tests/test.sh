#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== PYTHON ==="
python -m py_compile nexus.py nexuslib/core.py
echo "✅ Python"

echo "=== BASH ==="
bash -n bin/nexus
bash -n bin/repair-bot
bash -n tests/test.sh
echo "✅ Bash"

echo "=== SELFTEST ==="
python nexus.py selftest | grep -q "SELFTEST PASS"
echo "✅ Selftest"

echo "=== ARCHITECT ==="
python nexus.py create "Nexus Test Project" |
jq -e '.name == "nexus-test-project"' >/dev/null
echo "✅ Architect"

echo "=== STATUS ==="
python nexus.py status |
jq -e '.service == "mikis13-nexus"' >/dev/null
echo "✅ Status"

echo "=== ANTI LOOP ==="

P="anti-loop-test-$(date +%s)-$$"

python nexus.py learn "$P" FAIL >/dev/null
python nexus.py learn "$P" FAIL >/dev/null
python nexus.py learn "$P" FAIL >/dev/null

python nexus.py analyze "$P" |
jq -e \
'.recommendation == "STOP_REPEAT_AND_CHANGE_STRATEGY"' \
>/dev/null

echo "✅ Anti-loop"

echo
echo "================================"
echo "✅ MIKIS13 NEXUS TESTS PASS"
echo "================================"
