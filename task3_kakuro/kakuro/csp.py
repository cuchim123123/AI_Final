from kakuro.board import WHITE_CELLS, ALL_GROUPS, validate_puzzle_definition

class KakuroCSP:
  def __init__(self):
    validate_puzzle_definition()
    self.variables = list(WHITE_CELLS)
    self.groups = list(ALL_GROUPS)
    self.domains = {cell: set(range(1, 10)) for cell in self.variables}
    self.groups_by_cell = {cell: [] for cell in self.variables}
    for i, (_, cells) in enumerate(self.groups):
      for cell in cells:
        self.groups_by_cell[cell].append(i)

  @staticmethod
  def sum_bounds(count, used):
    available = [n for n in range(1, 10) if n not in used]
    if len(available) < count:
      return None
    return sum(available[:count]), sum(available[-count:])

  def group_supports(self, target, cells, domains, assignment):
    supports = [set() for _ in cells]
    values = [None] * len(cells)
    found = False
    def visit(i, total, used):
      nonlocal found
      if i == len(cells):
        if total == target:
          found = True
          for j, value in enumerate(values): supports[j].add(value)
        return
      cell = cells[i]
      candidates = [assignment[cell]] if cell in assignment else sorted(domains[cell])
      remaining = len(cells)-i-1
      for value in candidates:
        if value in used: continue
        new_total = total + value

        if new_total >= target and remaining > 0: continue
        bounds = self.sum_bounds(remaining, used | {value})
        if bounds is None: continue
        if new_total + bounds[0] > target or new_total + bounds[1] < target:
          continue

        values[i] = value
        visit(i+1, new_total, used | {value})

    visit(0, 0, set())
    return supports, found

        