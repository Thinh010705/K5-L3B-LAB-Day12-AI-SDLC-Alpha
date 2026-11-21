# Phase 4 Proof Artifacts — Release v1.0.0 & Test Contract v1.3

Thư mục này chứa các file bằng chứng thực nghiệm của Phase 4 cho nhóm Alpha:

| File | Mô tả | Kết quả |
|---|---|---|
| [`bench.json`](file:///d:/vinAI/lab12/K5-L3B-LAB-Day12-AI-SDLC-Alpha/docs/proof/phase-4/bench.json) | Kết quả đo hiệu năng có render Canvas 2D 1280x720 qua `chonoi.bench` (`bench_cmd`) | `avg_fps`: 69 (yêu cầu $\ge 60$), `p1_low_fps`: 31 (yêu cầu $\ge 30$), `load_ms`: 2 (yêu cầu $\le 10000$), `frames`: 2059 |
| [`soak.json`](file:///d:/vinAI/lab12/K5-L3B-LAB-Day12-AI-SDLC-Alpha/docs/proof/phase-4/soak.json) | Kết quả chạy soak test headless 10 ngày liên tục qua `chonoi.soak` (`soak_cmd`) | `days_completed`: 10/10, `crashes`: 0, `duration_s`: 1.32s |
| [`regression.log`](file:///d:/vinAI/lab12/K5-L3B-LAB-Day12-AI-SDLC-Alpha/docs/proof/phase-4/regression.log) | Log chạy toàn bộ bộ test hồi quy tự động của dự án | **176/176 tests pass** trong 8.517s |

## Lệnh tái hiện bằng chứng

```powershell
# 1. Benchmark có render (30s)
python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json

# 2. Soak test headless 10 ngày
python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json

# 3. Chạy toàn bộ test hồi quy
$env:PYTHONPATH = "tests;."
python -m unittest discover -s tests -v > docs/proof/phase-4/regression.log 2>&1
```

