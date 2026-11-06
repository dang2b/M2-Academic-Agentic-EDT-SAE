"""Greedy V1: most constrained session first, earliest free time, smallest fitting room.

Order: fewest eligible rooms, then most conflicts, then longest duration (id breaks ties, so the
result is deterministic). Each session takes the first start, in chronological order, where its
teachers and groups are free and a room is free; it is never moved afterwards. A session with no
such start is left unplaced.

Complexity: O(n log n) for the sort, then for each of the n sessions up to S starts x R rooms,
each check scanning the intervals already booked that day, so O(n * S * (R + n)) in the worst case.
"""
import random

from scheduling.algorithms.base import Algorithm
from scheduling.model import Placement, Problem, SessionRequest, Solution
from scheduling.occupancy import Occupancy, eligible_rooms


def placement_order(problem: Problem) -> list[SessionRequest]:
    rooms = {s.id: len(eligible_rooms(problem, s)) for s in problem.sessions}
    return sorted(
        problem.sessions,
        key=lambda s: (rooms[s.id], -len(problem.conflicts[s.id]), -s.duration_min, s.id),
    )


def first_fit(problem: Problem, occupancy: Occupancy, session: SessionRequest) -> Placement | None:
    rooms = eligible_rooms(problem, session)
    for day, start in problem.grid.starts(session.duration_min):
        end = start + session.duration_min
        if not occupancy.people_free(session, day, start, end):
            continue
        for room in rooms:
            if occupancy.room_free(room.id, day, start, end):
                return Placement(session.id, day, start, end, room.id)
    return None


def solve(problem: Problem, rng: random.Random | None = None, time_limit_s: float | None = None) -> Solution:
    solution, occupancy = Solution(), Occupancy(problem)
    for session in placement_order(problem):
        placement = first_fit(problem, occupancy, session)
        if placement is not None:
            solution.place(placement)
            occupancy.add(placement)
    return solution


ALGORITHM = Algorithm(
    name="greedy",
    version=1,
    solve=solve,
    deterministic=True,
    description="most constrained first, earliest free time, smallest fitting room, no backtracking",
)
