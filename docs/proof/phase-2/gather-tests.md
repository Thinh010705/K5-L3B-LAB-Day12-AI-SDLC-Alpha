# Gather Phase 2 — Kết quả test

> Chạy trên nhánh `feature/qa-p2`, Windows, Python 3.13, 2026-11-21.

## Lệnh

```powershell
$env:PYTHONPATH = "tests;."
python -m unittest tests.test_gather_p2_units tests.test_gather_p2_integration -v
```

## Kết quả

### Unit test (`test_gather_p2_units.py`) — 43 test, 43 pass

| Nhóm | Ca | Mô tả | Kết quả |
|------|-----|--------|---------|
| FishSwim | F1 | 8 đàn spawn đầu ca, id F1..F8, vị trí khác nhau | ✅ |
| FishSwim | F2 | Cùng seed giống, seed khác khác | ✅ |
| FishSwim | F3 | Cá bơi fish_speed/60 m/tick, age_ticks tăng | ✅ |
| FishSwim | F4 | Phản xạ mép x (fish_x) | ✅ |
| FishSwim | F5 | Phản xạ mép d theo loài (ca_keo [22,28]) | ✅ |
| FishSwim | F6 | age_ticks:119 → đổi hướng ở bước 120 | ✅ |
| FishSwim | F7 | Sinh tại phase_tick 360 | ✅ |
| FishSwim | F7b | Trần fish_max → không sinh | ✅ |
| FishSwim | F7c | random_fish:false → không bơi/không sinh | ✅ |
| FishSwim | F8 | Bắt ca_keo yield 2 | ✅ |
| FishSwim | F8b | Hái keo_neo node | ✅ |
| Monster | M1 | patrol 1.0 m/s, đổi target_idx khi tới waypoint | ✅ |
| Monster | M2 | d≥10, cách≤10 → chase | ✅ |
| Monster | M2b | d<10 → không chase | ✅ |
| Monster | M2c | chase, >exit_radius → patrol | ✅ |
| Monster | M3 | monster_hit, LIFO floor(n/2), invuln 90, recoil 60 | ✅ |
| Monster | M4 | Bất tử → không hit | ✅ |
| Monster | M5 | 2 quái, chỉ 1 hit (gần nhất) | ✅ |
| Monster | M5b | Hòa khoảng cách: 1 hit | ✅ |
| Monster | M6 | Recoil di chuyển, 60 bước → patrol | ✅ |
| Monster | M6b | Trùng tâm → recoil_dir [1,0] | ✅ |
| Monster | M7 | HP 1 + hit → faint(monster), gather_end | ✅ |
| Monster | M8 | Choke trước monster_hit; choke HP→0 → bỏ quái | ✅ |
| Monster | M9 | Day 1: M1; Day 3: M1+M2 | ✅ |
| Upgrade | U1 | oxygen lv1 → 2700 ticks | ✅ |
| Upgrade | U2 | hp lv2 → 5 | ✅ |
| Upgrade | U3 | Kết hợp oxygen+hp | ✅ |
| Upgrade | U4 | Cấp không tồn tại → BadInput | ✅ |
| Upgrade | U5 | Kiểu sai → BadInput | ✅ |
| Upgrade | U6 | player_limits trả đúng giá trị | ✅ |
| Scenario | S1 | recoil timer=0 → BadInput | ✅ |
| Scenario | S2 | recoil_dir không đơn vị → BadInput | ✅ |
| Scenario | S3 | target_idx=2 → BadInput | ✅ |
| Scenario | S4 | kind lạ → BadInput | ✅ |
| Scenario | S5 | fish age_ticks âm → BadInput | ✅ |
| Scenario | S6 | hold ca_keo/keo_neo hợp lệ | ✅ |
| Scenario | S7 | day ngoài [1,5] → BadInput | ✅ |
| Scenario | S8 | day=True (bool) → BadInput | ✅ |
| Sanity | P2-1 | fish_initial là int (8) | ✅ |
| Sanity | P2-2 | fish_speed tồn tại | ✅ |
| Sanity | P2-3 | monsters tồn tại | ✅ |
| Sanity | P2-4 | shop.upgrades tồn tại | ✅ |
| Sanity | P2-5 | fixture depths hợp lý | ✅ |

### Integration test (`test_gather_p2_integration.py`) — 8 test, 8 pass

| Ca | Mô tả | Kết quả |
|-----|--------|---------|
| IP1 | Cùng seed byte-identical (cá bơi + quái) | ✅ |
| IP2 | Snapshot 300 tick: cá di chuyển | ✅ |
| IP3 | gather ca_keo → inventory-out → quan đọc | ✅ |
| IP4 | Snapshot có monsters (Day 1 = M1) | ✅ |
| IP5 | Seed khác → cá spawn khác | ✅ |
| SP1 | Quái loài lạ → mã 2 | ✅ |
| SP2 | monster recoil timer=0 → mã 2 | ✅ |
| SP3 | fish age_ticks âm → mã 2 | ✅ |

### Test P1 regression — 36 test

- 35/36 pass. Test `I5_default_six_static_schools` **lỗi đúng** vì P2 đổi `fish_initial` từ danh sách 6 đàn sang `int(8)`. Đây là thay đổi có chủ đích của luật P2 (xem QA-p2-handoff.local dòng 20–23).

## Tổng cộng: 87 test, 86 pass, 1 expected fail (P1 I5)
