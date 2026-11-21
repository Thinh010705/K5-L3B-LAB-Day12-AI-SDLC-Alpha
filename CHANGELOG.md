# Changelog
## Unreleased

### Phase 3 — đang tích hợp

- **Breaking change khi bật contract v1.2:** file kho đổi từ `{"items":{"ca_linh":2}}` sang `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Fixture `gather.hold` và `quan.stock` cũng cần mảng cá thể. File kho đếm sẽ bị từ chối với mã 2; cần tạo lại fixture với id duy nhất và độ tươi từng cá thể.
- Đã bật manifest v1.2, chuyển file và snapshot sang cá thể, bổ sung hiển thị độ tươi/ươn và lịch dòng lũ. Test unit cơ chế P1/P2 dùng manifest P2 đã khóa; fixture CLI dùng schema v1.2. Đây là thay đổi kỳ vọng test do hợp đồng kho đổi, không phải bỏ kiểm tra luật cũ.
