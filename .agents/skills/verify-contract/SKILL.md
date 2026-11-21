---
name: verify-contract
description: Kiểm tra tính toàn vẹn của Test Contract (game.contract.json) và chạy kiểm thử tự động toàn hệ thống.
---

# verify-contract

Dùng skill này khi chuẩn bị tích hợp nhánh, nâng cấp phiên bản Test Contract hoặc trước khi gắn tag release.

## Quy trình thực hiện
1. **Kiểm tra schema contract:**
   ```powershell
   python -c "from chonoi.contract import load_contract; c = load_contract(); print('Contract version:', c['contract_version'])"
   ```
2. **Kiểm tra danh sách thành viên:**
   ```powershell
   python tools/check_team.py
   ```
3. **Chạy toàn bộ 176 test hồi quy:**
   ```powershell
   $env:PYTHONPATH = "tests;."
   python -m unittest discover -s tests -v
   ```
4. **Tiêu chuẩn đạt:** Mọi test đều `ok`, mã thoát 0. Nếu có lỗi, đọc kỹ traceback và đối chiếu phiên bản contract, không sửa test cho xanh nếu luật đang sai.
