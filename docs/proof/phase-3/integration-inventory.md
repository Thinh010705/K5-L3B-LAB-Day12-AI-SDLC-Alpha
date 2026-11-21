# Bằng chứng lát integration kho v1.2

Nhánh: `feature/integration-p3` (trước khi tích hợp Gather/Quan/Day v1.2). Ngày 2026-11-21.

| Lệnh | Kết quả |
| --- | --- |
| `PYTHONPATH=tests:. python3 -m unittest tests.test_inventory_p3 tests.test_integration_alpha -v` | 10/10 PASS. Kiểm schema kho cá thể, id trùng, fresh sát 30, ghi/đọc và smoke kho v1.1. |
| `PYTHONPATH=tests:. python3 -m unittest discover -s tests -q` | 168/168 PASS, 4.416 s, chạy với quyền mở socket localhost cho `test_live`. |
| `git diff --check` | PASS. |

Lần chạy đầy đủ trong sandbox cho 167 PASS và `test_live` lỗi `PermissionError` tại `socket.bind`; chạy lại riêng ngoài sandbox 1/1 PASS, sau đó chạy toàn bộ ngoài sandbox 168/168 PASS. Đây là lỗi quyền môi trường, không phải lỗi luật.

Chưa chạy smoke file v1.2 từ Gather sang Quan vì hai mô phỏng hiện vẫn sử dụng kho đếm và manifest vẫn là 1.1. Không tính phần đó là PASS.
