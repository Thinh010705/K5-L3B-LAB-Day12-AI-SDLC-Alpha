"""Versioned inventory handoff. Files are replaced atomically on completion."""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = KINDS_P1 + ("ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS_P2):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_instances(items, kinds=KINDS_P2):
    """Validate v1.2 physical stock, preserving every id and freshness value."""
    if not isinstance(items, list):
        raise BadInput("items v1.2 phải là mảng cá thể")
    seen = set()
    result = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể kho phải có đúng id, kind, fresh")
        ident, kind, fresh = item["id"], item["kind"], item["fresh"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise BadInput("id cá thể kho rỗng hoặc trùng")
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        if (isinstance(fresh, bool) or not isinstance(fresh, (int, float))
                or not math.isfinite(fresh) or not 0 <= fresh <= 100):
            raise BadInput(f"fresh ngoài miền [0,100]: {fresh!r}")
        seen.add(ident)
        result.append({"id": ident, "kind": kind, "fresh": fresh})
    return result


def read_inventory(path: str, kinds=KINDS_P2, *, version="1.1"):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if version == "1.2":
        return validate_instances(data["items"], kinds)
    if version in ("1.0", 1.0, "1.1"):
        return validate_items(data["items"], kinds)
    raise BadInput(f"contract_version không được hỗ trợ: {version!r}")


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, *, version="1.1"):
    if version == "1.2":
        items = sort_by_id(validate_instances(items))
    elif version in ("1.0", 1.0, "1.1"):
        items = validate_items(items)
        items = {k: items[k] for k in sorted(items)}
    else:
        raise BadInput(f"contract_version không được hỗ trợ: {version!r}")
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
