# Nhóm Alpha — Kế hoạch tích hợp qua các giai đoạn

**Người phụ trách chính:** Integrator (`@Thinh010705`)  
**Nguyên tắc:** Tích hợp từng thay đổi nhỏ, giữ `main` chạy được và chỉ xác nhận các mốc có bằng chứng thực tế.

## Giai đoạn 1: Thiết lập nền tảng và thống nhất hợp đồng

1. Xác nhận `TEAM.md` chứa đủ **5 tài khoản GitHub thật**; đồng bộ tên nhóm và số thành viên trong `game.contract.json`.
2. Công bố `INTEGRATION_V1.md` và `UI_SNAPSHOT_V1.md`; xin xác nhận trong kênh nhóm từ bốn người phụ trách Gather, Quan, UI, QA.
3. Sau khi thống nhất hợp đồng dữ liệu, các thành viên
   triển khai song song Gather, Quan, UI và QA.

   Người phụ trách Quan sử dụng file kho mẫu để phát triển
   độc lập, không cần chờ Gather hoàn thiện.

   Integrator nhận các thay đổi đã kiểm tra, tích hợp
   từng phần vào `main` và chạy lại regression tests.
4. Chạy test sẵn có cùng `test_integration_alpha.py`; lưu log thực tế tại `docs/proof/phase-1/`.
5. Ghi kết quả vào `docs/verification/phase-1.md`, bao gồm cả tiêu chí chưa đạt. Chỉ gắn tag `phase-1` tại mốc chính thức khi trạng thái tích hợp được xác minh.

## Giai đoạn 2–4: Cập nhật theo yêu cầu mới, không tự đoán trước

Khi yêu cầu của giai đoạn mới được mở:

- **PO:** ghi câu hỏi, quyết định và căn cứ vào `docs/clarify.md`.
- **Integrator:** lập danh sách thay đổi contract, nhu cầu chuyển đổi dữ liệu và xác định người thực hiện/người review cho từng thay đổi.
- **Chủ module:** triển khai trên nhánh nhỏ, dễ kiểm tra; QA bổ sung test phase mới và chạy lại test phase cũ.
- **Integrator:** kiểm tra tương thích schema và tích hợp các nhánh, sau đó tạo tag checkpoint thực tế. Không ép cập nhật (`force-update`) tag đã nộp.
- **Scrum/Release:** phối hợp phát hành `v1.0.0` sau Giai đoạn 4 khi game và demo sẵn sàng.

## Quy trình Git đề xuất

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/integration-contracts
# Thêm docs/contracts/, tests/test_integration_alpha.py và nhật ký cá nhân.
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
git add docs/contracts tests/test_integration_alpha.py docs/members/Thinh010705.md docs/verification/integrator-p1.md
git commit -m "docs: define Phase 1 integration contracts"
git push -u origin feature/integration-contracts
# Tạo PR, nhờ thành viên khác review; chỉ merge khi có test và bằng chứng.
```

**Lưu ý quan trọng:** Không chạy `git tag` từ nhánh feature chưa được merge. Tag cần trỏ đến commit `main` đã được tích hợp và kiểm thử. Khi làm lab trực tiếp, tuân thủ đồng hồ/mốc chính thức, không tự đặt deadline khác.

## Nội dung bàn giao cho từng người

- **Gather:** trả sự kiện đúng thứ tự quy định, giữ đúng thứ tự `hold`, bảo đảm `gather_end.inventory` phản ánh kho thực tế.
- **Quan:** nạp kho đã được kiểm tra vào `stock` ngay tại tick 0; từ chối trường hợp dùng đồng thời `scenario.quan.stock` và `--inventory`.
- **UI:** sử dụng các trường của `Session.snapshot()` đúng như tài liệu; UI không sở hữu hoặc tự tính luật chơi.
- **QA:** kiểm tra chuyển kho thành công, tệp kho sai, tính tất định và khả năng ghi output an toàn; chỉ ghi nhận kết quả kiểm thử đã chạy thật.
