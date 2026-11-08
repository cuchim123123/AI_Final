import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from queue import Queue, Empty

from kakuro.board import ROWS, WHITE_CELLS, HORIZONTAL_GROUPS, VERTICAL_GROUPS
from kakuro.solver import KakuroSolver
from kakuro.validator import validate_solution


class KakuroApp:
    CELL_SIZE = 66

    def __init__(self, root):
        self.root = root
        self.root.title("Task 3 - Kakuro CSP Solver")
        self.root.geometry("1000x780")
        self.queue = Queue()
        self.solver = None
        self.labels = {}
        self.solution = None
        self._build_ui()
        self._draw_grid()
        self.root.after(80, self._process_events)

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(
            top,
            text="Kakuro 9×9 — CSP / Backtracking Search",
            font=("Arial", 16, "bold"),
        ).pack(side="left")
        self.solve_button = ttk.Button(top, text="Giải bài toán", command=self.solve)
        self.solve_button.pack(side="right", padx=4)
        self.reset_button = ttk.Button(top, text="Làm mới", command=self.reset)
        self.reset_button.pack(side="right", padx=4)

        middle = ttk.Frame(self.root, padding=8)
        middle.pack(fill="both", expand=True)

        self.board_frame = ttk.Frame(middle)
        self.board_frame.pack(side="left", anchor="n", padx=(0, 12))

        side = ttk.Frame(middle)
        side.pack(side="left", fill="both", expand=True)
        ttk.Label(side, text="Diễn biến thuật toán", font=("Arial", 11, "bold")).pack(anchor="w")
        self.log = tk.Text(side, width=48, height=31, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(side, command=self.log.yview)
        scrollbar.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scrollbar.set)

        self.status = tk.StringVar(value="Sẵn sàng. Nhấn “Giải bài toán”.")
        ttk.Label(self.root, textvariable=self.status, padding=8).pack(fill="x")

    def _draw_grid(self):
        for child in self.board_frame.winfo_children():
            child.destroy()
        self.labels.clear()
        white_set = set(WHITE_CELLS)

        for r in range(1, 10):
            for c in range(1, 10):
                cell = (r, c)
                if cell not in white_set:
                    label = tk.Label(
                        self.board_frame,
                        text="#",
                        width=7,
                        height=3,
                        bg="#30343b",
                        fg="white",
                        relief="ridge",
                        borderwidth=1,
                    )
                else:
                    label = tk.Label(
                        self.board_frame,
                        text="{1..9}",
                        width=7,
                        height=3,
                        bg="white",
                        fg="#222222",
                        relief="ridge",
                        borderwidth=1,
                        font=("Consolas", 9),
                    )
                    self.labels[cell] = label
                label.grid(row=r - 1, column=c - 1, sticky="nsew")
        for r in range(9):
            self.board_frame.grid_rowconfigure(r, weight=1)
        for c in range(9):
            self.board_frame.grid_columnconfigure(c, weight=1)

    def _log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _event_callback(self, event, details, solver):
        # Solver chạy ở worker thread; chỉ gửi sự kiện vào queue.
        self.queue.put((event, details, dict(solver.domains), dict(solver.assignment),
                        solver.nodes, solver.backtracks, solver.propagation.steps))

    def _process_events(self):
        try:
            while True:
                event, details, domains, assignment, nodes, backtracks, steps = self.queue.get_nowait()
                self._render_event(event, details, domains, assignment)
                self.status.set(
                    f"Nodes: {nodes} | Backtracks: {backtracks} | "
                    f"Domain reductions: {steps}"
                )
        except Empty:
            pass
        self.root.after(80, self._process_events)

    def _render_event(self, event, details, domains, assignment):
        if event == "start":
            self._log("Bắt đầu lan truyền ràng buộc...")
        elif event == "domain":
            cell = details["cell"]
            self._log(f"Miền {cell} → {details['domain']}")
            if cell in self.labels and cell not in assignment:
                self.labels[cell].configure(text="{" + ",".join(map(str, details["domain"])) + "}")
        elif event == "select":
            self._log(f"MRV chọn ô {details['cell']}, miền={details['domain']}")
        elif event == "try":
            self._log(f"Thử ô {details['cell']} = {details['value']}")
            if details["cell"] in self.labels:
                self.labels[details["cell"]].configure(
                    text=str(details["value"]), bg="#fff0b3"
                )
        elif event == "backtrack":
            self._log(f"Quay lui: ô {details['cell']} = {details['value']} không dẫn đến lời giải")
            cell = details["cell"]
            if cell in self.labels:
                self.labels[cell].configure(bg="white")
        elif event == "contradiction":
            self._log(f"Mâu thuẫn ràng buộc: {details}")
        elif event == "solved":
            self._log(
                f"Tìm thấy lời giải! nodes={details['nodes']}, "
                f"backtracks={details['backtracks']}"
            )
        elif event == "unsolved":
            self._log("Không tìm được lời giải cho dữ liệu hiện tại.")

    def solve(self):
        self.solve_button.configure(state="disabled")
        self._log("─" * 32)
        self._log("Khởi chạy CSP solver...")
        def worker():
            solver = KakuroSolver(event_callback=self._event_callback)
            result = solver.solve()
            valid, errors = validate_solution(result)
            self.queue.put(("final", {"result": result, "valid": valid, "errors": errors,
                                      "nodes": solver.nodes,
                                      "backtracks": solver.backtracks,
                                      "steps": solver.propagation.steps},
                            dict(solver.domains), dict(solver.assignment),
                            solver.nodes, solver.backtracks, solver.propagation.steps))
        Thread(target=worker, daemon=True).start()
        self.root.after(100, self._check_final)

    def _check_final(self):
        # Final event is handled by _process_events; polling is only to re-enable button
        # when a final message arrives.
        if getattr(self, "_finished", False):
            self.solve_button.configure(state="normal")
            self._finished = False
        else:
            self.root.after(150, self._check_final)

    def reset(self):
        self.solution = None
        self._draw_grid()
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status.set("Đã làm mới.")
        self._finished = False

    def _handle_final(self, details):
        self._finished = True
        result = details["result"]
        if details["valid"]:
            self.solution = result
            for cell, value in result.items():
                self.labels[cell].configure(text=str(value), bg="#c8f7c5", fg="#111111")
            self._log("Xác thực độc lập: PASS — 28/28 nhóm hợp lệ.")
            self.status.set(
                f"Hoàn tất: PASS | nodes={details['nodes']} | "
                f"backtracks={details['backtracks']} | propagation={details['steps']}"
            )
        else:
            self._log("Xác thực: FAIL")
            for error in details["errors"]:
                self._log(error)
            messagebox.showerror("Lỗi xác thực", "\n".join(details["errors"]))

    # Override event processing to handle final events.
    def _process_events(self):
        try:
            while True:
                event, details, domains, assignment, nodes, backtracks, steps = self.queue.get_nowait()
                if event == "final":
                    self._handle_final(details)
                    continue
                self._render_event(event, details, domains, assignment)
                self.status.set(
                    f"Nodes: {nodes} | Backtracks: {backtracks} | Domain reductions: {steps}"
                )
        except Empty:
            pass
        self.root.after(80, self._process_events)


def run_app():
    root = tk.Tk()
    KakuroApp(root)
    root.mainloop()
