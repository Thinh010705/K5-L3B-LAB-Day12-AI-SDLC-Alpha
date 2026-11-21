# Xác minh phần Integrator — Giai đoạn 1 (nhóm Alpha)

**Người phụ trách:** @Thinh010705  
**Trạng thái:** **CHƯA XÁC MINH** — đây là danh sách kiểm tra nghiệm thu, **không** phải bằng chứng đã chạy test.

| Tiêu chí | Cách kiểm tra / lệnh | Bằng chứng cần lưu | Kết quả thực tế |
|---|---|---|---|
| `TEAM.md` thống nhất với contract nhóm | `python3 tools/check_team.py` | `docs/proof/phase-1/team-check.txt` | Chưa chạy |
| Chuyển kho Gather → Quan khớp event và snapshot | `test_round_trip_inventory_event_and_quan_snapshot` | `docs/proof/phase-1/integrator-tests.log` | Chưa chạy |
| Dừng do giới hạn tick không tạo/ghi đè tệp kho | `test_tick_limit_does_not_create_or_overwrite_inventory` | Cùng tệp log tích hợp | Chưa chạy |
| Kho đầu vào không hợp lệ bị từ chối trước khi tạo output | `test_invalid_inventory_fails_before_output_is_written` | Cùng tệp log tích hợp | Chưa chạy |
| Tham số sai / xung đột cấu hình kho bị từ chối | `test_stock_conflict_and_wrong_mode_flags_rejected` | Cùng tệp log tích hợp | Chưa chạy |
| Cùng seed và đầu vào tạo kết quả giống từng byte | `test_same_seed_same_input_byte_identical_round_trip` | Cùng tệp log tích hợp | Chưa chạy |
| Nguyên liệu trong thực đơn tương thích với Gather | `test_recipes_and_default_gather_kinds_are_compatible` | Cùng tệp log tích hợp | Chưa chạy |
| Kiểm thử hồi quy sẵn có | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | `docs/proof/phase-1/all-tests.log` | Chưa chạy |

## 1. Cách thu thập bằng chứng thật

Chạy từ thư mục gốc repo:

```bash
mkdir -p docs/proof/phase-1
set -o pipefail
PYTHONPATH=tests:. python3 -m unittest discover -s tests -p 'test_integration_alpha.py' -v 2>&1 | tee docs/proof/phase-1/integrator-tests.log
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v 2>&1 | tee docs/proof/phase-1/all-tests.log
python3 tools/check_team.py 2>&1 | tee docs/proof/phase-1/team-check.txt
```

Sau khi chạy, thay `Chưa chạy` bằng `Đạt` hoặc `Chưa đạt` **theo output thực tế** và dẫn liên kết tới tệp bằng chứng trong `docs/verification/phase-1.md` chính thức của nhóm. Không xóa log lỗi hoặc che giấu các blocker.

## 2. Danh sách rà soát trước khi gộp code

- [ ] Thành viên Gather xác nhận hợp đồng chuyển kho.
- [ ] Thành viên Quan xác nhận hợp đồng chuyển kho.
- [ ] Thành viên UI xác nhận hợp đồng snapshot.
- [ ] Thành viên QA rà soát các giả định của bộ kiểm thử.
- [ ] Integrator rà soát commit `main` sau khi merge.
- [ ] Tag `phase-1` khớp trạng thái đã kiểm thử và mốc chính thức của lab.
