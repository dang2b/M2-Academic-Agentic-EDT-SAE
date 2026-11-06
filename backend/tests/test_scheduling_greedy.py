import random

from scheduling.algorithms import ALGORITHMS
from scheduling.algorithms.greedy import placement_order, solve
from scheduling.evaluation import evaluate
from scheduling.examples import AMPHI, CLASSROOM, LAB, tiny
from scheduling.model import Group, Placement, Problem, Room, SessionRequest, hm
from scheduling.occupancy import Occupancy, eligible_rooms

MON = 0


def test_eligible_rooms_smallest_first_and_of_the_right_type():
    problem = tiny()
    assert [r.id for r in eligible_rooms(problem, problem.sessions_by_id[2])] == [CLASSROOM, AMPHI]
    assert [r.id for r in eligible_rooms(problem, problem.sessions_by_id[4])] == [LAB]  # TP room only


def test_occupancy_blocks_related_groups_and_unavailabilities():
    problem = tiny()
    occupancy = Occupancy(problem)
    occupancy.add(Placement(1, MON, hm(8, 30), hm(10), AMPHI))  # CM of the whole promotion
    td1, td2, tp = (problem.sessions_by_id[i] for i in (2, 3, 4))
    assert not occupancy.people_free(tp, MON, hm(9), hm(10, 30))  # TP1A students are in the CM
    assert occupancy.people_free(tp, MON, hm(10), hm(11, 30))
    assert not occupancy.people_free(td2, MON, hm(10), hm(11))  # Bob unavailable on Monday morning
    assert not occupancy.room_free(AMPHI, MON, hm(9), hm(10))
    assert not occupancy.room_free(LAB, 4, hm(14), hm(15))  # lab closed on Friday afternoon
    assert occupancy.people_free(td1, 1, hm(8, 30), hm(10))


def test_most_constrained_sessions_go_first():
    # CM and TP have a single possible room; the CM has more conflicts
    assert [s.id for s in placement_order(tiny())] == [1, 4, 2, 3]


def test_greedy_on_tiny_matches_the_hand_computed_timetable():
    problem = tiny()
    solution = solve(problem)
    assert solution.placements == {
        1: Placement(1, MON, hm(8, 30), hm(10), AMPHI),
        4: Placement(4, MON, hm(10), hm(11, 30), LAB),  # after the CM, Alice and TP1A both free
        2: Placement(2, MON, hm(13, 30), hm(15), CLASSROOM),  # Bob unavailable in the morning
        3: Placement(3, MON, hm(15), hm(16), CLASSROOM),  # right after TD1, Bob's other class
    }
    result = evaluate(problem, solution)
    assert result.feasible
    assert result.gap_score == 0
    assert result.imbalance_minutes > 0  # everything on Monday: the known weakness of first fit


def test_session_without_a_big_enough_room_is_left_unplaced():
    problem = Problem(
        rooms=(Room(1, capacity=20),),
        groups=(Group(1, size=50),),
        sessions=(SessionRequest(1, 60, frozenset({1}), frozenset({1})),),
    )
    result = evaluate(problem, solve(problem))
    assert result.unplaced == 1 and result.hard_violations == 0


def test_greedy_is_registered_as_deterministic():
    algorithm = ALGORITHMS["greedy@1"]
    assert algorithm.deterministic
    problem = tiny()
    assert algorithm.solve(problem, random.Random(1), None).placements == solve(problem).placements
