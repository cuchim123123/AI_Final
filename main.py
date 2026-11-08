import argparse
from kakuro.solver import KakuroSolver
from kakuro.validator import validate_solution, print_grid, print_group_report

def run_terminal(show_groups=False):
    solver=KakuroSolver(); solution=solver.solve()
    if solution is None:
        print('Không tìm được lời giải.'); return 1
    valid,errors=validate_solution(solution)
    print('\nLƯỚI KAKURO 9x9'); print_grid(solution)
    print(f"\nXác thực: {'PASS' if valid else 'FAIL'}")
    print(f'Nodes: {solver.nodes}')
    print(f'Backtracks: {solver.backtracks}')
    print(f'Propagation steps: {solver.propagation.steps}')
    if show_groups:
        print('\nBÁO CÁO 28 NHÓM'); print_group_report(solution)
    if errors:
        for error in errors: print(error)
        return 1
    print('Đã xác minh tổng và tính không trùng của tất cả 28 nhóm.')
    return 0

def main():
    parser=argparse.ArgumentParser(description='Kakuro CSP Solver')
    parser.add_argument('--ui',action='store_true',help='Mở giao diện Tkinter')
    parser.add_argument('--groups',action='store_true',help='In báo cáo 28 nhóm')
    args=parser.parse_args()
    if args.ui:
        from ui.app import run_app
        run_app()
    else: raise SystemExit(run_terminal(args.groups))
if __name__=='__main__': main()
