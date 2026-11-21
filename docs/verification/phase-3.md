# Nghiệm thu Phase 3 – TICKET-03: Mùa Nước Nổi

**Nhóm:** Alpha  
**Repository:** `Thinh010705/K5-L3B-LAB-Day12-AI-SDLC-Alpha`  
**Test Contract:** v1.2  
**Nhánh nghiệm thu:** `main`  
**Tag dự kiến:** `phase-3`  
**Trạng thái hồ sơ:** **PENDING** – chỉ đổi thành PASS sau khi kiểm tra bằng chứng thực tế.

> Quy tắc ghi nhận: không đánh dấu PASS chỉ vì PR đã merge. Các bằng chứng phải được tạo từ mã nguồn tích hợp trên `main`; nếu chưa kiểm tra thì ghi `PENDING`, khi sai ghi `FAIL` cùng issue/commit khắc phục.

## 1. Phạm vi thay đổi

- Thay kho đếm theo loại (v1.1) thành kho **cá thể** `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}` (v1.2).
- ID nguyên liệu duy nhất, tăng xuyên pha/ngày; bảo toàn `id`, `kind`, `fresh` khi bàn giao.
- Gather giảm 0,5 điểm tươi/s, Quan giảm 0,25 điểm tươi/s (60 tick/s); pause không giảm.
- Khi `fresh < 30`, phát `spoiled` một lần khi vượt ngưỡng; hàng ươn không dùng nấu.
- Giữ nguyên liệu theo ID, ưu tiên tươi nhất; mất nguyên liệu do ươn thì thả toàn bộ giữ chỗ và thử lại đúng một lần.
- Khi bắt đầu nấu, giá được cố định theo trung bình độ tươi; tiền boa tính trên giá sau điều chỉnh.
- JSONL, scenario, giao diện và Day cập nhật theo schema v1.2.
- Mở rộng chỉ nghiệm thu các mục thực sự bật trong `game.contract.json` (xem `extensions`).

## 2. Thông tin mã nguồn và thực thi

