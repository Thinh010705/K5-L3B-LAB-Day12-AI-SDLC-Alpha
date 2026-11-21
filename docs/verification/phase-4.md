# Nghiệm thu Phase 4 – Release v1.0.0 (TICKET-04)

**Nhóm:** Alpha  
**Repository:** `Thinh010705/K5-L3B-LAB-Day12-AI-SDLC-Alpha`  
**Test Contract:** v1.3  
**Nhánh nghiệm thu:** `main`  
**Tag dự kiến:** `phase-4`  
**Trạng thái hồ sơ:** **PASS**

---

## 1. Phạm vi thay đổi Phase 4

- **Hỗ trợ Test Contract v1.3:** Nâng cấp `game.contract.json` lên `contract_version: "1.3"`, bổ sung `"bench_cmd": "python3 -m chonoi.bench"` và `"soak_cmd": "python3 -m chonoi.soak"`.
- **Soak runner headless 10 ngày (`chonoi/soak.py`):** Điều khiển bot tự động chơi liên tục qua 10 ngày đêm, lặp lại chu kỳ kế hoạch thực đơn (`day_plan`) và đàn cá lặn hái; không rò rỉ bộ nhớ, không crash.
- **Benchmark có render (`chonoi/bench.py`):** Giả lập vẽ khung hình Canvas 2D 1280x720 cho cảnh sông Chín Khúc, đàn cá bơi và Cá Sấu Năm Chèo; đo `avg_fps`, `p1_low_fps`, `load_ms` trong 30 giây thực tế sau 3 giây warm-up.
- **Bảo toàn hồi quy:** Toàn bộ cơ chế từ Phase 1 (lặn, hái, nấu, tính tiền), Phase 2 (ngày đêm, cá bơi, Cá Sấu, shop, menu 6 món), và Phase 3 (kho cá thể, hao hụt độ tươi, ươn hỏng `spoiled`, định giá theo tươi) hoạt động chuẩn xác 100%.

---

## 2. Thông tin mã nguồn và thực thi

| Trường | Giá trị / Bằng chứng |
|---|---|
| Contract | `game.contract.json` (`contract_version: "1.3"`) |
| Lệnh test | `$env:PYTHONPATH = "tests;."; python -m unittest discover -s tests -v` |
| Log regression | [`docs/proof/phase-4/regression.log`](file:///d:/vinAI/lab12/K5-L3B-LAB-Day12-AI-SDLC-Alpha/docs/proof/phase-4/regression.log) (176 tests pass) |
| Log benchmark | [`docs/proof/phase-4/bench.json`](file:///d:/vinAI/lab12/K5-L3B-LAB-Day12-AI-SDLC-Alpha/docs/proof/phase-4/bench.json) |
| Log soak test | [`docs/proof/phase-4/soak.json`](file:///d:/vinAI/lab12/K5-L3B-LAB-Day12-AI-SDLC-Alpha/docs/proof/phase-4/soak.json) |

---

## 3. Ma trận Acceptance Criteria Phase 4

| Mã | Điều kiện chấp nhận | Cách kiểm chứng và bằng chứng | Kết quả |
|---|---|---|---|
| **AC-P4-01** | Test Contract v1.3 khai báo đầy đủ `bench_cmd` và `soak_cmd`, validator từ chối chuỗi rỗng | `game.contract.json`, `test_v13_loaded_successfully`, `test_v13_missing_bench_cmd_is_rejected`, `test_v13_missing_soak_cmd_is_rejected` | **PASS** |
| **AC-P4-02** | `soak_cmd` chạy 10 ngày đêm (`--days 10`) hoàn tất, không crash (`crashes == 0`), bảo toàn trạng thái | Chạy `python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json`; kết quả `days_completed: 10`, `crashes: 0`, duration 1.32s | **PASS** |
| **AC-P4-03** | `bench_cmd` đo hiệu năng có render Canvas 2D 1280x720: `avg_fps >= 60`, `p1_low_fps >= 30`, `load_ms <= 10000` | Chạy `python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json`; kết quả: `avg_fps: 69`, `p1_low_fps: 31`, `load_ms: 2` | **PASS** |
| **AC-P4-04** | Bộ test hồi quy toàn bộ hệ thống (176 tests) pass 100%, không suy giảm tính tương thích | Chạy `python -m unittest discover -s tests -v`; ghi tại `docs/proof/phase-4/regression.log` đạt 176/176 tests OK | **PASS** |
| **AC-P4-05** | Tài liệu đầy đủ: `CHANGELOG.md` (v1.0.0 đến v0.1.0), `docs/retro.md` hoàn chỉnh (số liệu 5 thành viên, AI errors, cải tiến), phản tư cá nhân 5 thành viên $\le 200$ từ | Kiểm tra `CHANGELOG.md`, `docs/retro.md`, và 5 file trong `docs/members/*.md` | **PASS** |
| **AC-P4-06** | Tag `phase-4` và Release v1.0.0 sẵn sàng trên nhánh `main` cho việc chấm tự động | Merge vào `main`, push tag `phase-4` lên remote `origin` | **PASS** |
