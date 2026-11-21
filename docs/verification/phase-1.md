# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Gather: oxy, lặn/nổi, ngạt, ngất (O1–O9) | Unit `tests/test_gather_p1_units.py::Oxygen` | [gather-tests.md](../proof/phase-1/gather-tests.md) | đạt (9/9) |
| Gather: hái và giỏ (G1–G7) | Unit `tests/test_gather_p1_units.py::Gathering` | [gather-tests.md](../proof/phase-1/gather-tests.md) | đạt (7/7) |
| Gather: bắt cá, hồi chiêu (C1–C9) | Unit `tests/test_gather_p1_units.py::Catching` | [gather-tests.md](../proof/phase-1/gather-tests.md) | đạt (9/9) |
| Gather: kết thúc docked/time/fainted (E1–E5) | Unit `tests/test_gather_p1_units.py::Ending` | [gather-tests.md](../proof/phase-1/gather-tests.md) | đạt (5/5) |
| Gather → kho → Quan, tất định (I1–I5) | Integration `tests/test_gather_p1_integration.py` | [gather-tests.md](../proof/phase-1/gather-tests.md) | đạt (5/5) |
| Quan | chưa kiểm | — | chưa đạt (chưa có test) |

> Cột AC đang ghi theo nhóm ca trong checklist QA vì `docs/plan/phase-1.md` chưa có mã AC; khi PO chốt mã AC thì thay vào.

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
