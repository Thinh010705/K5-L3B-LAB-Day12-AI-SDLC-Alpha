# Nhóm Alpha — Hợp đồng tích hợp phiên bản 1.0 (Giai đoạn 1)

**Người phụ trách:** Integrator (`@Thinh010705`)  
**Trạng thái:** Bản đề xuất để nhóm rà soát; chỉ có hiệu lực khi thành viên phụ trách Gather, Quan, UI và QA xác nhận.  
**Nguồn quy định chính:** `game.contract.json` và các module starter `chonoi/{headless,inventory,runner,jsonl,scenario}.py`. Không sao chép các thông số cấu hình sang logic chạy khác.

## 1. Ranh giới và trách nhiệm giữa các module

| Phần việc | Người phụ trách | Đầu vào | Đầu ra |
|---|---|---|---|
| Cơ chế chơi Gather (thu thập) | Lập trình viên Gather | Kịch bản, `--inputs`, seed, tham số cấu hình | Sự kiện `gather_end`, danh sách `hold`, dữ liệu JSONL |
| Chuyển giao kho nguyên liệu | Integrator / core starter | `GatherSim.inventory_items()` sau khi Gather thực sự kết thúc | Tệp JSON được ghi an toàn qua `--inventory-out` |
| Cơ chế chơi Quan (quán ăn) | Lập trình viên Quan | JSON qua `--inventory` **hoặc** `scenario.quan.stock` (không dùng đồng thời) | Snapshot/sự kiện Quan, tiền và uy tín |
| Giao diện | Lập trình viên UI | `Session.snapshot()` và danh sách sự kiện | Hiển thị dữ liệu; không tự triển khai lại luật mô phỏng |
| Xác minh và kiểm thử hồi quy | QA + Integrator | Cả hai chế độ, dữ liệu lỗi, các lần chạy tất định | Log kiểm thử và bằng chứng xác minh |

`chonoi/sim/gather.py` và `chonoi/sim/quan.py` do các thành viên được phân công quản lý. Nếu muốn thay đổi hợp đồng, nhóm cần thống nhất trước khi merge.

## 2. Hợp đồng chuyển giao kho nguyên liệu (Hợp đồng G)

Định dạng chuẩn của tệp kho:

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Tệp JSON có **duy nhất một khóa cấp cao nhất** là `items`. Giá trị của khóa này là một object ánh xạ mã nguyên liệu tới số lượng nguyên không âm. Giá trị `bool` trong Python **không được** tính là số lượng nguyên hợp lệ.
- Mã nguyên liệu cho phiên bản 1.0: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Khi ghi tệp, hệ thống bỏ các nguyên liệu có số lượng bằng 0, xuất khóa theo thứ tự ổn định, kết thúc tệp bằng ký tự xuống dòng và thay thế tệp theo cách an toàn (atomic). Dữ liệu kho nhập vào phải được kiểm tra hợp lệ **trước khi** headless tạo tệp đầu ra.
- `hold` của Gather là **danh sách theo thứ tự nhặt được** (mới nhất ở cuối danh sách, phục vụ cơ chế LIFO). Tệp kho chuyển giao chỉ lưu **số lượng theo loại**, không lưu thứ tự nhặt; Quan không được phụ thuộc vào thứ tự `hold`.
- Tệp kho chỉ được ghi **một lần khi Gather thực sự hoàn tất** (`Session.sim.done`) và người chạy có truyền `--inventory-out`. Nếu mô phỏng chỉ dừng vì đạt `--ticks`, chương trình **không được** tạo hoặc ghi đè tệp kho.
- Khi có xuất kho, `gather_end.data.inventory` phải bằng nội dung tệp kho. Nếu nhân vật ngất, người phụ trách Gather phải bảo đảm kho được ghi đúng quy định mất giỏ trong PRD.
- Quan nạp kho bằng `--inventory FILE`. Nếu vừa truyền `--inventory` vừa khai báo `scenario.quan.stock`, hệ thống phải báo lỗi, không được tự động cộng hoặc gộp hai kho.
- Tên và đường dẫn tệp do người gọi lệnh quyết định. Không được giả định một đường dẫn toàn cục hay ghi cứng `kho.json` bên trong logic mô phỏng.

### Quy tắc kết thúc Gather

