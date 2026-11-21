# Verification Phase 3 — tiến độ integration

Ngày 2026-11-21. Nhánh `feature/integration-p3`. Bằng chứng cuối cùng phải cập nhật theo commit được gắn tag `phase-3` trên `main`.

| AC | Bằng chứng | Kết quả hiện tại |
| --- | --- | --- |
| AC-P3-01: schema file kho cá thể, từ chối kho đếm v1.2, giữ id/fresh và thay file nguyên tử | `tests/test_inventory_p3.py`; `docs/proof/phase-3/integration-inventory.md` | PASS ở lớp adapter, chưa kích hoạt manifest |
| AC-P3-02: file Gather → Quan và Day cùng tick; hàng ươn, giá, giữ chỗ, JSONL | Cần smoke trên mã Gather/Quan/Day v1.2 | CHƯA KIỂM |
| AC-P3-03: HUD độ tươi hoặc hàng ươn | Cần test UI sau chuyển snapshot | CHƯA KIỂM |
| AC-P3-04: phân tích tác động, quyết định schema và thứ tự tích hợp | `docs/adr/0001-phase-3-inventory-handoff.md` | PASS |
| AC-P3-05: regression P1–P2 còn hiệu lực | `docs/proof/phase-3/integration-inventory.md` | 168/168 PASS với manifest v1.1 |
| AC-P3-06: tag `phase-3` trên commit `main` | Cần tích hợp các lát, test trên main và đối chiếu tag | CHƯA KIỂM |

Test P1/P2 kỳ vọng kho đếm phải được cập nhật theo breaking change khi bật v1.2, ghi rõ lý do từng thay đổi; không sửa test để che lỗi luật.
