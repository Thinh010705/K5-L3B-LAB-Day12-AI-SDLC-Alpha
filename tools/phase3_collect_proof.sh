#!/usr/bin/env bash
# Collects objective Phase 3 proof. Does not modify tracked code or tag Git.
# Requires bash, Python 3, project dependencies and current manifest v1.2.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PROOF="docs/proof/phase-3"
mkdir -p "$PROOF"
{
  echo '=== branch ==='; git branch --show-current
  echo '=== tested source commit ==='; git rev-parse HEAD
  echo '=== working tree before proof ==='; git status --short
  echo '=== remotes ==='; git remote -v
} > "$PROOF/git-baseline.txt"

python3 - <<'PY' > "$PROOF/manifest-audit.txt"
import json
from chonoi.contract import load_contract
c = load_contract()
assert str(c.get('contract_version')) == '1.2', 'must activate contract v1.2 before acceptance'
print('contract_version:', c['contract_version'])
print('extensions:', json.dumps(c.get('extensions', []), ensure_ascii=False, sort_keys=True))
print('freshness:', json.dumps(c.get('tuning', {}).get('freshness', c.get('freshness', {})), ensure_ascii=False, sort_keys=True))
print('contract validation: OK')
PY

cat > "$PROOF/scenario-threshold.json" <<'JSON'
{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}
JSON
python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario "$PROOF/scenario-threshold.json" --out "$PROOF/freshness-threshold.jsonl"

cat > "$PROOF/scenario-handoff.json" <<'JSON'
{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}
JSON
cat > "$PROOF/inputs-handoff.json" <<'JSON'
{"frames":[{"tick":0,"interact":true}]}
JSON
python3 -m chonoi.headless --mode gather --seed 1 --ticks 2 --scenario "$PROOF/scenario-handoff.json" --inputs "$PROOF/inputs-handoff.json" --out "$PROOF/gather-handoff.jsonl" --inventory-out "$PROOF/inventory-v12.json"
python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory "$PROOF/inventory-v12.json" --out "$PROOF/quan-stock-tick0.jsonl"

cat > "$PROOF/invalid-count-inventory.json" <<'JSON'
{"items":{"ca_linh":1}}
JSON
rm -f "$PROOF/should-not-exist.jsonl"
if python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory "$PROOF/invalid-count-inventory.json" --out "$PROOF/should-not-exist.jsonl" 2> "$PROOF/inventory-count-rejection.stderr"; then
  echo 'ERROR: old count inventory unexpectedly accepted under v1.2' >&2
  exit 1
else
  exit_code=$?
  if [ "$exit_code" -ne 2 ]; then
    echo "ERROR: expected exit 2 for old inventory, got $exit_code" >&2
    exit 1
  fi
fi
if [ -e "$PROOF/should-not-exist.jsonl" ]; then
  echo 'ERROR: invalid input unexpectedly produced output file' >&2
  exit 1
fi

python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --snapshot-every 600 --out "$PROOF/day-1.jsonl"

python3 - "$PROOF" <<'PY' | tee "$PROOF/smoke-summary.txt"
import json, math, pathlib, sys
p=pathlib.Path(sys.argv[1]); read=lambda fn:[json.loads(x) for x in (p/fn).read_text(encoding='utf-8').splitlines() if x.strip()]
rows=read('freshness-threshold.jsonl')
sp=[r for r in rows if r.get('type')=='event' and r.get('name')=='spoiled']
assert len(sp)==1 and sp[0]['tick']==1, f'spoiled should fire once at tick=1: {sp}'
assert sp[0].get('data',{}).get('item_id')=='I1' and sp[0].get('data',{}).get('location')=='hold', sp
print('PASS: spoiled at tick 1 for I1 (hold)')
inv=json.loads((p/'inventory-v12.json').read_text(encoding='utf-8'))
assert set(inv)=={'items'} and len(inv['items'])==1, inv
item=inv['items'][0]
assert item['id']=='I1' and item['kind']=='ca_linh' and 0<=item['fresh']<100, item
handoff=read('gather-handoff.jsonl')
ends=[r for r in handoff if r.get('type')=='event' and r.get('name')=='gather_end']
assert len(ends)==1, ends
assert ends[0]['data']['inventory']['items']==inv['items'], 'event/file inventory differ'
quans=read('quan-stock-tick0.jsonl')
ss=[r for r in quans if r.get('type')=='snapshot' and r.get('tick')==0]
assert ss, 'no Quan tick-0 snapshot'
assert ss[0].get('stock')==inv['items'], f'Quan did not preserve inventory exactly: {ss[0].get("stock")}'
print('PASS: Gather event -> inventory file -> Quan tick0 preserve individual ID/kind/fresh')
day=read('day-1.jsonl')
assert day[-1].get('type')=='end' and day[-1].get('reason')=='days_complete' and day[-1].get('days_completed')==1, day[-1]
print('PASS: Day one-day completion')
print('PASS: count inventory rejected before JSONL created (verified by shell exit code 2)')
print('NOTE: these smoke checks do not cover reserve/reprice, UI, extension, all Day edge cases')
PY

set -o pipefail
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v 2>&1 | tee "$PROOF/regression.log"

echo "Proof saved in $PROOF. Mark AC PASS only after verifying all additional tests/UI/extensions."
