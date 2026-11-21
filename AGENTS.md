# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
  - PowerShell: `$env:PYTHONPATH = "tests;."; python3 -m unittest discover -s tests -v` (nếu `python3` là stub WindowsApps thì smoke test hộp đen trả mã 9009 — tắt App execution alias hoặc cài Python có `python3`).
  - Chỉ luật Gather P1: `PYTHONPATH=tests:. python3 -m unittest tests.test_gather_p1_units tests.test_gather_p1_integration -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- Test của QA: `tests/test_gather_p1_units.py` (ca O/G/C/E, dựng qua `Session` + `LiveInputs`), `tests/test_gather_p1_integration.py` (ca I, gọi `chonoi.headless.main`). Đổi luật Gather thì chạy lại cả hai; kết quả ghi ở `docs/proof/phase-1/`.
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- **`verify-contract`** (`.agents/skills/verify-contract/SKILL.md`): Kiểm tra tính toàn vẹn của `game.contract.json`, kiểm tra danh sách thành viên `TEAM.md`, và chạy full 176 test hồi quy trước khi merge nhánh.
- **`run-soak-bench`** (`.agents/skills/run-soak-bench/SKILL.md`): Tự động chạy soak test 10 ngày đêm (`chonoi.soak`) và đo hiệu năng render Canvas 2D (`chonoi.bench`), kiểm tra các ràng buộc FPS/Crash và xuất file bằng chứng vào `docs/proof/phase-4/`.
