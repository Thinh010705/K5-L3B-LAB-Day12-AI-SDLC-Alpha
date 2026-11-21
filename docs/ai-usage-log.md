# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Cao Minh Quang (@quang011105) | Antigravity (Gemini 3.8 Flash) | Triển khai module sim/quan (bếp nấu, khách hàng, phục vụ, doanh thu) | ~40k tokens | AI đề xuất tên nhánh ban đầu chưa bám sát TEAM.md, cần điều chỉnh lại |
| Phase 2 | Cao Minh Quang (@quang011105) | Antigravity (Gemini 3.8 Flash) | Nâng cấp sim/quan: order_tick, đóng ca, day_plan, cháy món (dish_burnt) | ~35k tokens | Logic tính kho khả dụng khi cháy món bị trừ trùng reserved cũ, đã phát hiện qua test và sửa |
| Phase 3 | Cao Minh Quang (@quang011105) | Antigravity (Gemini 3.8 Flash) | Triển khai kho cá thể, hao tươi, spoiled theo ID, tái cấp giữ chỗ và chốt base_price theo độ tươi | ~35k tokens | AI cần được hướng dẫn định hướng thứ tự tick chính xác theo Ticket-03 |
| Phase 3 | Nguyễn Năng Thịnh (@Thinh010705) | Codex | Adapter file kho, tích hợp PR Gather/Quán, bật v1.2, sửa HUD, smoke Day và mở rộng dòng lũ | Chưa đo | Lần đầu bật v1.2 có 29 lỗi do fixture/kỳ vọng kho đếm P1/P2; giữ regression cơ chế trên manifest P2 và chuyển test CLI sang v1.2. Công cụ trình duyệt không mở được localhost. |
| Phase 4 | Cao Minh Quang (@quang011105) | Antigravity (Gemini 3.8 Flash) | Rà soát độ ổn định sim/quan cho soak test 10 ngày, chuẩn hóa trường cảnh báo khách giận và hoàn thiện phản tư cá nhân | ~20k tokens | Người dùng định hướng AI tập trung phạm vi cá nhân, tránh làm chéo việc chung của nhóm |
