class KakuroHeuristics:
  @staticmethod
  def select_unassigned_variable(csp, domains, assignment, emit=None):
    unassigned = [v for v in csp.variables if v not in assignment]
    if not unassigned: return None
    def key(cell):
      degree = sum (1 for gi in csp.groups_by_cell[cell]
                    for other in csp.groups[gi][1]
                    if other not in assignment and other != cell)
      return (len(domains[cell]), -degree, cell)

    chosen = min(unassigned, key=key)
    if emit: emit('select', {'cell':chosen, 'domain': sorted(domains[chosen])})
    return chosen

  @staticmethod
  def order_domain_values(csp, cell, domains, assignment):
    neighbors = set()
    for gi in csp.groups_by_cell[cell]: neighbors.update(csp.groups[gi][1])
    neighbors.discard(cell)
    neighbors=[n for n in neighbors if n not in assignment]
    #Estimate LCV impact by counting neighboring domains that contain this value
    scored=[]
    for value in sorted(domains[cell]):
      impact = sum(1 for n in neighbors if value in domains[n])
      scored.append((impact, value))
    return [v for _, v in sorted(scored)]