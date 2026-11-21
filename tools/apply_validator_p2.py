#!/usr/bin/env python3
"""Add version dispatch to existing chonoi/contract.py without rewriting P1 code.

Run from repository root: python3 tools/apply_validator_p2.py
The patch checks for an exact P1 anchor and refuses to overwrite changed code.
"""
from pathlib import Path
import ast

path = Path('chonoi/contract.py')
source = path.read_text(encoding='utf-8')
old = '    validate_tuning(c.get("tuning"))\n    return c\n'
new = '''    version = c.get("contract_version")
    if version == "1.0" or (type(version) is float and version == 1.0):
        validate_tuning(c.get("tuning"))
    elif version == "1.1":
        from .contract_v11 import validate_contract_v11
        validate_contract_v11(c)
    else:
        raise BadInput(f"contract_version không được hỗ trợ: {version!r}")
    return c
'''
if new in source:
    print('Already patched: chonoi/contract.py')
elif source.count(old) != 1:
    raise SystemExit('Cannot patch safely: P1 anchor changed. Review contract.py manually.')
else:
    revised = source.replace(old, new)
    ast.parse(revised, filename=str(path))
    path.write_text(revised, encoding='utf-8')
    print('Patched: chonoi/contract.py (v1.0 unchanged, v1.1 validation added)')
