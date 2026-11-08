from kakuro.board import WHITE_CELLS, ALL_GROUPS, ROWS

def validate_solution(solution):
  errors = []

  if solution is None:
    return False, ["Không có lời giải để kiểm tra."]

  missing = [cell for cell in WHITE_CELLS if cell not in solution]
  extra = [cell for cell in solution if cell not in set(WHITE_CELLS)]
  if missing:
    errors.append(f"Còn thiếu ô: {missing}")
  if extra:
    errors.append(f"Có tạo độ không phải ô trắng: {extra}")

  for cell in WHITE_CELLS:
    if cell in solution and solution[cell] not in range(1, 10):
      errors.append(f"Giá trị tại {cell} không thuộc 1..9.")

  for index, (target, cells) in enumerate(ALL_GROUPS, start = 1):
    if any(cell not in solution for cell in cells):
      continue
    values = [solution[cell] for cell in cells]
    if sum(values) != target:
      errors.append(
        f"Nhóm {index} tổng sai: {values}, tổng={sum(values)}, cần={target}."
      )
    if len(values) != len(set(values)):
      errors.append(f"Nhóm {index} bị lặp chữ số: {values}.")

  return len(errors) == 0, errors

def print_grid(solution):
  for r, row in enumerate(ROWS, start=1):
    output = []
    for c, char in enumerate(row, start=1):
      if char == "#":
        output.append("#")
      else:
        value = solution.get((r, c), ".")
        output.append(str(value))
    print(" ".join(f"{x:>2}" for x in output))

def print_group_report(solution):
  for index, (target, cells) in enumerate(ALL_GROUPS, start=1):
    values = [solution[cell] for cell in cells]
    direction = "ngang" if index <= 14 else "dọc"
    print(
      f"{index:02d}. {direction:5} | "
      f"sum={target:2d} | values={values} | actual={sum(values)} | "
      f"unique={len(values) == len(set(values))}"
    )