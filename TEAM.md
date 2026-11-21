# TEAM

**Tên nhóm:** Alpha  **Số người:** 5  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn Năng Thịnh | @Thinh010705 | integration/contracts – Tích hợp Gather → Quan, quản lý contract, đồng bộ dữ liệu và kiểm tra toàn hệ thống | Integrator – Quản lý docs/contracts/, tích hợp các nhánh, kiểm tra và gắn tag từng phase | Thành viên 5 (QA) |
| Trần Trọng Đạt | @dtr-uep | sim/gather – Logic bơi/lặn, oxy, HP, thu thập nguyên liệu, bắt cá, giỏ và cập bến | PO – Phụ trách làm rõ yêu cầu, liên hệ giảng viên và cập nhật docs/clarify.md | Thành viên 3 (Quan) |
| Cao Minh Quang | @quang011105 | sim/quan – Khách hàng, gọi món, bếp, nấu ăn, phục vụ, doanh thu và uy tín | Scrum/Release – Theo dõi tiến độ, điều phối standup, tổng hợp trạng thái và chuẩn bị release | Thành viên 2 (Gather) |
| Nguyễn Anh Quân | @anhhquan511 | client/ui – Giao diện Gather/Quan, HUD, trạng thái nhân vật, tương tác và demo | UI/Demo Lead – Phụ trách trải nghiệm người dùng, kịch bản demo và CREDITS.md | Nguyễn Năng Thịnh (Integration) |
| Hoàng Minh Quyền | @EddyTryToCode | qa – Unit test, headless test, regression test, CI và kiểm chứng contract | QA Lead / AI Harness – Quản lý tests/, docs/verification/, AGENTS.md, kỹ năng AI và bằng chứng kiểm thử | Thành viên 4 (UI) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Nhóm chat Zalo
- Khi bất đồng về thiết kế: Thảo luận tối đa 2 phút, ưu tiên game.contract.json và yêu cầu PRD; nếu chưa thống nhất, Integrator quyết định và PO ghi lại lý do trong docs/clarify.md.
- Khi ai đó trễ hoặc vướng quá 10 phút: Thông báo ngay cho nhóm, nêu vấn đề và trạng thái code; người dự phòng hỗ trợ hoặc nhận bàn giao để tránh chậm tiến độ.
- Giờ standup giữa phase: Kickoff và tại các mốc chuyển Phase 1 → 2 → 3 → 4; mỗi lần tối đa 5 phút để cập nhật tiến độ, blocker và phân công yêu cầu mới.
- Cách đọc code của nhau (tùy chọn): Mỗi thành viên kiểm tra thay đổi ở module liên quan; QA chạy regression test và Integrator kiểm tra khả năng tương thích trước khi merge.
- Cách làm việc với Git: Mỗi người làm trên một nhánh feature/<module>, commit và push thường xuyên; Integrator phụ trách merge vào main và gắn tag phase-1 đến phase-4.
