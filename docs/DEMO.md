# Kịch bản Demo 3 phút — Quán Ăn Chợ Nổi (Nhóm Alpha)

> **Người phụ trách:** Nguyễn Anh Quân (`@anhhquan511`, UI/Demo Lead)  
> **Mục tiêu:** Trình diễn trọn vẹn vòng lặp **1 Ngày liên hoàn (`DayIntro → Lặn & Hái → Cập bến → Quán Nhà Bè → Shop nâng cấp → Ngày 2`)**, đồ họa phong cách *Dave the Diver × Miền Tây Nam Bộ*, và tính tất định ở chế độ `headless`.

---

## 1. Lệnh chạy Demo trực tiếp (1 lệnh duy nhất)

Chạy tại thư mục gốc repo trong Terminal VS Code:

```powershell
python -m chonoi.live --mode day --days 2 --seed 7 --cook-scale 1.4 --scenario docs/demo/demo_day.json
```

*(Hoặc chạy đủ 5 ngày chuẩn không scale thời gian nấu: `python -m chonoi.live --mode day --days 5 --seed 7`)*

Mở trình duyệt tại **`http://127.0.0.1:8000/`**.

---

## 2. Kịch bản trình bày theo mốc thời gian (3 phút)

### ⏱ 0:00 – 0:25 | Menu Chính, Pause & Cài đặt âm thanh
- Trình chiếu **Menu Chính** với tranh vẽ tay Key Art *Út Sen & Quán Ăn Chợ Nổi*.
- Nhấn **⚙ Cài đặt âm thanh** (giới thiệu 3 thanh trượt Master / Nhạc ngũ cung Nam Bộ / SFX tự tổng hợp Web Audio API, lưu `localStorage`, tắt hoàn toàn khi chạy headless).
- Bấm **▶ Chơi ngay** → hiện **DayIntro Ngày 1** (*Má Tư công bố thực đơn & danh sách nguyên liệu cần lấy*).

### ⏱ 0:25 – 1:25 | Buổi Sáng (`gather`) — Lặn Sông Chín Khúc kiểu *Dave the Diver*
- **Phía trên mặt nước**: Bơi ngang mặt nước để giảng viên thấy:
  - Bức nền bình minh parallax (dừa nước, nhà sàn, ghe cây bẹo).
  - **4 ghe chợ nổi sống động** (Chú Sáu bán hủ tiếu bốc khói, Cô Ba ghe trái cây cây bẹo, Anh Năm câu cá, Dì Bảy ghe rau) **tự tương tác, vẫy tay & đối đáp giọng Nam Bộ**.
  - Bấm **`E`** gần nút hái (Bông điên điển / Bông súng / Kèo nèo) để xem **animation hái hoa tung cánh bay vào giỏ**.
- **Bên dưới mặt nước**:
  - Lặn xuống để thấy **hẻm sông 2.5D** (rễ đước/bần, xuồng đắm, lờ tre, thảm rêu đá 3 tầng dưới đáy), **cung ngắm trắng** trước mặt Út Sen và **đồng hồ tròn O₂ phát sáng** góc dưới-trái.
  - Bấm **`Space`** bắt đàn cá linh / cá lóc để trình diễn **animation quét vợt lưới tre + cá bay vòng cung vào giỏ**.
  - Thử bấm **`Z`** để chuyển nhanh giữa **Camera bám nhân vật (Phóng to)** ↔ **Toàn cảnh** (chỉ **Cá Sấu Năm Chèo** ở tầng sâu `d ≥ 10m` và **Radar Minimap**).
- Bơi về **Bến Má Tư** (Má Tư vẫy tay gọi) → bấm **`E`** để **chốt giỏ & tự động chuyển sang Buổi Tối**.

### ⏱ 1:25 – 2:15 | Buổi Tối (`quan`) — Nhà Bè Đèn Dây Vàng (2 bếp, 4 bàn, 6 món)
- Hiện **EveningIntro** báo số nguyên liệu vừa mang từ sông về & món nấu được.
- Vào **Nhà bè Quán Má Tư** (sàn gỗ vẽ tay, 2 hàng dây đèn vàng, hoa đăng trôi trên sông đêm, Má Tư ngồi ghế tre quạt mo).
- Khi khách vào bàn (`T1`–`T4`):
  - Chỉ vào **bảng Kho khả dụng** (đã tự trừ phần khách giữ chỗ `reserved`) và **Thực đơn 6 món**.
  - Lại bếp `B1`/`B2` bấm **`E`** nấu món → trình diễn **Animation góc nhìn thứ nhất (POV)** nhìn thẳng xuống bếp lò đất than hồng với hai tay Út Sen cầm vá/đũa lật cá, khuấy lẩu & rắc bông điên điển!
  - Chín bấm **`E`** bưng mâm tre → lại bàn bấm **`E`** phục vụ trước vạch vàng **50% kiên nhẫn** → hiện **Animation góc nhìn thứ nhất (POV)** hai tay Út Sen đẩy mâm tre đặt món nóng hổi lên bàn trước mặt khách cười mắt sao ăn **tiền boa (tip) + sao uy tín**!
- Nhấn thử **`Esc`** mở **Pause làm mờ nền** (đồng hồ đứng yên), rồi bấm **Tiếp tục**.

### ⏱ 2:15 – 2:45 | Cửa Hàng Chợ Nổi (`Shop`) & Sang Ngày 2
- Hết 75 giây ca tối → tự bật **Cửa Hàng Chợ Nổi (`Shop`)**.
- Bấm **Mua Bình Oxy Cấp 1 (200k)** → tiền trừ ngay, hiện `Cấp hiện tại: 1 (áp dụng: 0)`.
- Bấm **✔ Hoàn tất & Sang Ngày mới** → chuyển thẳng sang **Ngày 2** với thực đơn mới và **Oxy tối đa đã tăng lên 45s**!

### ⏱ 2:45 – 3:00 | Chứng minh Headless & Test Tự Động (25đ cốt lõi)
- Quay lại Terminal, khẳng định mọi sáng tạo đồ họa/âm thanh chỉ chạy ở lớp hiển thị và chạy nhanh 1 lệnh test xác minh:
  ```powershell
  $env:PYTHONPATH="tests;."; python -m unittest test_day_core_p2 test_contract_v11 test_gather_p1_units test_python_starter_units -v
  ```
