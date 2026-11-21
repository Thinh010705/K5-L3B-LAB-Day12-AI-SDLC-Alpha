# Phase 2 – Tiến độ Integrator / Contracts (Alpha)

> Đây là checklist theo dõi công việc. **Không đánh dấu PASS cho các bài chưa chạy.**

## Nguồn yêu cầu

- TICKET-02 / Test Contract v1.1.
- Hợp đồng nhóm đã duyệt: `docs/contracts/INTEGRATION_V1_1.md`, `DAY_CYCLE_V1_1.md`, `UI_SNAPSHOT_V1_1.md`.

## Tình trạng đã được quan sát

| Công việc | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Baseline Phase 1 sau merge các nhánh | PASS, 74/74, 4.201 s | Terminal trước khi kích hoạt manifest v1.1; cần lưu log vào proof nếu chưa có |
| Hợp đồng tích hợp v1.1 | Nhóm đã xác nhận | Ba file `docs/contracts/*V1_1.md` |
| Tạo bản đề xuất manifest v1.1 | Đã tạo, JSON hợp lệ, đủ số lượng | `docs/contracts/game.contract.v1_1.proposed.json` |
| Kiểm thử runtime với manifest mới, khi code còn v1.0 | FAIL: 16 failures, 4 errors, 40 tests được ghi nhận | Validator v1.0 từ chối `keo_neo` ở N5; không coi đó là test v1.1 PASS |
| Kiểm tra dữ liệu tĩnh TICKET-02 | CHƯA ĐÁNH GIÁ | `tools/check_contract_p2.py` + `tests/test_contract_p2_data.py` – điền sau khi chạy |
| Cập nhật parser/validator v1.1 | CHƯA XÁC NHẬN | Chủ code phối hợp Integrator |
| Gather, Quan, day, Shop, UI tích hợp v1.1 | CHƯA XÁC NHẬN | Smoke thực tế và test của nhóm |
| Regression sau cập nhật code | CHƯA CHẠY | Chạy trên commit cùng manifest đã áp dụng |
| Tag `phase-2` trên `main` | CHƯA XÁC NHẬN | `git show phase-2 --no-patch` |

## Điều kiện để kích hoạt `game.contract.json` v1.1

1. Gather validator chấp nhận `keo_neo`/`ca_keo`, đúng số đàn, điểm sinh và quái.
2. Quan hỗ trợ 6 món, 2 bếp, 4 bàn và công thức theo manifest.
3. Runner/CLI hỗ trợ `--mode day`, `--days 1..5`, pause và trạng thái xuyên ngày.
4. QA cập nhật các test v1.0 có kỳ vọng bị TICKET-02 thay thế; giữ regression vẫn còn hiệu lực.
5. Tích hợp nhánh, áp dụng manifest, chạy lại smoke và regression **trên commit cụ thể**.

## Bằng chứng nghiệm thu cần bổ sung

- `docs/proof/phase-2/manifest-audit.log` – kiểm tra dữ liệu tĩnh.
- `docs/proof/phase-2/integration.*` – Gather→Quan, stock giao nhận.
- `docs/proof/phase-2/day-one.*` – vòng một ngày đến Shop đóng.
- `docs/proof/phase-2/day-multi.*` – nhiều ngày, nâng cấp có hiệu lực trễ.
- `docs/proof/phase-2/regression.log` – các test còn hiệu lực.
- `docs/verification/phase-2.md` – AC → bằng chứng → PASS/FAIL/BLOCKED trên commit bàn giao.

**Đề nghị phân công:** Gather và Quan cập nhật module tương ứng; người phụ trách Day/Runner đảm nhiệm state machine và CLI; QA cập nhật test; Integrator đối chiếu giao diện, smoke và nghiệm thu trên `main`.
