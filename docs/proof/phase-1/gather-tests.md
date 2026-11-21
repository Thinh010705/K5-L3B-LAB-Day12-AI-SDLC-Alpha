# Bằng chứng test Gather Phase 1 (QA)

- Ngày chạy: 2026-11-21 · Nhánh: `feature/qa` (tách từ `dattt`) · Commit luật được kiểm: `6abf155` (Implement Phase 1 gather mechanics)
- Môi trường: Windows 11, Python 3.13.12. `python3` trên máy là stub WindowsApps (mã 9009), nên dùng một bản sao tạm `python3.exe` của Python 3.13 đặt đầu PATH để chạy các smoke test hộp đen.
- Lệnh: `PYTHONPATH="tests;." python3 -m unittest discover -s tests -v`
- Kết quả: **68 test, OK** (32 test có sẵn + 36 test mới).

## Test mới
| File | Ca | Số test |
|---|---|---|
| `tests/test_gather_p1_units.py` | O1–O9 (oxy, lặn/nổi, ngạt, ngất), G1–G7 (hái, giỏ), C1–C9 (bắt cá, hồi chiêu), E1–E5 (kết thúc), kiểm fixture | 31 |
| `tests/test_gather_p1_integration.py` | I1–I5 (`--inventory-out` → `quan --inventory`, ngất ghi kho rỗng, `tick_limit` không ghi kho, tất định từng byte, 6 đàn cá đứng yên) | 5 |

Các ca integration gọi `chonoi.headless.main(argv)` ngay trong tiến trình, nên chạy được cả khi máy không có `python3`.

## Kiểm tra đột biến (test có bắt được lỗi thật không)
Mỗi lần sửa sai một chỗ trong `chonoi/sim/gather.py`, chạy bộ test mới, rồi khôi phục file:

| Đột biến | Kết quả |
|---|---|
| bán kính `<=` → `<` | bị bắt (3 failure, 1 error) |
| `faint.lost` không đảo thứ tự | bị bắt (1) |
| hồi chiêu cho bắt khi `catch_cd_ticks <= 1` | bị bắt (2) |
| choke `>=` → `>` | bị bắt (3) |
| `oxygen_empty` phát mọi tick khi oxy = 0 | bị bắt (3) |
| bắt cá xong không xóa đàn cá | bị bắt (2) |
