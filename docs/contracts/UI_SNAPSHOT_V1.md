# Nhóm Alpha — Hợp đồng dữ liệu Snapshot và Event phiên bản 1.0

**Mục đích:** Thống nhất giao diện dữ liệu giữa mô phỏng, UI và kiểm thử; tài liệu này **không** thay thế nguồn cấu hình thông số game.

## 1. Quy ước chung

UI sử dụng `Session.snapshot()` và các sự kiện từ `Session.step()` — cùng lớp mô phỏng được dùng bởi `chonoi.headless` và `chonoi.live`. UI không được tự ý sửa trạng thái gameplay, tự tạo bộ sinh số ngẫu nhiên (RNG) cho logic game hoặc tính lại tiền/điểm. Mọi tham số số học phải lấy từ `game.contract.json`.

| Loại bản ghi | Các trường bắt buộc và ý nghĩa |
|---|---|
| `snapshot` | `type`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score` |
| `event` | `type: "event"`, `tick`, `phase`, `name`, `data` |
| `end` | `type: "end"`, `ticks`, `sim_tick`, `mode`, `state`, `reason`, `money`, `earned`, `reputation`, `score` |

## 2. Snapshot Gather — từ `GatherSim.snapshot()`

- `player`: thông tin nhân vật, gồm:
  - `pos`: tọa độ `[x, z]`, với `z` hướng về phía bắc.
  - `vel`: vận tốc di chuyển hiện tại `[vx, vz]`.
  - `oxygen_ticks`, `oxygen_max_ticks`: oxy hiện tại và dung lượng tối đa tính theo tick.
  - `hp`, `hp_max`: máu hiện tại và tối đa.
  - `zero_oxy_ticks`: thời gian hết oxy tính theo tick.
  - `catch_cd_ticks`: số tick hồi chiêu bắt cá.
  - `at_surface`: nhân vật có đang ở mặt nước hay không.
- `hold`: danh sách mã nguyên liệu theo thứ tự nhặt; `hold_count`: số vật phẩm; `hold_capacity`: sức chứa tối đa.
- `nodes`: danh sách nút nguyên liệu **được sắp xếp ổn định**, mỗi nút gồm `{id, pos, kind, ready, regrow_ticks}`.
- `fish`: danh sách cá **được sắp xếp ổn định**, mỗi cá gồm `{id, pos, kind, heading_deg}`.
- Sự kiện `gather_end` có `data.reason` (lý do kết thúc) và `data.inventory.items` (số lượng nguyên liệu chuyển giao).

## 3. Snapshot Quan — từ `QuanSim.snapshot()`

- `player.pos`: tọa độ `[x, z]` trong mặt phẳng nhìn từ trên xuống.
- `stock`: ánh xạ mã nguyên liệu → số lượng hiện có; **không** đồng nhất với danh sách `hold` của Gather.
- `hand`: món ăn đang cầm hoặc `null`, theo quy tắc của mô phỏng.
- `stoves`: danh sách bếp có thứ tự, với các trường `id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`.
- `tables`: danh sách bàn có thứ tự, gồm `id`, `pos`, `customer_id`.
- `customers`: danh sách khách đang ngồi tại quán, sắp theo ID.
  Mỗi khách có các trường theo Test Contract v1.0:
  - `id`: mã khách.
  - `table_id`: mã bàn.
  - `dish_id`: mã món đã gọi.
  - `order_tick`: thời điểm gọi món.
  - `state`: trạng thái khách, ví dụ `waiting` hoặc `eating`.
  - `patience_ticks_left`: số tick kiên nhẫn còn lại.
  - `eat_ticks_left`: số tick ăn còn lại.
  - `order_status`: trạng thái đơn hàng.
  - `reserved`: nguyên liệu đã giữ chỗ.
  - `base_price`: giá món ăn.
  - `tip`: tiền boa.
- Sự kiện `quan_end` có các trường `reason`, `money`, `earned`, `shift_earned`, `reputation`.

## 4. Danh sách sự kiện

### Gather

- `gather`: hái nguyên liệu thành công.
- `node_regrown`: nguyên liệu mọc lại.
- `hold_full`: giỏ không còn đủ sức chứa.
- `fish_caught`: bắt cá thành công.
- `dive`: bắt đầu lặn.
- `surface`: nổi lên mặt nước.
- `oxygen_empty`: oxy vừa giảm về 0.
- `choke`: mất máu do ngạt.
- `faint`: nhân vật ngất.
- `gather_end`: kết thúc buổi sáng.

### Quan

- `customer_arrived`: khách đến quán.
- `no_dish`: không có món phù hợp với nguyên liệu.
- `cook_started`: bắt đầu nấu.
- `dish_ready`: món đã nấu xong.
- `dish_picked`: người chơi nhặt món.
- `served`: phục vụ khách thành công.
- `paid`: khách thanh toán.
- `customer_left`: khách rời quán.
- `quan_end`: kết thúc ca bán hàng.

Các trường `data` và thứ tự phát sự kiện phải tuân theo
mục E và F của Test Contract v1.0.

## 5. Quy tắc thay đổi và phối hợp

- Người phụ trách Gather/Quan phải thông báo cho UI trước khi thêm trường hoặc đổi luồng chuyển trạng thái.
- Không đổi tên hay xóa trường bắt buộc của phiên bản 1.0 nếu chưa được nhóm phê duyệt.
- UI nên xử lý mềm dẻo với **trường tùy chọn** bị thiếu; lỗi thiếu **trường bắt buộc** phải được kiểm thử phát hiện, không âm thầm dùng giá trị mặc định để che lỗi.
- Cuối mỗi phase, QA trích xuất ví dụ JSONL từ **chương trình chạy thật**. Không sử dụng ví dụ trong tài liệu rồi ghi nhận như bằng chứng thực thi.

**Lưu ý về kho quán:**
`stock` là lượng nguyên liệu vật lý, bao gồm cả nguyên liệu
đã được giữ chỗ cho đơn hàng.

Nguyên liệu khả dụng = tồn vật lý - tổng lượng đã giữ chỗ.

UI không được coi toàn bộ `stock` là nguyên liệu có thể
dùng cho đơn mới.


