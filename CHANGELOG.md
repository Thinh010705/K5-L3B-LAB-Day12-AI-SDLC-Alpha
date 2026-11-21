# Changelog
## Unreleased

### Phase 3 — đang tích hợp

- **Breaking change khi bật contract v1.2:** file kho đổi từ `{"items":{"ca_linh":2}}` sang `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Fixture `gather.hold` và `quan.stock` cũng cần mảng cá thể. File kho đếm sẽ bị từ chối với mã 2; cần tạo lại fixture với id duy nhất và độ tươi từng cá thể.
- Đã thêm bộ đọc/ghi file chọn schema theo `contract_version`, bảo toàn id và độ tươi, kiểm dữ liệu và thay file nguyên tử. Manifest đang là v1.1 trong lúc Gather/Quan/Day chuyển luật.
