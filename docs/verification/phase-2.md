# Verification — QA Phase 2

> Người thực hiện: QA lead. Ngày: 2026-11-21.

## Phạm vi

Phase 2 Gather: cá bơi/sinh, Cá Sấu (patrol/chase/hit/recoil/invuln), nâng cấp (oxygen/hp), scenario validation, integration gather→quan.

## File test

| File | Loại | Số ca | Kết quả |
|------|------|-------|---------|
| `tests/test_gather_p2_units.py` | Unit | 43 | 43 pass |
| `tests/test_gather_p2_integration.py` | Integration | 8 | 8 pass |

## Tính năng chưa đạt / chưa test

- `--mode day`: chưa triển khai (headless từ chối mã 2). Không test.
- Shop mua nâng cấp: chỉ test `active_upgrades` truyền vào GatherSim, không test luồng mua/trả tiền.
- Quán 6 món (3 món mới: canh_chua_ca_loc, ca_keo_nuong, lau_mam): menu chưa có → chưa test (lỗi thuộc contract/menu, đã báo nhóm).
- Day cycle (DAY_CYCLE_V1_1): chưa có trên nhánh này.

## Lệnh chạy test

```powershell
# Chỉ P2
$env:PYTHONPATH = "tests;."; python -m unittest tests.test_gather_p2_units tests.test_gather_p2_integration -v

# Toàn bộ Gather P1 + P2
$env:PYTHONPATH = "tests;."; python -m unittest tests.test_gather_p1_units tests.test_gather_p1_integration tests.test_gather_p2_units tests.test_gather_p2_integration -v
```

## Ghi chú

- Test P1 `I5_default_six_static_schools` lỗi đúng vì P2 đổi `fish_initial` từ danh sách → int(8). Ghi nhận, không sửa test P1 cho xanh — cần cập nhật I5 theo luật P2 mới (commit riêng, ghi lý do).
- Test P1 `test_smoke_p1.Contract.test_gather_snapshot_has_gather_fields` lỗi vì len(fish)==6 → 8. Test do giảng viên cấp, không sửa, đã báo nhóm qua docs/clarify.md.
- Mọi thông số đọc từ `game.contract.json`, không hard-code trong test.
- Mọi RNG qua `Streams`, đảm bảo determinism.
