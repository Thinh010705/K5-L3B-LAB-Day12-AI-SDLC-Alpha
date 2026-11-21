# Nhóm Alpha — Hợp đồng tích hợp v1.1 (Phase 2)

**Người điều phối:** Integrator (`@Thinh010705`)  
**Trạng thái:** Bản đề xuất để các thành viên Gather, Quan, UI và QA xác nhận.  
**Nguồn chuẩn:** TICKET-02 — *Một ngày ở chợ nổi*, Test Contract v1.1. Khi có khác biệt, ưu tiên TICKET-02.  
**Kế thừa:** `INTEGRATION_V1.md` và các luật v1.0 không bị TICKET-02 thay thế.

## 1. Phạm vi thay đổi

| Giao diện | v1.0 | v1.1 | Chủ sở hữu |
|---|---|---|---|
| CLI | `gather`, `quan` | Thêm `day`, `--days` (chỉ mode `day`, 1–5, mặc định 1) | Integrator + chủ `runner/headless` |
| Hợp đồng kho | `{"items":{...}}` | Giữ nguyên schema, bổ sung `ca_keo`, `keo_neo` | Gather + Quan + Integrator |
| Gather | 4 loại nguyên liệu, 6 đàn tĩnh | 6 loại, cá bơi/sinh, tối đa 12 đàn, Cá Sấu Năm Chèo | Gather |
| Quan | 3 món, B1, T1 | 6 món, B1–B2, T1–T4 | Quan |
| Vòng ngày | Hai mode độc lập | `day`: Gather → Quan → Shop, lặp tới tối đa 5 ngày | Chủ chế độ `day` + Integrator |
| UI | Snapshot/event v1.0 | Thêm HUD kế hoạch, ngày, Shop, quái, pause, nâng cấp | UI |
| Kiểm thử | V1.0 | Thêm v1.1 và hồi quy Phase 1 với số liệu mới | QA + Integrator |

## 2. Manifest và CLI bắt buộc

- `game.contract.json` phải có `contract_version: "1.1"`, `team: "Alpha"`, `team_size: 5`, và số liệu chuẩn TICKET-02. Không đổi `contract_version` trước khi code và kiểm thử cập nhật tương ứng.
- Khai đầy đủ 6 nguyên liệu `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`, `ca_keo`, `keo_neo` thông qua cấu hình thích hợp; 6 món và đúng công thức/giá/thời gian nấu của TICKET-02.
- Chế độ `day` nhận `--days N` (1–5, mặc định 1). `--days` trong mode độc lập là sai cờ; các cờ `--inventory` chỉ dành cho `quan`, `--inventory-out` chỉ dành cho `gather`.
- Tham số bắt buộc gồm `--mode`, `--seed`, `--ticks`, `--out`; cờ dữ liệu sai trả mã 2 và phải được kiểm tra trước khi tạo file output. Lỗi thực thi/ghi file trả mã 1; chạy hợp lệ trả mã 0.
- Trong mode `day`, bàn giao kho **nội bộ**, không dùng file kho trung gian làm yêu cầu bắt buộc. Mode `gather` và `quan` độc lập vẫn phải hỗ trợ chuyển kho qua file đúng v1.0.

## 3. Hợp đồng kho Gather → Quan

Định dạng giữ nguyên, chỉ có một khóa cấp cao nhất:

```json
{"items":{"bong_sung":2,"ca_loc":1,"ca_keo":2,"keo_neo":1}}
```

- `items` là map mã nguyên liệu → số nguyên không âm; thiếu mã xem là 0, bỏ mục có số lượng 0 khi ghi; từ chối khóa lạ, mã lạ, boolean, số thực, số âm.
- Khi Gather kết thúc bằng `docked` hoặc `time`, giữ toàn bộ phần còn trong giỏ. Khi `fainted`, giỏ mất và kho bàn giao rỗng (`{"items":{}}`). Khi chỉ chạm `tick_limit` mà chưa kết thúc Gather thì không ghi hoặc ghi đè file kho.
- Sự kiện `gather_end.data.inventory` phải khớp dữ liệu kho. Mode `day` dùng cùng schema để dựng kho đầu ca Quan, kể cả khi Gather kết thúc vì ngất.
- Trong Quan, `stock` là **tồn vật lý gồm cả phần giữ chỗ**; tồn khả dụng = tồn vật lý − tổng lượng giữ chỗ. Không giữ chỗ trùng cho hai đơn.
- Trong mode `day`, `scenario.quan.stock` và `scenario.quan.reputation` bị cấm; kho của Quan lấy từ Gather, uy tín từ trạng thái xuyên ngày. Trong mode `quan` độc lập, `--inventory` xung đột `scenario.quan.stock` vẫn phải trả mã 2.
- Hàng còn dư sau Shop **không chuyển sang Gather của ngày kế tiếp** (ngoại trừ cơ chế vendor nếu nhóm bật mở rộng và đã khai `extensions`).

## 4. Hợp đồng vòng ngày

