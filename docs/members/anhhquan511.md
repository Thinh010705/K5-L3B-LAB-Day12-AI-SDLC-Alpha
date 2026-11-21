# anhhquan511 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm commit):**
  - `0cb13ce`: Xây dựng toàn bộ giao diện 2D phong cách miền Tây Nam Bộ cho cả 2 buổi (`gather` bình minh sông Chín Khúc, Út Sen áo bà ba khăn rằn kính lặn giỏ lưới; `quan` nhà bè đèn dây vàng, khói bếp, bàn khách, mâm món), HUD đầy đủ PRD-0 (tự tính **Kho khả dụng**, vạch 50% tiền boa, bảng thực đơn), thoại Nam Bộ và âm thanh Web Audio API trong `chonoi/web/index.html`.
  - `806a85b`: Cập nhật `CREDITS.md` và bổ sung hợp đồng giao diện `sim/* ↔ client/ui` vào `docs/contracts/README.md`.
  - Đồng bộ UI với `sim/gather` và `sim/quan` sau khi merge `origin/main` (hỗ trợ cả schema PRD-0 lẫn key thực tế `dish`/`price`/`impatient`/`dish_burnt`).
- **Tôi đã review:** Đối chiếu `chonoi/sim/gather.py`, `chonoi/sim/quan.py` và `docs/contracts/UI_SNAPSHOT_V1.md` để đảm bảo UI đọc đúng snapshot và không đụng luật headless.
- **AI sai ở đâu và tôi phát hiện thế nào:** Ở bản vẽ khói bếp đầu tiên cho cảnh `quan`, hướng trục `z` bị đảo dấu (`-Math.PI/2` khiến khói bay xuống thay vì bay lên) và khi đối chiếu với `sim/quan.py` của nhóm mới phát hiện một số event dùng khóa `dish`/`price` khác với PRD-0 (`dish_id`/`amount`). Đã rà code và sửa tương thích cả hai dạng.
- **Điều tôi học được:** Chốt sớm hợp đồng dữ liệu (`UI_SNAPSHOT_V1.md`) và rà soát lại payload thật ngay sau khi merge giúp tích hợp UI ↔ Sim mượt mà không vỡ giao diện.
