# EddyTryToCode — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm commit):**
  - Phase 1: Xây dựng test unit và integration Gather P1 (`b71c931`), sửa docstring fixture (`0d98f6f`), lập ma trận truy vết và hướng dẫn test (`a9ae9b1`).
  - Phase 2: Triển khai 43 unit tests và 8 integration tests Gather P2 (`c2c75be`), kiểm thử cá bơi, Cá Sấu tuần tra/va chạm, bất tử và nâng cấp.
  - Phase 3 & 4: Rà soát kiểm thử hồi quy v1.2/v1.3, xác minh tính tất định headless runner và bộ 176 tests.
- **Tôi đã review:** Review module `sim/gather` (Đạt), `sim/quan` (Quang) và `chonoi/contract.py` (Thịnh).
- **AI sai & phát hiện:** AI sinh tọa độ Cá Sấu ngoài biên `depths` gây lỗi BadInput; tôi phát hiện qua log test và sửa waypoint hợp lệ.
- **Bài học:** Viết test hộp đen theo đúng Test Contract giúp phát hiện lỗi vỡ giao diện sớm.
