"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .day import DaySession
from .errors import BadInput
from .inputs import BUTTONS_V10, BUTTONS_V11_CORE, LiveInputs
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario
from .scenario_day import load_day_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
PROPOSED_V11 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "contracts", "game.contract.v1_1.proposed.json",
)
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=1):
        self._args = (mode, tuning, scenario, seed, inventory)
        self.mode = mode
        self.tuning = tuning
        self.days = days
        self.inventory_out = inventory_out
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        mode, tuning, scenario, seed, inventory = self._args
        if mode == "day":
            self.session = DaySession(tuning, scenario, seed, days=self.days)
            self.inputs = LiveInputs(buttons=BUTTONS_V11_CORE)
            self.events = list(getattr(self.session, "initial_events", []))
        else:
            self.session = Session(mode, tuning, scenario, seed, inventory)
            self.inputs = LiveInputs(buttons=BUTTONS_V10)
            self.events = []
        self._buy_queue = []
        self._saved = False
        self._paused = False
        self.error = None

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    if getattr(self.session, "sim", None) is not None:
                        self.session.sim.done = True
                        self.session.sim.reason = "error"
                    else:
                        self.session.done = True
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done or self._paused:
            return
        inp = self.inputs.advance()
        if self._buy_queue:
            inp.buy = self._buy_queue.pop(0)
        for row in s.step(inp):
            self.events.append(row)
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out and hasattr(s, "write_inventory_if_done"):
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            phase_key = snap.get("phase") or self.mode
            snap["meta"] = self.tuning.get(phase_key, self.tuning.get(self.mode, {}))
            snap["freshness"] = self.tuning.get("freshness")
            snap["menu"] = self.tuning.get("menu", {})
            if "shop" in self.tuning:
                snap["shop_config"] = self.tuning["shop"]
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["paused"] = self._paused or snap.get("state") == "paused"
            if self.session.done:
                if self.error:
                    snap["reason"] = "error"
                elif self.mode == "day":
                    snap["reason"] = "days_complete"
                else:
                    snap["reason"] = self.session.sim.reason
            else:
                snap["reason"] = None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_paused(self, paused: bool):
        with self._lock:
            self._paused = bool(paused)

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch", "pause", "shop_done", "attack", "photo"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and (not isinstance(buy, str) or not buy):
            raise ValueError("buy phải là chuỗi khác rỗng")
        with self._lock:
            self.inputs.set(move, **buttons)
            if buy is not None:
                self._buy_queue.append(buy)

    def restart(self):
        with self._lock:
            self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        elif path.startswith("/assets/"):
            rel = path[len("/assets/"):]
            if not rel or "/" in rel or "\\" in rel or ".." in rel:
                self._send(404, b'{"error":"khong hop le"}')
                return
            ext = os.path.splitext(rel)[1].lower()
            mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".webp": "image/webp", ".svg": "image/svg+xml"}.get(ext)
            if not mime:
                self._send(404, b'{"error":"khong ho tro"}')
                return
            fpath = os.path.join(WEB_DIR, "assets", rel)
            try:
                with open(fpath, "rb") as f:
                    self._send(200, f.read(), mime)
            except OSError:
                self._send(404, b'{"error":"thieu asset"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/pause":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict) or not isinstance(body.get("paused"), bool):
                    raise ValueError("paused phải là boolean")
                self.game.set_paused(body["paused"])
            elif path == "/restart":
                self.game.restart()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (gather / quan / day).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--days", type=int, default=5, help="số ngày khi chạy --mode day (1..5)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--contract", help="đường dẫn file manifest tùy chọn (mặc định game.contract.json)")
    p.add_argument("--cook-scale", dest="cook_scale", type=float, default=1.0,
                   help="hệ số thời gian nấu chỉ dùng khi chơi live/demo (mặc định 1.0, không ảnh hưởng headless)")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        contract = load_contract(a.contract) if a.contract else load_contract()
        tuning = contract["tuning"]
        if a.mode == "day" and ("day_plan" not in tuning or "shop" not in tuning):
            if os.path.exists(PROPOSED_V11):
                contract = load_contract(PROPOSED_V11)
                tuning = contract["tuning"]
                print(f"[live] Dùng cấu hình v1.1 tại {PROPOSED_V11} cho --mode day.", flush=True)
            else:
                raise BadInput("day yêu cầu tuning.day_plan và tuning.shop v1.1")
        if a.cook_scale <= 0:
            raise BadInput("--cook-scale phải > 0")
        if a.cook_scale != 1.0:
            from copy import deepcopy
            tuning = deepcopy(tuning)
            for dish in tuning.get("menu", {}).values():
                if "cook_s" in dish:
                    dish["cook_s"] = round(dish["cook_s"] * a.cook_scale, 2)
        if a.mode == "day":
            scenario = load_day_scenario(a.scenario, tuning, a.days)
            inventory = None
        else:
            scenario = load_scenario(a.scenario, a.mode, tuning)
            inventory = read_inventory(a.inventory) if a.inventory else None
            if inventory is not None and "stock" in scenario:
                raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, days=a.days)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    extra = f", {a.days} ngày" if a.mode == "day" else ""
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}{extra}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
