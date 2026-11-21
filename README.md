# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:https://github.com/Thinh010705/K5-L3B-LAB-Day12-AI-SDLC-Alpha

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Phase 3 — kho cá thể và dòng lũ

Contract v1.2 dùng file kho `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Kho đếm v1.1 không đọc được ở v1.2; cần chuyển fixture sang cá thể có id duy nhất. Chạy smoke bàn giao và ngưỡng 30 bằng `PYTHONPATH=tests:. python3 -m unittest tests.test_integration_p3 -v`.

Nhóm 5 người chọn mở rộng **dòng lũ**: lịch ở `tuning.gather.current`, scenario có `random_current:false` để tắt và `current_direction:-1|1` để khóa hướng. Snapshot Gather có `current:null` hoặc `{direction,ticks_left}`. Test và bằng chứng: `PYTHONPATH=tests:. python3 -m unittest tests.test_current_p3 -v`, `docs/proof/phase-3/integration-v12.md`.
## Sáng tạo của nhóm

> Toàn bộ phần sáng tạo chỉ hoạt động ở chế độ trình duyệt (`chonoi/live.py`, `chonoi/web/`), **tắt hoàn toàn ở `chonoi.headless`** và không làm thay đổi tính tất định hay Test Contract.

- **Bối cảnh Miền Tây Nam Bộ vẽ tay (Mức 2) & phong cách *Dave the Diver***: 4 tranh nền & Key Art gốc (`chonoi/web/assets/`) gồm bình minh sông Chín Khúc, hẻm sông 2.5D dưới nước (rễ đước, ghe đắm, lờ bắt cá), sàn gỗ nhà bè Quán Má Tư và ảnh bìa Menu chính; kết hợp camera phóng to bám nhân vật (`Z`), hiệu ứng parallax, minimap radar và vòng nhắm bắt cá.
- **Thế giới Chợ Nổi sống động trên mặt nước**: 4 ghe thương hồ (Chú Sáu, Cô Ba, Anh Năm, Dì Bảy) và Má Tư trên bến trò chuyện qua lại bằng thoại Nam Bộ tự nhiên, tương tác theo giỏ cá của Út Sen; đàn cá uốn lượn đa khớp và tầng rêu đá/sò ốc 3 lớp dưới đáy sông.
- **Hoạt ảnh Góc Nhìn Thứ Nhất (POV) toàn màn hình khi nấu & phục vụ**: Khi lên bếp nấu (`cook_started`), màn hình chuyển sang POV toàn màn hình 3 bước (**Bật bếp vặn núm đánh lửa → Lắc chảo gang xào nấu tung nguyên liệu & lửa áp chảo → Hoàn thiện bốc khói**); khi lên món (`served`), POV bưng mâm tre đặt trước mặt thực khách kèm phản ứng nhận tiền boa (nhấp chuột / `Space` để bỏ qua nhanh).
- **Âm thanh ngũ cung Nam Bộ & SFX tổng hợp bằng Web Audio API**: Nhạc nền sáng/tối theo thang âm ngũ cung, hiệu ứng âm thanh đánh lửa bếp ga, xèo xèo xào chảo, bắt cá, hái hoa, nhận boa; lưu cài đặt âm lượng Master/Music/SFX ở `localStorage`.
- **Trải nghiệm Demo hoàn chỉnh**: Màn hình Menu chính, DayIntro/EveningIntro chuyển ca, Shop nâng cấp, Pause (`Esc`/`P`), tùy chọn `--cook-scale` riêng cho live và kịch bản demo 3 phút (`docs/DEMO.md`).

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
