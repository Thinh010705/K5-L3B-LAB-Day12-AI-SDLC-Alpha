# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Cao Minh Quang (@quang011105) | Antigravity (Gemini 3.8 Flash) | Triển khai module sim/quan (bếp nấu, khách hàng, phục vụ, doanh thu) | ~40k tokens | AI đề xuất tên nhánh ban đầu chưa bám sát TEAM.md, cần điều chỉnh lại |
| Phase 2 | Cao Minh Quang (@quang011105) | Antigravity (Gemini 3.8 Flash) | Nâng cấp sim/quan: order_tick, đóng ca, day_plan, cháy món (dish_burnt) | ~35k tokens | Logic tính kho khả dụng khi cháy món bị trừ trùng reserved cũ, đã phát hiện qua test và sửa |
