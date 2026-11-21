# Nhóm Alpha — Hợp đồng vòng ngày và Shop v1.1

**Phạm vi:** Mode `day` của Phase 2; phối hợp giữa Gather, Quan, Shop và UI.  
**Nguồn chuẩn:** TICKET-02/Test Contract v1.1. Đây là tài liệu bàn giao giao diện, không phải thông báo tính năng đã được cài đặt.

## 1. Vòng đời của một Ngày

```text
DayIntro (UI) → gather → EveningIntro (UI) → quan → DayResult (UI) → shop
                                      ↓                                     ↓
                                 kho bàn giao                        ngày kế / Summary
```

- Mode `day` cho `--days` từ 1 đến 5, mặc định 1; `days_completed` đếm **số Shop đã đóng**, không phải số ca Gather hay Quan hoàn tất.
- Kể cả Gather ngất, ca Quan vẫn bắt đầu với kho rỗng.
- Tiền, tổng thu (`earned`), uy tín và cấp nâng cấp duy trì xuyên ngày; mỗi Ngày mới khôi phục oxy và máu theo `active_upgrades`, giỏ được làm mới.
- Kho dư sau Shop không được chuyển thành giỏ ngày kế.

## 2. Kế hoạch 5 Ngày chuẩn

| Ngày | Món dự kiến (`dish_id`: số suất) | Nguyên liệu cần (`kind`: số lượng) |
|---|---|---|
| 1 | `ca_loc_nuong_trui`: 3, `goi_bong_sung`: 3 | `ca_loc`: 3, `bong_sung`: 6 |
| 2 | `ca_loc_nuong_trui`: 2, `lau_ca_linh_dien_dien`: 2 | `ca_loc`: 2, `ca_linh`: 6, `bong_dien_dien`: 2 |
| 3 | `goi_bong_sung`: 2, `canh_chua_ca_loc`: 2, `ca_keo_nuong`: 2 | `bong_sung`: 4, `ca_loc`: 2, `bong_dien_dien`: 2, `ca_keo`: 4 |
| 4 | `lau_mam`: 1, `ca_loc_nuong_trui`: 2, `goi_bong_sung`: 1 | `ca_linh`: 2, `ca_keo`: 1, `keo_neo`: 1, `bong_dien_dien`: 1, `ca_loc`: 2, `bong_sung`: 2 |
| 5 | `lau_mam`: 1, `lau_ca_linh_dien_dien`: 1, `ca_loc_nuong_trui`: 1 | `ca_linh`: 5, `ca_keo`: 1, `keo_neo`: 1, `bong_dien_dien`: 2, `ca_loc`: 1 |

- `day_plan` là mảng 5 object `{day,dishes,ingredients}`. `ingredients` tính bằng tổng công thức × số suất; không tự nhập số không khớp công thức.
- Trong mode `day`, chỉ chọn món có id trong kế hoạch và đủ tồn **khả dụng**. Khách vẫn có thể gọi tiếp món nằm trong kế hoạch dù đã đạt số suất dự kiến.
- Mode `quan` chạy độc lập có thể chọn từ cả 6 món.

## 3. Giữ trạng thái và nâng cấp

| Thuộc tính | Qua ca Gather/Quan | Qua Shop sang Ngày mới |
|---|---|---|
| `money`, `earned` | Giữ và cập nhật | Giữ (trừ tiền khi mua) |
| `reputation` | Giữ và cập nhật | Giữ |
| `upgrades` | Giữ cấp đã mua | Giữ |
| `active_upgrades` | Cấp hiệu lực trong Ngày | Cập nhật từ `upgrades` khi dựng Ngày mới |
| `stock` từ Gather | Chuyển sang Quan | Không chuyển sang giỏ Ngày mới |
| `hold` | Chốt khi kết thúc Gather | Làm mới ở Ngày kế |

**Nâng cấp lõi:**

- `oxygen`: cấp 1 giá 200, 45 s; cấp 2 giá 400, 60 s.
- `hp`: cấp 1 giá 250, 4 HP; cấp 2 giá 500, 5 HP.

Nếu người chơi đủ tiền bằng đúng giá thì mua thành công. Mua lỗi không làm thay đổi trạng thái tiền/cấp. `earned` không bị trừ khi mua.

## 4. Quy tắc chuyển pha, tick và Shop

- Đầu Ngày phát theo thứ tự: `day_start`, `day_plan`, `phase_start` (gather).
- Sau `gather_end` dựng Quan và phát `phase_start` (quan) trong cùng tick; sau `quan_end` dựng Shop và phát `phase_start` (shop) trong cùng tick.
- Pha mới bắt đầu gameplay từ **bước tiếp theo**; snapshot chuyển pha là pha mới và `phase_tick = 0`.
- Trong Shop: xử lý `buy` trước `shop_done`, kể cả khi Shop còn đúng một tick. `shop_done` ở cạnh lên kết thúc với `shop_end(reason="done")`; hết 600 tick hoạt động thì `shop_end(reason="time")`.
- Khi Shop đóng: tăng `days_completed`; nếu đủ ngày thì `end(reason="days_complete")`, chưa đủ thì dựng ngay Ngày mới và áp cấp mới mua cho ngày đó.
- Pause làm ngừng thời gian mô phỏng, không làm ngừng **tick ngoài**.

## 5. Đầu vào kiểm thử theo TICKET-02

- Tình huống `day` có thể dùng các khối `gather`, `quan` như mẫu mỗi Ngày và khối `day {money,earned,reputation,upgrades,day_plan}` làm trạng thái xuyên ngày. Khi khai tiền ban đầu, khai cả `money` và `earned`, với `0 ≤ money ≤ earned`.
- Cấm `quan.stock` và `quan.reputation` trong mode `day`.
- Trong mode `day`, `day.day_plan` có thể ghi đè kế hoạch theo ngày bằng `dishes`; tính lại `ingredients` và kiểm tra giá trị nếu được khai.
- Test hồi quy phải kiểm tra ít nhất một Ngày, nhiều Ngày, mua thành công/thất bại, pause, chuyển pha khi Gather ngất và `days_completed`.

## 6. Phần cần xác nhận giữa các thành viên

- **Chủ `day`/runner:** hình thức gọi Gather/Quan từ cùng phiên và chuyển trạng thái xuyên ngày.
- **Gather:** cung cấp kết quả chốt giỏ; giữ đúng kho khi `time`/`docked`, mất khi `fainted`.
- **Quan:** nhận kho, kế hoạch ngày và trạng thái tiền/uy tín; giữ chỗ nguyên liệu đúng.
- **UI:** DayIntro/EveningIntro/DayResult/Summary là màn hình hiển thị, không được làm sai tick headless.
- **QA:** cung cấp fixture/test và log tại `docs/proof/phase-2/`; kết quả chưa chạy không được ghi là PASS.