| Trường | Giá trị/bằng chứng |
|---|---|
| Commit mã nguồn kiểm thử | Xem `docs/proof/phase-3/git-baseline.txt` (nếu được tạo) |
| Commit bàn giao | Lấy bằng `git rev-parse 'phase-3^{commit}'` **sau khi gắn tag** |
| Contract | `game.contract.json`: phải có `contract_version: "1.2"` |
| Lệnh test | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` |
| Log regression | `docs/proof/phase-3/regression.log` |
| Log smoke | `docs/proof/phase-3/smoke-summary.txt` |
| UI manual test | Ảnh hoặc video thực tế do UI/QA bổ sung |

## 3. Ma trận Acceptance Criteria

**Trạng thái mặc định PENDING:** thay bằng PASS hoặc FAIL sau khi đối chiếu file bằng chứng. Các file `*.jsonl` chỉ là đầu ra thô; cần xác minh nội dung event/snapshot, không chỉ kiểm tra file có tồn tại.

| Mã | Điều kiện chấp nhận | Cách kiểm chứng và bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 | Manifest v1.2 và kho `{items:[{id,kind,fresh}]}` hợp lệ; file kho đếm hoặc sai schema bị từ chối mã 2 trước khi tạo output | `manifest-audit.txt`, `inventory-count-rejection.stderr`, test validation | PENDING |
| AC-P3-02 | ID duy nhất tăng xuyên pha/ngày, không tái sử dụng; hàng mua mới nếu có vendor có ID mới | Unit/integration tests cho ID, `day` nhiều ngày | PENDING |
| AC-P3-03 | Gather hao tươi 0,5/s, hàng mới bắt đầu hao ở tick sau; ngưỡng 30 và `spoiled` đúng tick, đúng một lần | `freshness-threshold.jsonl` và unit test biên | PENDING |
| AC-P3-04 | `gather_end.data.inventory` giống file, ghi nguyên tử đúng một lần; ngất xuất `items:[]`; giới hạn tick không ghi đè file | `gather-handoff.jsonl`, `inventory-v12.json`, tests inventory | PENDING |
| AC-P3-05 | Qua `quan --inventory` giữ chính xác ID/kind/fresh; quán giảm 0,25/s, kể cả hàng giữ chỗ | `quan-stock-tick0.jsonl`, Quan tests | PENDING |
| AC-P3-06 | Hàng giữ bị ươn: nhả cả phần giữ, thử giữ lại một lần theo `order_tick` và id bàn; thiếu thành `unfulfillable` | Quan reservation/stock tests và event proof | PENDING |
| AC-P3-07 | Nấu tiêu đúng ID đã giữ; `base_price=floor(price*avg_fresh/100)`, boa dựa trên giá đã chốt | Quan pricing tests, `cook_started`/`served` events | PENDING |
| AC-P3-08 | Trong Day, chuyển Gather → Quan cùng tick, không giảm tươi thêm; chạy 1 ngày/multi-day và giữ định danh | `day-1.jsonl`, Day integration tests | PENDING |
| AC-P3-09 | Snapshot/event v1.2: hold/stock/reserved theo cá thể; `spoiled` có id/kind/location; mất hàng theo LIFO | JSONL contract tests và log cụ thể | PENDING |
| AC-P3-10 | Pause không làm hao tươi; thứ tự tick và deterministic outputs đúng; regression P1–P2 còn hiệu lực đạt | `regression.log`, test pause và determinism | PENDING |
| AC-P3-11 | UI/HUD hiển thị độ tươi hoặc nhận diện hàng ươn, có bằng chứng chụp từ bản chơi | Ảnh/video UI và checklist manual | PENDING |
| AC-P3-12 | Extension được khai trong manifest (đối với nhóm 5 người phải có ít nhất 1), chạy đúng luật và có test/bằng chứng | `extensions` trong manifest; test `current` hoặc `reservations`; README | PENDING |
| AC-P3-13 | CHANGELOG/clarify/AI usage/retro, phân tích tác động và lý do sửa test cũ; code các thành viên đã tích hợp | Docs, commit/PR history, `docs/plan/phase-3-impact.md` | PENDING |
| AC-P3-14 | Tag `phase-3` được push và trỏ tới commit nghiệm thu trên `main` | `git rev-parse 'phase-3^{commit}'`, `git rev-parse origin/main`, `git ls-remote --tags origin 'refs/tags/phase-3*'` | PENDING |

## 4. Kịch bản smoke cần lưu

1. **Ngưỡng tươi:** dựng `gather.hold` có I1 fresh=30; chạy một bước, phải phát `spoiled` tick=1 tại `hold`.
2. **Bàn giao qua hai tiến trình:** Gather với I1 fresh=100 + interact ở bến; dùng `--inventory-out`, mở Quan `--inventory` tại tick 0; so `id`, `kind`, `fresh` chính xác.
3. **Kho sai:** đưa file đếm cũ vào `quan --inventory` dưới manifest v1.2; phải exit code 2 trước khi tạo file JSONL.
4. **Day:** chạy `--mode day --days 1`, kiểm tra end `days_completed=1`, `reason=days_complete`; kiểm tra chuyển pha và độ tươi qua snapshot/events.
5. **Regressions:** chạy đầy đủ tests và xem có test P1–P2 bị thay do thay đổi contract hay không; với mỗi test đổi cần ghi lý do.
6. **UI & extension:** chơi thử thủ công; ghi ảnh/video và đối chiếu với `extensions` thực tế.

## 5. Regression và các test thay đổi

| Test/nhóm test | Luật cũ | Luật mới v1.2 | Lý do cập nhật | Kết quả |
|---|---|---|---|---|
| Inventory P1–P2 | Đếm theo loại | Cá thể ID/kind/fresh | Thay thế schema ở TICKET-03 | CHƯA ĐỐI CHIẾU |
| Gather/Quan P1–P2 | Hàng không hao tươi | Hao tươi, hàng ươn và reserved theo ID | TICKET-03 thay đổi luật | CHƯA ĐỐI CHIẾU |
| Day P2 | Bàn giao kho đếm | Bàn giao cá thể, không hao thêm ở tick đổi pha | TICKET-03 thay đổi luật | CHƯA ĐỐI CHIẾU |

**Khi test cũ không còn hợp lệ:** phải cập nhật fixture/assertion theo phiên bản hoặc giữ fixture v1.0/v1.1 để kiểm tra tương thích ngược. Không xóa test chỉ để bộ test xanh.

## 6. Vấn đề tồn đọng / ngoại lệ

| ID | Vấn đề | Mức ảnh hưởng | Cách xử lý / liên kết |
|---|---|---|---|
| — | Chưa xác nhận từ log thực tế | — | Cập nhật sau khi chạy test |

## 7. Kết luận nghiệm thu

**PENDING.** Chỉ điền `PASS` khi từng AC bắt buộc có test/bằng chứng đúng từ `main`, UI được kiểm thủ công, extension được xác minh và toàn bộ regression còn hiệu lực đạt. Sau đó commit bộ hồ sơ, xác nhận trạng thái `main` sạch, tạo và push tag `phase-3`.

**Mốc thời gian:** TICKET-03 quy định deadline là phút 2:30 của buổi lab. Nếu nộp sau mốc, giữ thời gian commit/tag thực tế; không sửa tag hoặc ghi thời điểm không đúng.
