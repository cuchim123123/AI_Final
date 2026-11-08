ROWS = [
  "#########",
  "##...#..#",
  "##.......",
  "#..##....",
  "#..#....#",
  "##....#..",
  "#....##..",
  "#.......#",
  "##..#...#",
]

HORIZONTAL_GROUPS = [
    (22, [(2, 3), (2, 4), (2, 5)]),
    (3,  [(2, 7), (2, 8)]),
    (28, [(3, c) for c in range(3, 10)]),
    (14, [(4, 2), (4, 3)]),
    (20, [(4, c) for c in range(6, 10)]),
    (17, [(5, 2), (5, 3)]),
    (22, [(5, c) for c in range(5, 9)]),
    (28, [(6, c) for c in range(3, 7)]),
    (12, [(6, 8), (6, 9)]),
    (14, [(7, c) for c in range(2, 6)]),
    (6,  [(7, 8), (7, 9)]),
    (39, [(8, c) for c in range(2, 9)]),
    (16, [(9, 3), (9, 4)]),
    (8,  [(9, 6), (9, 7), (9, 8)]),
]

VERTICAL_GROUPS = [
    (44, [(r, 3) for r in range(2, 10)]),
    (16, [(2, 4), (3, 4)]),
    (9,  [(2, 5), (3, 5)]),
    (15, [(r, 7) for r in range(2, 6)]),
    (44, [(r, 8) for r in range(2, 10)]),
    (11, [(r, 6) for r in range(3, 7)]),
    (14, [(3, 9), (4, 9)]),
    (17, [(4, 2), (5, 2)]),
    (12, [(r, 5) for r in range(5, 9)]),
    (29, [(r, 4) for r in range(6, 10)]),
    (7,  [(6, 9), (7, 9)]),
    (12, [(7, 2), (8, 2)]),
    (7,  [(8, 6), (9, 6)]),
    (12, [(8, 7), (9, 7)]),
]

ALL_GROUPS = HORIZONTAL_GROUPS + VERTICAL_GROUPS
WHITE_CELLS = [
  (r + 1, c + 1)
  for r , row in enumerate(ROWS)
  for c, char in enumerate(row)
  if char == "."
]

def validate_puzzle_definition():
  while_set = set(WHITE_CELLS)
  for total, cells in ALL_GROUPS:
    if not cells:
      raise ValueError("Có nhóm không chứa ô trắng.")
    for cell in cells:
      if cell not in while_set:
        raise ValueError(f"Ô {cell} trong nhóm không phải ô trắng.")
    if total < len(cells) * (len(cells) + 1) // 2:
      raise ValueError(f"Tổng {total} quá nhỏ cho nhóm {cells}.")
    if total > sum(range(10 - len(cells), 10)):
      raise ValueError(f"Tổng {total} quá lớn cho nhóm {cells}.")

  counts = {cell: 0 for cell in WHITE_CELLS}
  for _, cells in ALL_GROUPS:
    for cell in cells:
      counts[cell] += 1

  missing = [cell for cell, count in counts.items() if count != 2]
  if missing:
    raise ValueError(
      "Mỗi ô trắng phải thuộc đúng một nhóm ngang và một nhóm dọc. "
      f"Các ô không hợp lệ: {missing}"
    )

  if len(WHITE_CELLS) != 48 or len(ALL_GROUPS) != 28:
    raise ValueError("Dữ liệu phải có 48 ô trắng và 28 nhóm.")
  return True