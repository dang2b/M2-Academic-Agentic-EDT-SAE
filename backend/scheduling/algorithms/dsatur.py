"""DSatur V1: graph colouring where the most saturated session is placed next.

Classic DSatur (Brélaz, 1979) colours the vertex whose neighbours already use the most colours.
Here classes have different lengths and may partly overlap, so saturation is measured directly:
the session with the FEWEST feasible placements left (start + free room) goes next, recomputed
after every placement. Ties: most conflicts with sessions still to place, then longest, then id.
It then takes the first feasible start in chronological order, like greedy V1, so the only
difference with greedy V1 is the dynamic order. A session with no feasible placement left is
left unplaced.

Complexity: n steps, each recounting the options of the remaining sessions (up to n x S starts
x (R + n) checks), so O(n^2 * S * (R + n)) in the worst case: about n times greedy V1.
"""
import random

from scheduling.algorithms.base import Algorithm
from scheduling.model import Problem, SessionRequest, Solution
from scheduling.occupancy import Occupancy, feasible_placements


def _priority(problem: Problem, session: SessionRequest, options: int, remaining: set[int]) -> tuple:
    uncoloured_neighbours = len(problem.conflicts[session.id] & remaining)
    return (options, -uncoloured_neighbours, -session.duration_min, session.id)


def solve(problem: Problem, rng: random.Random | None = None, time_limit_s: float | None = None) -> Solution:
    solution, occupancy = Solution(), Occupancy(problem)
    remaining = {s.id for s in problem.sessions}
    while remaining:
        options = {sid: list(feasible_placements(problem, occupancy, problem.sessions_by_id[sid])) for sid in remaining}
        chosen = min(remaining, key=lambda sid: _priority(problem, problem.sessions_by_id[sid], len(options[sid]), remaining))
        remaining.discard(chosen)
        if options[chosen]:  # no option left: unplaced
            solution.place(options[chosen][0])
            occupancy.add(options[chosen][0])
    return solution


ALGORITHM = Algorithm(
    name="dsatur",
    version=1,
    solve=solve,
    deterministic=True,
    description="fewest feasible placements first (recomputed after each step), earliest free time",
)