| Lý do | Kho xuất ra |
|---|---|
| `docked` | Toàn bộ nguyên liệu còn trong giỏ |
| `time` | Toàn bộ nguyên liệu còn trong giỏ |
| `fainted` | Kho rỗng `{"items":{}}` |
| `tick_limit` | Không tạo hoặc ghi đè file kho |

Khi ghi kho, chương trình phải ghi vào file tạm
cùng thư mục đích rồi thay thế file đích theo cách nguyên tử.

Nội dung file kho phải khớp với
`gather_end.data.inventory`.

## 3. Hợp đồng dòng lệnh (CLI) và mã thoát

Thực hiện từ thư mục gốc của repository:

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 \
  --scenario gather_scenario.json --inputs gather_inputs.json \
  --inventory-out kho.json --out gather.jsonl

python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 \
  --inventory kho.json --out quan.jsonl
```

Các lệnh trên minh họa **cú pháp**; lệnh Quan chỉ chạy thành công nếu bước Gather trước đó đã kết thúc hợp lệ và thực sự tạo `kho.json`.

- Mã thoát `0`: chạy bình thường; `2`: tham số/dữ liệu đầu vào không hợp lệ (phải từ chối **trước khi tạo tệp đầu ra**); `1`: lỗi runtime hoặc ghi tệp.
- Chế độ hỗ trợ ở phiên bản 1.0: `gather` và `quan`. Chế độ `day` **chưa được hỗ trợ** cho tới khi có phiên bản hợp đồng mới quy định rõ.
- Đường dẫn tệp đầu vào và đầu ra không được trùng nhau. `--inventory` chỉ dùng cho Quan; `--inventory-out` chỉ dùng cho Gather.
- Cùng seed và cùng đầu vào phải cho tệp JSONL và tệp kho **giống nhau từng byte**. Sử dụng `Streams` được seed, thứ tự ID ổn định và mô hình tick cố định (`tick_hz` trong cấu hình).

## 4. Thứ tự bản ghi sự kiện JSONL (Hợp đồng B)

Mỗi lần chạy bắt đầu bằng `snapshot` tại tick `0`, tiếp theo là các `event` sinh ra trong từng tick theo thứ tự xử lý, sau đó là `snapshot` đến hạn (hoặc snapshot cuối), và **đúng một** dòng `end` kết thúc. Mỗi tick có tối đa một snapshot.

Ví dụ cấu trúc (giá trị minh họa, **không phải log chạy thật**):

```json
{"type":"event","tick":1,"phase":"gather","name":"gather_end","data":{"reason":"docked","inventory":{"items":{"ca_loc":1}}}}
```

```json
{"type":"snapshot","tick":0,"sim_tick":0,"mode":"quan","phase":"quan","phase_tick":0,"state":"playing","stock":{"ca_loc":1}}
```

Ví dụ `snapshot` ở trên chỉ ghi **một số trường tiêu biểu**, không phải toàn bộ schema JSONL; không sử dụng nó làm dữ liệu fixture đầy đủ. Snapshot thực tế còn chứa các trường chung và trường riêng theo chế độ.

Các trường chung của snapshot gồm: `type`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score`. Trường riêng của từng chế độ được liệt kê trong `UI_SNAPSHOT_V1.md`.

## 5. Điều kiện nghiệm thu trước khi merge/gắn tag

1. `python3 tools/check_team.py` báo hợp lệ với **5 thành viên thật**; `TEAM.md` và `game.contract.json` phải thống nhất.
2. Bộ kiểm thử sẵn có chạy đạt: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.
3. Bộ kiểm thử tích hợp bổ sung chạy đạt: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -p 'test_integration_alpha.py' -v`.
4. QA lưu **log Terminal chạy thật** trong `docs/proof/phase-1/` và cập nhật `docs/verification/phase-1.md` bằng kết quả quan sát được.
5. Integrator chỉ gắn tag `phase-1` khi việc tích hợp, kiểm thử và bằng chứng đã hoàn tất, đồng thời tuân thủ mốc thời gian chính thức của lab.

**Quản lý thay đổi:** nếu Giai đoạn 2 trở đi bổ sung mã nguyên liệu, trường snapshot hoặc thay đổi quy tắc CLI, cần ghi rõ phiên bản hợp đồng mới và chạy lại kiểm thử hồi quy Giai đoạn 1 trước khi chấp thuận. Không tự triển khai trước các yêu cầu phase đang bị khóa.
