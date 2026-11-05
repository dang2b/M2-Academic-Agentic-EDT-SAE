"""Baseline: every session at a random time in a random room, ignoring all constraints.

Not a real algorithm: it shows what "no algorithm" scores, so the others have a floor to beat.
"""
import random

from scheduling.algorithms.base import Algorithm
from scheduling.model import Placement, Problem, Solution


def solve(problem: Problem, rng: random.Random, time_limit_s: float | None = None) -> Solution:
    solution = Solution()
    for session in problem.sessions:
        day, start = rng.choice(problem.grid.starts(session.duration_min))
        room = rng.choice(problem.rooms)
        solution.place(Placement(session.id, day, start, start + session.duration_min, room.id))
    return solution


ALGORITHM = Algorithm(
    name="random",
    version=1,
    solve=solve,
    deterministic=False,
    description="random time and room for each session, constraints ignored",
)
