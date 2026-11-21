# ADR 0001 — Chuyển kho đếm sang cá thể ở Phase 3

Ngày: 2026-11-21. Trạng thái: đã chốt giao diện, đang tích hợp.

## Tác động

`inventory.py`, `headless.py`, `runner.py`, `live.py` là ranh giới file. `sim/gather.py` cấp id, giữ thứ tự giỏ và phát `gather_end`; `sim/quan.py` giữ nguyên cá thể, hao tươi và chọn nguyên liệu; `day.py` bàn giao trong cùng tick; `shop.py` giữ kho thô không hao; `scenario.py` và `scenario_day.py` kiểm fixture; `web/index.html` đọc snapshot mới. Test P1/P2 đang giả định bảng đếm cần thay kỳ vọng có lý do khi bật v1.2.

## Quyết định

- File v1.2 có đúng `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Kho rỗng là `{"items":[]}`. `id` duy nhất, khác rỗng; `kind` thuộc danh mục; `fresh` là số hữu hạn trong `[0,100]`. Giữ cả hàng ươn.
- Đầu đọc chọn schema theo `contract_version`; v1.2 từ chối bảng đếm với mã 2 trước khi ghi JSONL. Đầu ghi sắp bằng `ids.sort_by_id`, giữ nguyên giá trị số khi JSON round trip, ghi tạm cùng thư mục rồi `os.replace`.
- Gather sở hữu `I1,I2,…` theo thứ tự nhặt và bộ đếm phải sống qua phase/Ngày. LIFO theo thứ tự giỏ. Quan và Shop không tự đổi id hàng được bàn giao; hàng Shop mua dùng id kế tiếp.
- Trong Day, `gather_end.data.inventory` và kho được chuyển từ cùng một danh sách cá thể sau hao tươi của bước Gather. Quan bắt đầu hao ở bước kế. Không chuyển hàng Shop vào `gather_end`.

## Thứ tự tích hợp

1. Bộ đọc/ghi và test schema chạy với v1.1 chưa đổi manifest.
2. Gather, Quan, Day/Shop, scenario và HUD cùng chuyển sang cá thể. Bổ sung manifest và validator v1.2 khi các đầu đã sẵn sàng.
3. Smoke file Gather → Quan, smoke Day cùng tick, test ngưỡng 30, rồi regression còn hiệu lực. Sau đó mới đổi `game.contract.json` sang v1.2 và ghi bằng chứng trên commit bàn giao.

Không chuyển ngầm kho đếm thành cá thể vì không thể suy ra id và độ tươi lịch sử.
