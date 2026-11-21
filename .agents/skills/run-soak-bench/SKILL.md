---
name: run-soak-bench
description: Thực thi và nghiệm thu kiểm thử độ bền 10 ngày (soak test) và đo hiệu năng render Canvas 2D (benchmark) theo Test Contract v1.3.
---

# run-soak-bench

Dùng skill này khi cần kiểm tra hiệu năng, độ ổn định đa ngày và tạo bằng chứng thực nghiệm cho Phase 4 / Release.

## Quy trình thực hiện
1. **Chạy Soak Test (10 ngày liên tục):**
   ```powershell
   python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json
   ```
   - Kiểm tra `soak.json`: `days_completed == 10`, `crashes == 0`.
2. **Chạy Benchmark có render Canvas 2D (30 giây sau 3 giây warm-up):**
   ```powershell
   python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
   ```
   - Kiểm tra `bench.json`: `avg_fps >= 60`, `p1_low_fps >= 30`, `load_ms <= 10000`.
3. **Lưu nhật ký hồi quy:**
   ```powershell
   $env:PYTHONPATH = "tests;."
   python -m unittest discover -s tests -v > docs/proof/phase-4/regression.log 2>&1
   ```
