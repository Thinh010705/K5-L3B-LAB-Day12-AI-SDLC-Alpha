# Bằng chứng Phase 3

Thư mục chứa kết quả chạy trên mã nguồn của nhóm Alpha tại thời điểm nghiệm thu. Không chỉnh tay kết quả để biến FAIL thành PASS.

| File | Nội dung |
|---|---|
| `git-baseline.txt` | Branch, commit hash trước đóng hồ sơ và git status |
| `manifest-audit.txt` | Contract version, extension và thông số freshness được đọc từ manifest |
| `regression.log` | Kết quả `unittest discover -s tests -v` |
| `freshness-threshold.jsonl` | Scenario I1=30, Gather một bước và event `spoiled` |
| `gather-handoff.jsonl` | Gather cập bến, chứa `gather_end` và snapshot |
| `inventory-v12.json` | Kho được Gather xuất theo schema cá thể |
| `quan-stock-tick0.jsonl` | Quan đọc inventory tại tick 0 |
| `inventory-count-rejection.stderr` | Lỗi từ chối schema kho đếm v1.1 dưới v1.2 |
| `day-1.jsonl` | Day chạy đủ 1 ngày |
| `smoke-summary.txt` | Kết quả đối chiếu tự động, nên kiểm tra cùng raw JSONL |
| `ui-*.png` / `ui-*.mp4` | Bằng chứng hiển thị fresh/ươn, cần chụp từ bản chạy thật |
| `extension-*.log` | Test tương ứng mã `extensions` trong `game.contract.json` |

**Tạo tự động:** từ gốc repo, chạy `bash tools/phase3_collect_proof.sh`. Lệnh này chỉ thu thập một phần AC; các tiêu chí giữ chỗ/giá/UI/extension vẫn cần test tương ứng. Không đưa file bí mật hoặc file cá nhân vào bằng chứng.

**Lưu ý về commit:** log `git-baseline.txt` là commit trước khi cập nhật tài liệu/bằng chứng. Commit tag cuối cùng phải được xác nhận bằng `git rev-parse 'phase-3^{commit}'` sau khi commit docs; không sao chép hash cũ làm hash release.
