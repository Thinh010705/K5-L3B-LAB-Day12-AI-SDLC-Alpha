"""Kho cá thể v1.2 và tính độ tươi theo đơn vị chính xác (240 đơn vị/điểm)."""

import math
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

UNITS = 240


def validate_instances(items, kinds):
    if not isinstance(items, list):
        raise BadInput("v1.2: items/hold phải là mảng cá thể, không nhận kho đếm")
    seen = set()
    result = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể phải có đúng id, kind, fresh")
        ident, kind, fresh = item["id"], item["kind"], item["fresh"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise BadInput("id cá thể phải là chuỗi khác rỗng, duy nhất")
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput("kind cá thể không hợp lệ")
        if (isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or
                not math.isfinite(fresh) or not 0 <= fresh <= 100):
            raise BadInput("fresh phải hữu hạn trong [0,100]")
        seen.add(ident)
        result.append(dict(item))
    return result


def ordered_instances(items):
    return [dict(item) for item in sort_by_id(items)]


class Freshness:
    """Mỗi sim giữ bộ tính riêng; ID được giữ bởi IdAllocator chung của lượt/day."""

    def __init__(self, config, tick_hz, *, location="hold"):
        self.config = config
        self.location = location
        rate = "quan_decay_per_s" if location == "stock" else "gather_decay_per_s"
        self.decay = Fraction(str(config[rate])) * UNITS / tick_hz
        self.threshold = Fraction(str(config["spoiled_below"])) * UNITS
        self.values = {}

    def _units(self, fresh):
        units = Fraction(str(fresh)) * UNITS
        # Khôi phục giá trị nguyên đơn vị sau round-trip float JSON (vd 100-1/120).
        # Không làm tròn cá thể ở hai phía sát ngưỡng 30 thành đúng ngưỡng.
        nearest = round(units)
        error = abs(float(units - nearest))
        tolerance = math.ulp(float(fresh)) * UNITS * 2
        if error <= tolerance and not (nearest == self.threshold and units != self.threshold):
            return Fraction(nearest)
        return units

    def decay_hold(self, hold):
        return self.decay_items(hold)

    def decay_items(self, hold):
        events = []
        for item in sort_by_id(hold):
            ident = item["id"]
            previous = self.values.get(ident)
            if previous is None:
                previous = self._units(item["fresh"])
            current = max(Fraction(0), previous - self.decay)
            self.values[ident] = current
            item["fresh"] = float(current / UNITS)
            if previous >= self.threshold and current < self.threshold:
                events.append(("spoiled", {"item_id": ident, "kind": item["kind"], "location": self.location}))
        return events

    def forget(self, items):
        for item in items:
            self.values.pop(item["id"], None)