Trong giao diện chơi: `DayIntro → gather → EveningIntro → quan → DayResult → Shop → DayIntro` (hoặc Summary sau Ngày 5).  
Trong **headless**, các pha gameplay là `gather`, `quan`, `shop`; màn giới thiệu/kết quả là màn UI, không tự bổ sung tick gameplay hoặc thay đổi event theo hợp đồng.

Trình tự event chuyển pha tại cùng một tick:

1. Ngày mới: `day_start` → `day_plan` → `phase_start` (gather).
2. Kết thúc Gather: `gather_end` → dựng Quan với kho nhận được → `phase_start` (quan), kể cả khi ngất.
3. Kết thúc Quan: `quan_end` → dựng Shop → `phase_start` (shop).
4. Shop đóng: `shop_end`, tăng `days_completed`; kết thúc nếu đã đủ `--days`, nếu chưa thì dựng ngày kế tại tick đó.

Pha mới chỉ xử lý gameplay từ **bước tiếp theo**. Snapshot lúc chuyển pha thuộc pha **mới** với `phase_tick: 0`. Event kết thúc mang tên pha **cũ**.

Trạng thái xuyên ngày giữ `money`, `earned`, `reputation`, `upgrades` (cấp đã mua); `active_upgrades` là cấp đang có hiệu lực. Oxy và HP hồi đầy lúc bắt đầu Ngày theo **cấp hiệu lực**; cấp vừa mua ở Shop chỉ áp dụng khi bắt đầu Ngày tiếp theo.

## 5. Đầu vào mới: pause và Shop

- `pause` là nút boolean ở cả ba mode, tác động ở **cạnh lên**. Khi paused, `tick` ngoài vẫn tiến nhưng `sim_tick`, `phase_tick` và các timer gameplay không tiến; bỏ qua hành động và `buy`. Cạnh lên tiếp theo phát `resumed` và chạy gameplay ở chính bước đó.
- `shop_done` là nút boolean chỉ có tác dụng trong Shop và ở cạnh lên.
- `buy` là chuỗi không rỗng, xử lý **chỉ tại frame khai báo**, không phải trạng thái giữ. Lõi hỗ trợ `oxygen`, `hp`; lệnh mua không được hỗ trợ trong Shop phát `buy_failed` theo Test Contract.
- Trong cùng một bước Shop: xử lý `buy` trước `shop_done`, kể cả ở bước cuối. Shop tự đóng sau tối đa 600 tick hoạt động nếu chưa được đóng bằng nút.
- Nâng cấp `oxygen`: cấp 1 giá 200 → oxy 45 s; cấp 2 giá 400 → oxy 60 s. Nâng cấp `hp`: cấp 1 giá 250 → 4 Máu; cấp 2 giá 500 → 5 Máu. Tiền giảm đúng giá mua; `earned` không giảm. Đủ đúng tiền vẫn mua được.
- Mua không đủ tiền hoặc đạt tối đa phát `buy_failed` và **không làm đổi tiền/cấp**.

## 6. Các điều kiện kiểm thử tích hợp tối thiểu

1. Mode độc lập Gather → file kho → Quan vẫn hoạt động với **6 mã nguyên liệu** sau nâng cấp.
2. Mode `day --days 1` chuyển Gather → Quan → Shop; `days_completed` chỉ tăng khi Shop đóng; dòng `end` có `reason: "days_complete"` khi đã đủ ngày.
3. Gather ngất → vẫn chuyển sang Quan nhưng kho rỗng.
4. `buy oxygen`/`buy hp` thành công và thất bại đúng quy tắc; cấp mới **không** ảnh hưởng Gather của ngày vừa kết thúc, chỉ có hiệu lực ở ngày tiếp theo.
5. Pause không làm tiến `sim_tick`, `phase_tick`, các timer gameplay và không thực hiện mua hàng trong trạng thái pause.
6. Vẫn giữ tính tất định byte-for-byte với cùng seed/inputs/manifest trên cùng bản chạy; input sai trả mã 2 trước khi ghi output.
7. Hồi quy Phase 1 sau khi cập nhật số chuẩn; thay đổi kỳ vọng test cũ phải có lý do vì TICKET-02 thay luật mặc định (ví dụ: đàn cá 6 tĩnh → 8 bơi/sinh).

## 7. Quy trình bàn giao

- Chủ module xác nhận schema và phạm vi công việc trước khi merge; không đổi event/field đã chốt mà không báo QA/UI.
- QA + Integrator chạy smoke hai tiến trình ở mốc giữa phase, lưu `docs/proof/phase-2/integration.*`; sau đó chạy `day --days 1`, nhiều ngày và hồi quy trên commit bàn giao.
- Ghi ma trận AC → bằng chứng → kết quả trong `docs/verification/phase-2.md`; nêu rõ phần nào chưa đạt, kèm commit thực tế. Chỉ gắn tag `phase-2` trên `main` ở trạng thái đã ghi nhận, không di chuyển tag để sửa lịch sử.
