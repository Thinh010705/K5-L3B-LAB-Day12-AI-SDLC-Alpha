# Credits

## Tài sản đồ họa & âm thanh (Module `client/ui`)
- **Tranh nền & Key Art phong cách miền Tây Nam Bộ (Mức 2)** (`chonoi/web/assets/`):
  - `gather_dawn.jpg` (cảnh bình minh sông Chín Khúc, bờ dừa nước, nhà sàn, ghe cây bẹo),
  - `gather_underwater.jpg` (hẻm sông 2.5D dưới nước kiểu *Dave the Diver*: rễ đước/bần, ghe đắm, lờ bắt cá, tia nắng & sương mù độ sâu),
  - `quan_raft.jpg` (sàn gỗ nhà bè Quán Má Tư góc nhìn từ trên xuống),
  - `menu_cover.jpg` (tranh bìa Út Sen & Quán Ăn Chợ Nổi lúc hoàng hôn).
  - *Nguồn & Giấy phép*: 100% ảnh gốc do nhóm Alpha tự tạo bằng công cụ tạo ảnh AI trong bài lab (không sao chép tài sản bản quyền bên ngoài).
- **Sprite nhân vật, thủy quái, 6 nguyên liệu & 6 món ăn** (`chonoi/web/index.html`): 100% tự vẽ bằng HTML5 Canvas 2D có nét mực, đổ bóng, ánh sáng động và hoạt ảnh mượt.
- **Nhạc nền ngũ cung Nam Bộ & Hiệu ứng âm thanh** (`chonoi/web/index.html`): 100% tự tổng hợp bằng Web Audio API trong trình duyệt, lưu âm lượng Master/Music/SFX trong `localStorage` (tắt hoàn toàn ở headless).

## Khung kỹ thuật
- Khung starter `chonoi/` và `tests/`: do giảng viên môn AI SDLC cung cấp.
- Mở rộng nhỏ trên `chonoi/live.py` (đã ghi lý do trong `docs/contracts/README.md`): phục vụ file ảnh tĩnh trong `chonoi/web/assets/`, thêm `POST /pause` và trả thêm `menu`, `shop_config`, `paused` trong `/state` cho UI Phase 2 (không ảnh hưởng `headless` hay `test_live.py`).

## Công cụ AI đã sử dụng
- **Antigravity (Google Deepmind)**: Hỗ trợ phân tích PRD-0 & TICKET-02 (Phase 1–2), tạo 3 tranh nền miền Tây Nam Bộ gốc, thiết kế camera phóng to bám nhân vật + parallax + minimap, nâng cấp HUD chuẩn v1.1 (Menu, Intro, Shop, Pause, Settings âm thanh, 6 nguyên liệu, 6 món, Thủy quái).
