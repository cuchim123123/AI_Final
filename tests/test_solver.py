import unittest
from kakuro.board import WHITE_CELLS, ALL_GROUPS, validate_puzzle_definition
from kakuro.solver import KakuroSolver
from kakuro.validator import validate_solution
class KakuroTests(unittest.TestCase):
    def test_puzzle_definition(self):
        self.assertTrue(validate_puzzle_definition())
        self.assertEqual(len(WHITE_CELLS),48); self.assertEqual(len(ALL_GROUPS),28)

    def test_solver_returns_valid_solution(self):
        solution=KakuroSolver().solve(); valid,errors=validate_solution(solution)
        self.assertTrue(valid,'\n'.join(errors)); self.assertEqual(len(solution),48)

    def test_validator_rejects_invalid_solution(self):
        solution=KakuroSolver().solve(); bad=dict(solution); bad[WHITE_CELLS[0]]=0
        valid,errors=validate_solution(bad); self.assertFalse(valid); self.assertTrue(errors)
        
if __name__=='__main__': unittest.main()
