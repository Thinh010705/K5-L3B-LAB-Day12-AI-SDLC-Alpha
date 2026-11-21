# anhhquan511 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - **Phase 1**: Giao diện 2D miền Tây, HUD PRD-0 (Kho khả dụng, mốc boa 50%, xử lý `stove.dish`), Web Audio, `CREDITS.md` (`0cb13ce`, `806a85b`).
  - **Phase 2 & Demo**: 4 tranh nền vẽ tay miền Tây (bình minh, đáy sông 2.5D kiểu *Dave the Diver*, nhà bè, ảnh bìa); camera phóng to + parallax + minimap; 4 ghe chợ nổi NPC; hoạt ảnh bắt cá/hái hoa và **POV toàn màn hình** (bật bếp → xào nấu → phục vụ); HUD v1.1 (Menu, Intro, Shop, Pause, Settings); nối `--mode day`, `--cook-scale` ở `chonoi/live.py` và kịch bản Demo (`docs/DEMO.md`, `docs/demo/demo_day.json`).
- **Đã review:** Đối chiếu `sim/gather.py`, `sim/quan.py`, `day.py`, `contract_v11.py` và `UI_SNAPSHOT_V1.md`.
- **AI sai & cách phát hiện:** Phát hiện khói bếp ngược trục `z`, nút Shop dựng lại mỗi 16ms gây hụt click, và lệch khóa event ở `sim/quan.py`; đã đọc code trực tiếp và sửa dứt điểm.
- **Bài học:** Tách sạch hiển thị khỏi lõi mô phỏng giúp sáng tạo thoải mái mà vẫn giữ 100% tính tất định headless.
