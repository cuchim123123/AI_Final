# Task 3 — Kakuro CSP Solver

## Cấu trúc
- `main.py`: điểm khởi chạy.
- `kakuro/board.py`: ma trận và 28 nhóm gợi ý.
- `kakuro/csp.py`: biến, miền giá trị, ràng buộc.
- `kakuro/solver.py`: Backtracking Search.
- `kakuro/heuristics.py`: MRV, Degree Heuristic, LCV.
- `kakuro/propagation.py`: Constraint Propagation, Forward Checking.
- `kakuro/validator.py`: kiểm tra lời giải độc lập.
- `ui/app.py`: giao diện Tkinter.
- `tests/test_solver.py`: kiểm thử tự động.

## Yêu cầu
Python 3.10 trở lên. Tkinter thường có sẵn trong Python trên Windows.

## Chạy
```bash
python main.py
python main.py --groups
python main.py --ui
python -m unittest discover -s tests -v
```

## CSP và thuật toán
Mỗi ô trắng là một biến, miền ban đầu `{1, ..., 9}`. Mỗi nhóm yêu cầu tổng bằng gợi ý và chữ số không lặp. Bộ giải dùng Constraint Propagation, Backtracking Search, MRV, Degree Heuristic, LCV và Forward Checking. Validator kiểm tra độc lập toàn bộ 28 nhóm.
