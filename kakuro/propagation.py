from copy import deepcopy

class KakuroPropagation:
  def __init__(self, csp, emit = None):
    self.csp = csp
    self.emit_callback = emit
    self.steps = 0

  def emit(self, event, details):
    if self.emit_callback:
      self.emit_callback(event, details)

  def propagate(self, domains, assignment):
    changed = True
    while changed:
      changed = False
      for gi, (target, cells) in enumerate(self.csp.groups):
        supports, found = self.csp.group_supports(target, cells, domains, assignment)
        if not found:
          self.emit('contradiction', {'group': gi, 'target': target})
          return False
        for i, cell in enumerate(cells):
          if cell in assignment:
            if assignment[cell] not in supports[i]:
              return False
            continue
          new_domain = domains[cell] & supports[i]
          if not new_domain:
            self.emit('contradiction', {'cell': cell, 'group': gi})
            return False
          if new_domain != domains[cell]:
            removed = sorted(domains[cell]-new_domain)
            domains[cell] = new_domain
            self.steps += 1
            changed = True
            self.emit('domain', {'cell': cell, 'domain': sorted(new_domain), 'removed': removed, 'group': gi})
    return True

  def forward_checking(self, cell, value, domains, assignment):
    new_domains = deepcopy(domains)
    new_assignment = dict(assignment)
    new_domains[cell] = {value}
    new_assignment[cell] = value
    if not self.propagate(new_domains, new_assignment):
      return None
    return new_domains, new_assignment

