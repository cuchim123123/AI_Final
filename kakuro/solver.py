from copy import deepcopy
from kakuro.csp import KakuroCSP
from kakuro.heuristics import KakuroHeuristics
from kakuro.propagation import KakuroPropagation

class KakuroSolver:
  def __init__(self, event_callback=None):
    self.csp = KakuroCSP()
    self.event_callback = event_callback
    self.propagation = KakuroPropagation(self.csp, self._emit)
    self.nodes = 0
    self.backtracks = 0
    self.assignment = {}
    self.domains = deepcopy(self.csp.domains)

  def _emit(self, event, details):
    if self.event_callback:
      self.event_callback(event, details, self)

  def select_unassigned_variable(self, domains, assignment):
    return KakuroHeuristics.select_unassigned_variable(self.csp, domains, assignment, lambda e, d: self._emit(e, d))

  def order_domain_values(self, cell, domains, assignment):
    return KakuroHeuristics.order_domain_values(self.csp, cell, domains, assignment)

  def _search(self, domains, assignment):
    self.domains = domains
    self.assignment = assignment
    if len(assignment) == len(self.csp.variables):
      return assignment
    cell = self.select_unassigned_variable(domains, assignment)
    for value in self.order_domain_values(cell, domains, assignment):
      self.nodes += 1
      self._emit('try', {'cell': cell, 'value': value})
      state = self.propagation.forward_checking(cell, value, domains, assignment)
      if state is not None:
        result = self._search(*state)
        if result is not None:
          return result

      self.backtracks += 1
      self._emit('backtrack', {'cell': cell, 'value': value})
    return None

  def solve(self):
    domains = deepcopy(self.csp.domains)
    assignment = {}
    self._emit('start', {})
    if not self.propagation.propagate(domains, assignment):
      self._emit('unsolved', {})
      return None
    result = self._search(domains, assignment)
    if result is None:
      self._emit('unsolved', {})
      return None
    self.assignment = result
    self.domains = domains
    self._emit('solved', {'nodes': self.nodes, 'backtracks': self.backtracks, 'propagation_steps': self.propagation.steps})
    return result


