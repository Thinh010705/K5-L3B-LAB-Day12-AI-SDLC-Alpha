# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-11-21 — Phase 4: Release v1.0.0 & Soak/Benchmark (Test Contract v1.3)

### Added
- **Test Contract v1.3 Support:** Cập nhật `game.contract.json` với `contract_version: "1.3"`, bổ sung các khóa thực thi công cụ bắt buộc `"bench_cmd": "python3 -m chonoi.bench"` và `"soak_cmd": "python3 -m chonoi.soak"`.
- **Hỗ trợ chu kỳ 10 ngày (`chonoi/day.py`):** Cho phép vòng lặp ngày chơi vô hạn, tự động xoay vòng danh sách công thức thực đơn D1–D5 cho các ngày tiếp theo (`day_plan[(day - 1) % len(day_plan)]`) và gán đúng ngày lặn `gather_day = ((day - 1) % 5) + 1`.
- **Soak Runner (`chonoi/soak.py`):** Triển khai lệnh chạy kiểm thử độ bền headless nhiều ngày, tích hợp bot tự động thông minh; vượt qua bài test 10 ngày với 0 crash (`days_completed: 10`, `crashes: 0`).
- **Benchmark Tool (`chonoi/bench.py`):** Triển khai lệnh đo đạc hiệu năng mô phỏng render khung hình Canvas 2D độ phân giải 1280x720 (bơi lặn Út Sen, đàn cá bơi hình sin, Cá Sấu Năm Chèo tuần tra); kết quả thực nghiệm đạt 69 FPS trung bình (vượt chuẩn $\ge 60$), 1% low 31 FPS (vượt chuẩn $\ge 30$), thời gian nạp cảnh 2ms (vượt chuẩn $\le 10000$ms).
- **Kiểm thử Contract v1.3 (`tests/test_contract_v11.py`):** Bổ sung các ca kiểm thử nạp manifest v1.3 và từ chối nếu thiếu `bench_cmd` hoặc `soak_cmd`. Toàn bộ 176 test hồi quy toàn hệ thống pass 100%.

## [0.3.0] - 2026-11-21 — Phase 3: Mùa Nước Nổi & Kho Cá Thể (Test Contract v1.2)

### Added
- **Kho cá thể:** Chuyển đổi định dạng kho sang mảng cá thể `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}` với ID tăng duy nhất xuyên suốt các pha và các ngày.
- **Hệ thống độ tươi & ươn hỏng:** Cơ chế phân rã độ tươi theo thời gian thực (Gather giảm 0.5 điểm/s, Quán giảm 0.25 điểm/s); khi độ tươi $< 30$, hệ thống kích hoạt sự kiện `spoiled` một lần duy nhất và loại bỏ khỏi chuỗi nấu.
- **Định giá theo độ tươi:** Món ăn được chốt giá `base_price = floor(price * avg_fresh / 100)` tại thời điểm bắt đầu nấu; tiền boa tính dựa trên giá sau điều chỉnh.
- **Mở rộng Dòng Lũ:** Lịch dòng lũ tác động lực đẩy lên nhân vật Út Sen theo chu kỳ.

## [0.2.0] - 2026-11-21 — Phase 2: Chợ Sáng Quán Đêm & Cá Sấu Năm Chèo (Test Contract v1.1)

### Added
- **Chu kỳ ngày đêm liên tục (`--mode day`):** Chuyển giao tự động giữa ca sáng Lặn & Hái và ca tối Quán Ăn Chợ Nổi; tích hợp cửa hàng nâng cấp thể lực, oxy và mở rộng sức chứa giỏ.
- **Cá bơi tự do & Cá Sấu Năm Chèo:** 8 đàn cá bơi lội ngẫu nhiên có vây chuyển động; quái vật Cá Sấu tuần tra vùng nước sâu theo lộ trình và rượt đuổi người chơi khi áp sát.
- **Thực đơn mở rộng 6 món:** Bổ sung canh chua cá lóc, cá kèo nướng muối ớt và lẩu mắm đậm đà phong vị sông nước miền Tây.

## [0.1.0] - 2026-11-21 — Phase 1: Khởi Khởi Sông Chín Khúc & Quán Ăn Chợ Nổi (Test Contract v1.0)

### Added
- **Ca sáng Lặn & Hái (`--mode gather`):** Cơ chế vật lý bơi gia tốc/giảm tốc, giới hạn biên lòng sông, quản lý thanh dưỡng khí oxy, hái bông súng/điên điển và bắt cá linh/cá lóc/cá kèo.
- **Ca tối Quán Ăn Chợ Nổi (`--mode quan`):** Quản lý nhà bè nổi của Má Tư; tiếp nhận thực khách, nấu bếp củi, phục vụ món ăn theo đơn và tính điểm uy tín/doanh thu.
