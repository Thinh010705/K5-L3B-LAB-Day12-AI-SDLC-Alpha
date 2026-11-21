# Phân tích tác động và phối hợp Phase 3

**TICKET-03:** Mùa Nước Nổi – Test Contract v1.2

## Ma trận tác động

| Module / vai trò | Nội dung cần đổi | Vị trí cần rà soát | Kiểm thử cần có | Phụ thuộc |
|---|---|---|---|---|
| Integrator / Contract | version 1.2, schema item, validator, migration, file atomic và ID xuyên ngày | `chonoi/contract*.py`, `inventory*.py`, `ids.py`, `game.contract.json` | valid/invalid/duplicate/old count, atomic write | Khóa API trước |
| Gather | `hold` cá thể, hao tươi, `spoiled`, `lost` LIFO, event inventory cá thể | `chonoi/sim/gather.py`, `scenario.py` | ngưỡng tick1, ngất, tick-limit, initial ID, độ tươi | Inventory API |
| Quan | `stock` cá thể, reserved ID, re-reserve, `unfulfillable`, giá theo fresh | `chonoi/sim/quan.py`, `scenario.py` | stale reserved, tie-break, pricing floor, tips | Inventory API |
| Day / Shop | Bàn giao cùng tick, ID qua ngày, không hao extra, hàng mua ở Shop nếu bật vendor | `chonoi/day.py`, `shop.py`, `runner.py` | handoff, nhiều ngày, shop, pause | Gather + Quan |
| UI / HUD | Hiển thị fresh/ươn và snapshot dạng list | `chonoi/web/`, các client UI thực tế | thử chơi, screenshot/video | Snapshot API |
| QA / Extension | Regression P1–P2, fixture v1.2, test current/reservations nếu bật | `tests/`, `docs/proof/phase-3/` | boundary, deterministic, extension | Tất cả |

## Quy tắc phối hợp

- Owner gửi tên nhánh/PR và test command trước khi Integrator merge.
- Không thay đổi contract chung khi chưa báo các consumer của API.
- Sau từng lần merge, chạy test module và kiểm tra `game.contract.json` còn nhất quán.
- Không khởi động migration phá `main` khi một đầu bàn giao chưa hỗ trợ kho cá thể.
- Nếu test P1/P2 bị thay thế: ghi rõ tên test, giả định cũ, điều khoản TICKET-03 và test thay thế vào báo cáo nghiệm thu.
- Mở rộng ưu tiên `current` theo phương án của nhóm; chỉ ghi "đã triển khai" khi manifest + code + test chứng minh.

## Nhánh / bản bàn giao

- Nhánh phần việc tham khảo: `feature/integration-p3`, `feature/gather-p3`, `feature/quan-p3`, `feature/ui-p3`, `feature/qa-p3`.
- Bản bàn giao: commit tích hợp trên `main` + `docs/verification/phase-3.md` + `docs/proof/phase-3/` + `phase-3`.
- Đóng góp cá nhân: đối chiếu commit/PR thực tế; không suy từ phân công.
