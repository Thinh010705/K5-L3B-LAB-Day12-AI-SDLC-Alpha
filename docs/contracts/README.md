# Hợp đồng tích hợp (nên chốt sớm; hình thức do nhóm chọn)

Điền trong 15 phút kickoff (hoặc thay bằng một mục trong README / một bảng trên giấy, miễn cả nhóm cùng thống nhất):
1. **Schema file kho** — khớp mục G của PRD-0 (kho ghi khi `gather_end`) + một file kho mẫu hợp lệ: `inventory.sample.json`.
2. **Giao diện giữa `sim/*` và `client/ui`** — trạng thái nào UI được đọc, lệnh nào UI gửi vào:
   - **Kênh giao tiếp (`chonoi.live` — đã mở rộng nhẹ cho Phase 2)**:
     - `GET /state` → trả snapshot JSON đúng schema mục E của PRD-0 / mục 4.4 của TICKET-02, kèm `meta` (`tuning[phase]`), `menu`, `shop_config`, `events`, `finished`, `paused`, `reason`, `error`.
     - `GET /assets/<file>` → phục vụ ảnh nền tĩnh trong `chonoi/web/assets/` (`gather_dawn.jpg`, `quan_raft.jpg`, `menu_cover.jpg`), chặn path traversal.
     - `POST /input` → gửi `{"move": [dx, dy], "interact": bool, "catch": bool, ...}` (hỗ trợ mở rộng Phase 2: `pause`, `shop_done`, `attack`, `photo`, `buy`).
     - `POST /pause` → tạm dừng / tiếp tục vòng tick trên cửa sổ chơi trực tiếp (`{"paused": bool}`) cho Menu chính, DayIntro và Pause (Esc/P).
     - `POST /restart` → khởi động lại lượt chơi với cùng `seed` và `scenario`.
   - **Trường UI đọc từ snapshot**:
     - Chung: `tick`, `mode`, `time_left_ticks`, `money`, `earned`, `reputation`, `score`, `events[]`, `finished`, `reason`, `meta`.
     - `gather`: `player.{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, invuln_ticks, catch_cd_ticks, at_surface}`, `hold[]`, `hold_capacity`, `nodes[]{id, kind, pos, ready, regrow_ticks}`, `fish[]{id, kind, pos, heading_deg}`.
     - `quan`: `player.{pos}`, `stock` (tồn vật lý), `hand` (`{order_id, dish_id, base_price}` hoặc `null`), `stoves[]{id, pos, state, dish, cook_ticks_left, ready_ticks}`, `tables[]{id, pos, customer_id}`, `customers[]{id, table_id, dish_id, state, order_status, patience_ticks_left, eat_ticks_left, reserved}`.
   - **Quy tắc an toàn**: UI chỉ đọc snapshot (tự bỏ qua trường chưa có), tự tính **Kho khả dụng** = `stock - sum(customer.reserved)`, không ghi đè luật chơi hay ảnh hưởng chế độ headless.
3. **Danh sách sự kiện** — tên, `data`, ai phát, ai nghe (gather: `gather`, `node_regrown`, `hold_full`, `fish_caught`, `gather_end`...; quan: theo mục E của PRD-0).

Khi đổi hợp đồng sau này: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú, tùy chọn).
