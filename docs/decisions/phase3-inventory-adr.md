# ADR-P3-01 – Chuyển inventory sang kho cá thể (v1.2)

**Trạng thái:** Quyết định thiết kế của nhóm Alpha (cần đối chiếu với implementation thực tế)  
**Nguồn yêu cầu:** TICKET-03 – Mùa Nước Nổi  
**Phạm vi:** Contract/Inventory, Gather, Quan, Day, Shop, HUD và QA

## Bối cảnh

Phase 1–2 dùng kho đếm theo `kind`; không biểu diễn được độ tươi, tuổi nguyên liệu và danh tính từng phần hàng. TICKET-03 thay thế hoàn toàn schema kho theo loại bằng mảng cá thể. Điều này là breaking change đối với file kho, fixture, scenario, JSONL và reserved orders.

## Quyết định

1. **Schema v1.2 chuẩn:** `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`; root chỉ có `items`, mỗi item phải có đúng `id`, `kind`, `fresh` theo Test Contract.
2. **Ràng buộc:** ID chuỗi khác rỗng và duy nhất, kind thuộc nguyên liệu được khai, fresh hữu hạn trong `[0,100]`. File đếm từ bản cũ bị từ chối với mã 2 khi dùng contract v1.2.
3. **Cấp ID:** `I1,I2,...` theo thứ tự vào giỏ, không tái sử dụng; duy trì qua các pha/ngày, kể cả ID đã dùng hoặc bỏ. Ngày đầu giữ ID từ fixture; các ngày sau cấp ID mới theo thứ tự fixture.
4. **Biểu diễn tươi:** Đề xuất fixed-point 240 đơn vị/điểm để biểu diễn chính xác trong nội bộ: hàng mới 24000 đơn vị; Gather trừ 2 đơn vị/tick; Quan trừ 1 đơn vị/tick; ngưỡng 30 là 7200 đơn vị. JSON/JSONL vẫn dùng số `fresh` trong 0–100. Cần kiểm thử với các fixture có độ tươi không nằm đúng lưới fixed-point trước khi dùng làm biểu diễn duy nhất.
5. **Hao tươi:** Hàng mới bắt đầu hao từ bước sau. Pause dừng hao, món đã nấu không hao. `spoiled` được phát một lần khi đi từ `fresh >= 30` sang `< 30`, sắp theo ID.
6. **Giữ hàng và giá:** Giữ theo ID, ưu tiên fresh lớn, hòa theo ID; item ươn không dùng nấu. Khi hàng đang giữ ươn, giải phóng toàn bộ giữ chỗ của đơn và thử giữ lại đúng một lần; khi bắt đầu nấu chốt giá bằng phép `floor` theo độ tươi trung bình.
7. **Bàn giao:** Gather → Quan trong Day giữ nguyên cá thể cùng tick, không hao thêm. File `--inventory-out` chỉ ghi khi có `gather_end`, thay thế nguyên tử với file tạm cùng thư mục, không ghi khi chỉ chạm `--ticks`.
8. **Bật version:** Khi các module dùng chung schema mới ổn định mới chuyển manifest trên `main` thành v1.2; giữ kiểm thử cho luật cũ còn hiệu lực, cập nhật fixture khi contract thay thế.

## Thứ tự tích hợp

1. Contract v1.2, validator, inventory adapter, test schema/migration.
2. Gather và Quan thực thi schema chung độc lập.
3. Day, Shop, HUD nhận snapshot mới; xác nhận tick bàn giao.
4. QA smoke hai tiến trình, ngưỡng và giá; regression cũ còn hiệu lực.
5. Commit tài liệu, bằng chứng trên `main` và tạo tag nghiệm thu.

## Hệ quả và rủi ro

- **Tương thích:** file kho đếm cũ không thể đọc dưới contract v1.2; phải cập nhật fixture/test.
- **Tính đúng:** nếu dùng số thực mà làm tròn trước khi so ngưỡng 30 có thể gây lệch tick; cần so với giá trị chính xác nội bộ.
- **Tính nhất quán:** hai đơn không được giữ chung một item; ID đã dùng không thể được cấp lại.
- **Hiệu năng:** giữ ID và fresh tăng chi phí bộ nhớ nhưng cho phép kiểm thử truy vết rõ hơn.
- **Giao diện:** snapshot đổi cấu trúc nên UI phải được kiểm thử cùng bản runtime, không đoán trường dữ liệu.

## Chủ sở hữu và review

- Chủ trì quyết định/adapter: Integrator.
- Code Gather/Quan/Day/UI: owner tương ứng.
- Xác nhận test và breaking change: QA.
- Theo dõi actual implementation: đối chiếu PR/commit trên `main` trước khi đánh dấu ADR là đã triển khai.
