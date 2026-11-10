"""Per-solve time limit of the SAT solver."""
from nqueens.factory import build_sat


def test_time_limit_interrupts_search():
    # Sequential encoding at N=60 takes far longer than 0.05 s.
    r = build_sat("sequential", time_limit_s=0.05).solve(60)
    assert r.extra["timed_out"] and not r.solved
    assert r.time_s < 5


def test_time_limit_not_hit_on_easy_instance():
    r = build_sat("pairwise", time_limit_s=30).solve(8)
    assert r.solved and not r.extra["timed_out"]
