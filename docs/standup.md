# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Nguyễn Anh Quân (@anhhquan511) | Hoàn thiện đồ họa miền Tây 2D (`gather`/`quan`), HUD PRD-0 (gồm Kho khả dụng), âm thanh Web Audio, `CREDITS.md`, hợp đồng UI | Đồng bộ payload sự kiện thực tế với `sim/quan`, chơi thử 2 buổi liền mạch và gửi PR vào `main` | Không (một số event ở `sim/quan` dùng khóa `dish`/`price`, đã xử lý tương thích hai chiều ở UI) |
| Phase 2 | Nguyễn Anh Quân (@anhhquan511) | Nâng cấp đồ họa Mức 2 kiểu *Dave the Diver* (4 tranh nền vẽ tay, camera phóng to bám nhân vật, 4 ghe chợ nổi tương tác NPC, cá sống động, rêu đáy sông, animation bắt cá/hái hoa), nối `--mode day` vào `chonoi/live.py`, chuẩn bị kịch bản Demo (`docs/DEMO.md`) | Kiểm thử trọn vòng 2–5 ngày trên trình duyệt & sẵn sàng Demo | Chờ Integrator nâng `game.contract.json` gốc lên v1.1 (`live.py` đã tự fallback sang `game.contract.v1_1.proposed.json` để Demo chạy ngay) |
