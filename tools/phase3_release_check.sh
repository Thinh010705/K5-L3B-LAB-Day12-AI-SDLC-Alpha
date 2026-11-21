#!/usr/bin/env bash
# A conservative preflight; does not create or move tags.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [ "$(git branch --show-current)" != 'main' ]; then echo 'FAIL: switch to main'; exit 1; fi
if [ -n "$(git status --porcelain)" ]; then echo 'FAIL: working tree must be clean'; git status --short; exit 1; fi
git fetch origin --prune
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then echo 'FAIL: local main differs from origin/main'; exit 1; fi
if git show-ref --verify --quiet refs/tags/phase-3 || [ -n "$(git ls-remote --tags origin 'refs/tags/phase-3*')" ]; then echo 'NOTE: phase-3 tag already exists: inspect it; never force-move'; exit 1; fi
python3 - <<'PY'
import json, pathlib, re
c=json.loads(pathlib.Path('game.contract.json').read_text(encoding='utf-8'))
assert str(c.get('contract_version'))=='1.2', 'contract is not v1.2'
p=pathlib.Path('docs/proof/phase-3')
log=(p/'regression.log').read_text(encoding='utf-8')
assert re.search(r'Ran \d+ tests',log), 'test count not recorded'
assert re.search(r'(?m)^OK\s*$',log), 'test output has no final OK'
assert not re.search(r'(?m)^FAILED',log), 'regression failed'
report=pathlib.Path('docs/verification/phase-3.md').read_text(encoding='utf-8')
pending=re.findall(r'^\| AC-P3-[^\n]*\| PENDING \|',report,re.M)
assert not pending, f'{len(pending)} AC rows still PENDING'
assert (p/'smoke-summary.txt').is_file(), 'smoke summary missing'
assert 'PASS:' in (p/'smoke-summary.txt').read_text(encoding='utf-8'), 'smoke summary has no PASS lines'
exts=c.get('extensions',[])
assert exts, '5-person team needs at least one extension; verify team_size if changed'
print('PASS: main and origin/main match; manifest v1.2; regression log, smoke summary and AC table present')
print('Extensions declared:',exts)
print('NOTE: manual UI review, extension functionality, and proof completeness remain a human sign-off')
PY
printf 'READY TO REVIEW FOR TAG: %s\n' "$(git rev-parse HEAD)"
