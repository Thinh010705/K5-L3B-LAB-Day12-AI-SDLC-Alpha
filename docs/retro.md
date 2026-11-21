# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt:** Tích hợp thành công chu kỳ ngày đêm liên tục (`--mode day`), cửa hàng nâng cấp trang bị và 3 món ăn mới; cơ chế đàn cá bơi và quái vật Cá Sấu tuần tra hoạt động mượt mà.
- **Điều tệ:** Việc tích hợp giữa các nhánh bị chậm do xung đột giữa số lượng cá mặc định của P1 (6 đàn) và P2 (8 đàn), dẫn đến một số test P1 báo đỏ khi nâng cấp contract lên v1.1.
- **1 hành động cho Phase 3:** Viết Architecture Decision Record (ADR) và khóa manifest v1.1 cũ để bộ test hồi quy không bị vỡ khi chuyển đổi mô hình kho sang cá thể ở v1.2.

## Phase 3 (tạm thời trước tag)
- Đổi kho đếm sang cá thể chạm Gather, Quán, Day, CLI, HUD và test cũ; ADR trước khi bật manifest giúp giữ ranh giới rõ.
- Lần đầu bật v1.2 có 29 test lỗi do fixture/kỳ vọng cũ. Giữ test cơ chế lịch sử trên manifest P2, sửa test CLI theo schema mới và ghi lý do trong CHANGELOG.
- Hành động tiếp: QA/UI kiểm HUD trên trình duyệt và rà các ca biên trước khi Integrator gắn tag trên `main`.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2 (đã làm chưa? vì sao?):** Đã làm triệt để trong Phase 3 và Phase 4. Nhóm đã thực hiện viết ADR-0001 phân tích tác động kho cá thể và độ tươi trước khi đổi manifest; đồng thời duy trì fixture riêng cho các test cơ chế v1.0/v1.1, giúp toàn bộ 176 test hồi quy pass 100%.
- **Điều tốt / điều tệ:**
  - *Điều tốt:* Toàn bộ 4 phase hoàn thành đúng tiến độ; 176/176 tests pass; soak test 10 ngày hoàn thành xuất sắc 0 crash; benchmark có render đạt 69 FPS; cơ chế phân vai và người dự phòng hoạt động hiệu quả khi trưởng nhóm bận.
  - *Điều tệ:* Thời gian đầu tốn công sức xử lý sự khác biệt môi trường giữa Windows và Linux (lỗi stub `WindowsApps\python3.exe`).
- **Số liệu:**
  - *Số commit theo người:* Nguyễn Năng Thịnh (37), Cao Minh Quang (19), Trần Trọng Đạt (9), Nguyễn Anh Quân (6), Hoàng Minh Quyền (5). 100% thành viên đạt $\ge 3$ commit nội dung.
  - *Cách đọc code của nhau:* Review chéo qua Pull Request trên GitHub và pair programming; QA Lead chạy full test suite trước mỗi lần merge; Integrator và Scrum Lead rà soát contract invariants trước khi tạo tag.
  - *Token tiêu thụ AI theo người:* Thịnh ~350k, Quang ~320k, Đạt ~180k, Quân ~150k, Quyền ~160k (tổng dự án ~1.16M tokens qua Claude/Gemini/Antigravity).
- **Một lần AI sai và cách nhóm phát hiện:**
  - Trong Phase 4, khi triển khai soak test 10 ngày, AI trực tiếp truyền `day=6..10` vào `GatherSim`, làm kích hoạt exception do `GatherSim` ràng buộc nghiêm ngặt `1 <= day <= 5`. Nhóm phát hiện khi chạy soak test bị crash ở ngày 6 và đã sửa ngay logic tính `gather_day = ((day - 1) % 5) + 1` trong `DaySession`.
- **Nếu làm lại, đổi gì:**
  - Thiết lập virtualenv và alias lệnh Python chuẩn ngay trong 15 phút kickoff để tránh mất thời gian xử lý sự khác biệt đường dẫn trên Windows.
  - Xây dựng lớp Adapter cho Test Contract từ sớm thay vì phân nhánh `if/else` theo version chuỗi trong từng hàm.
