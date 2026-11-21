# Nhóm Alpha — Giao diện Snapshot, Event và Input v1.1

**Trạng thái:** Bản đề xuất để UI và chủ simulation rà soát.  
**Kế thừa:** `UI_SNAPSHOT_V1.md`; các trường v1.0 không bị TICKET-02 thay đổi vẫn được giữ nguyên.

## 1. Quy ước chung

- Tốc độ gameplay 60 tick/s; `tick` là bước đầu vào bên ngoài, `sim_tick` là số bước mô phỏng thực sự chạy. Trong trạng thái `paused`, `tick` vẫn tăng nhưng `sim_tick`/`phase_tick` và các timer gameplay đứng yên.
- Bản ghi chung `snapshot`: `type,tick,sim_tick,mode,phase,phase_tick,state,time_left_ticks,money,earned,reputation,score`.
- Bản ghi `event`: `type:"event",tick,phase,name,data`; mode `day` bổ sung trường `day` vào vỏ event.
- Dòng `end` mode `day` bổ sung `days_completed`; khi hoàn tất số ngày đã yêu cầu có `reason:"days_complete"`.
- Khi đang pause, snapshot dùng `state:"paused"`; UI đọc trạng thái mô phỏng, không tự tính lại tiền, uy tín, vật phẩm hay thời gian.

## 2. Snapshot Gather v1.1

Kế thừa các trường v1.0: `player`, `hold`, `hold_count`, `hold_capacity`, `nodes[]`, `fish[]`.

**Bổ sung:**

- `player.invuln_ticks`: số tick bất tử sau khi bị quái chạm. (Trường mới v1.1, không thuộc v1.0.)
- `monsters[]`: các quái có id, loại, vị trí, waypoint và trạng thái; dữ liệu fixture có `target_idx,state,state_ticks_left,recoil_dir` theo TICKET-02.
- `fish[].age_ticks` trong dữ liệu scenario/fixture phục vụ quy tắc cá bơi/sinh; UI phải tuân theo schema snapshot thực tế và đặc tả, không suy đoán thứ tự xuất hiện.
- Nếu bật mở rộng Lao: thêm `player.attack_cd_ticks`. Nếu bật mở rộng Sổ tay: thêm `ca_ho` (object hoặc null).

Sự kiện bổ sung:

| Tên | `data` |
|---|---|
| `monster_hit` | `monster_id,hp,lost,pos` |
| `fish_spawned` | `id,kind,pos` |
| `faint` do quái | `cause:"monster",lost,hp:0` |

Đối với `lost`, giữ thứ tự bỏ theo **LIFO**. UI có thể hiển thị các thay đổi từ event, nhưng trạng thái cuối cùng lấy từ snapshot.

## 3. Snapshot Quan v1.1

Giữ các trường của v1.0 (`player,stock,hand,stoves[],tables[],customers[]`). Phạm vi cấu hình mới gồm **2 bếp B1/B2, 4 bàn T1–T4 và 6 món**.

- `stock` là tồn vật lý, gồm nguyên liệu đã giữ chỗ; **tồn khả dụng** phải tính sau khi trừ phần `reserved` của khách.
- Trong mode `day`, menu khách được lọc theo `day_plan.dishes`, sau đó theo tồn khả dụng; trong mode `quan` độc lập, dùng cả 6 món.
- Tiền, `earned`, `reputation` và `score` là giá trị do simulation xuất; UI không tự điều chỉnh.

## 4. Snapshot mode `day` và Shop

Trong mode `day`, **mọi snapshot** thêm:

- `day`: ngày hiện tại.
- `day_plan`: kế hoạch gồm `dishes` và `ingredients`.
- `upgrades`: map nâng cấp **đã mua**.
- `active_upgrades`: map nâng cấp **đang hiệu lực** cho Ngày hiện tại.

`phase` có thể là `gather`, `quan` hoặc `shop`; snapshot Shop có `stock` dư từ ca Quan và `time_left_ticks` là thời gian Shop còn lại. Snapshot chuyển pha thuộc pha mới với `phase_tick: 0`.

Danh sách event vòng ngày/Shop:

| Tên | `data` |
|---|---|
| `day_start`, `phase_start` | `{}` |
| `day_plan` | `{dishes,ingredients}` |
| `paused`, `resumed` | `{}` |
| `bought` | `{upgrade,level,price,money}` |
| `buy_failed` | `{action,reason}` với `funds/max_level/out_of_stock/unknown` |
| `shop_end` | `{reason}` với `done/time` |

Các sự kiện mở rộng như `attack`, `monster_stunned`, `dish_burnt`, `vendor_trade`, `photo`, `released` chỉ áp dụng khi nhóm chọn và cấu hình extension tương ứng.

## 5. Hợp đồng input tương tác

- `pause` là boolean ở cả `gather`, `quan`, `day`, tác động ở cạnh lên. Khi pause, mọi hành động khác và `buy` bị bỏ qua; cạnh lên tiếp theo phát `resumed` rồi chạy gameplay ngay bước đó.
- `shop_done` là boolean, chỉ tác dụng ở Shop, cạnh lên.
- `buy` là **chuỗi khác rỗng**, chỉ chạy ở frame khai báo, không duy trì như nút đang giữ. Các giá trị lõi: `oxygen`, `hp`; mở rộng tùy theo `extensions`.
- `interact` và `catch` vẫn theo luật cạnh lên v1.0. Giữ nút xuyên đổi pha không tự tạo cạnh mới.
- Khi ở chế độ `day`, màn hình giới thiệu và kết quả là phần UI; không được tự tạo tick headless hay phát event gameplay ngoài contract.

## 6. Checklist kiểm tra UI và QA

- [ ] Snapshot ở Gather, Quan, Shop khớp field v1.1 thực tế.
- [ ] Đổi pha vẫn nhận được event `phase_start` và snapshot của pha mới.
- [ ] Menu kế hoạch ngày hiển thị đúng nguyên liệu; UI không sửa dữ liệu simulation.
- [ ] HUD hiển thị quái gần, oxy thấp, thời gian gần hết, 2 bếp/4 bàn.
- [ ] Pause không làm sim tick/timer tiếp tục chạy.
- [ ] Nâng cấp vừa mua hiển thị ngay nhưng chỉ áp dụng từ Ngày kế.
- [ ] Không ghi nhận checklist đạt trước khi có test/ảnh/log thật.
