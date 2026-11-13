from scheduling.algorithms import ALGORITHMS
from scheduling.algorithms import greedy
from scheduling.algorithms.dsatur import solve
from scheduling.evaluation import evaluate
from scheduling.examples import tiny
from scheduling.model import Group, Placement, Problem, Room, SessionRequest, Unavailability, hm

FREE, BUSY = 1, 2  # teachers


def one_slot_problem() -> Problem:
    """S1 fits anywhere; S2's teacher is only available on Monday 8:30-10:00. Same group: they clash.

    Greedy's static order (rooms, conflicts, duration, id) cannot see the unavailability and
    places S1 first, on Monday 8:30, the only slot S2 had.
    """
    day = (hm(8, 30), hm(18, 30))
    away = [Unavailability(BUSY, 0, hm(10), hm(18, 30))] + [Unavailability(BUSY, d, *day) for d in range(1, 5)]
    return Problem(
        rooms=(Room(1, capacity=30),),
        groups=(Group(1, size=30),),
        sessions=(
            SessionRequest(1, 90, frozenset({FREE}), frozenset({1})),
            SessionRequest(2, 90, frozenset({BUSY}), frozenset({1})),
        ),
        teacher_unavailabilities=tuple(away),
    )


def test_greedy_loses_the_session_with_a_single_slot():
    problem = one_slot_problem()
    assert evaluate(problem, greedy.solve(problem)).unplaced == 1


def test_dsatur_places_the_most_constrained_session_first():
    problem = one_slot_problem()
    solution = solve(problem)
    assert solution.placements[2] == Placement(2, 0, hm(8, 30), hm(10), 1)
    assert solution.placements[1] == Placement(1, 0, hm(10), hm(11, 30), 1)
    assert evaluate(problem, solution).feasible


def test_dsatur_is_valid_on_tiny_and_registered():
    problem = tiny()
    assert evaluate(problem, solve(problem)).feasible
    assert ALGORITHMS["dsatur@1"].deterministic
