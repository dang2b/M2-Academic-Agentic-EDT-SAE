from scheduling.evaluation import Weights, evaluate, leaf_timetables
from scheduling.examples import AMPHI, CLASSROOM, LAB, TD2, TP1A, tiny
from scheduling.model import Placement, Solution, hm

MON, TUE, FRI = 0, 1, 4


def solution(*placements: Placement) -> Solution:
    result = Solution()
    for p in placements:
        result.place(p)
    return result


def at(session_id: int, day: int, start: int, minutes: int, room: int) -> Placement:
    return Placement(session_id, day, start, start + minutes, room)


def test_feasible_solution():
    problem = tiny()
    result = evaluate(problem, solution(
        at(1, MON, hm(8, 30), 90, AMPHI),
        at(2, TUE, hm(8, 30), 90, CLASSROOM),
        at(3, TUE, hm(10), 60, CLASSROOM),
        at(4, TUE, hm(10), 90, LAB),  # same time as TD2: unrelated groups, other teacher and room
    ))
    assert result.feasible
    assert result.hard_violations == 0
    assert result.short_gaps == 0 and result.long_gap_minutes == 0
    assert result.preference_misses == 0
    # TP1A: Mon 90, Tue 180 (TD1 then TP), average 54 -> 36 + 126 + 3 * 54
    # TD2:  Mon 90, Tue 60, average 30 -> 60 + 30 + 3 * 30
    assert result.imbalance_minutes == 324 + 180


def test_each_hard_violation_is_counted():
    problem = tiny()
    result = evaluate(problem, solution(
        at(1, MON, hm(8, 30), 90, CLASSROOM),  # 60 students in 35 seats
        at(2, MON, hm(9), 90, CLASSROOM),  # Bob unavailable, overlaps the CM: related groups, same room
        at(3, MON, hm(11), 60, AMPHI),  # Bob unavailable
        at(4, FRI, hm(13, 30), 90, CLASSROOM),  # TP outside a TP room, Alice prefers mornings
    ))
    assert dict(result.hard) == {
        "invalid_placement": 0,
        "room_capacity": 1,
        "teacher_unavailable": 2,
        "group_overlap": 1,
        "room_overlap": 1,
        "room_type": 1,
    }
    assert not result.feasible
    assert result.long_gap_minutes == 60  # TD2: CM until 10:00, TD at 11:00
    assert result.gap_score == 3
    assert result.preference_misses == 1


def test_short_gap_costs_less_than_an_hour_but_not_nothing():
    problem = tiny()
    result = evaluate(problem, solution(
        at(1, MON, hm(13, 30), 90, AMPHI),
        at(3, MON, hm(15, 30), 60, CLASSROOM),  # TD2 waits 30 min
    ))
    assert result.short_gaps == 1 and result.long_gap_minutes == 0
    assert 0 < result.gap_score < Weights().gap_per_hour


def test_lunch_is_not_a_gap():
    problem = tiny()
    result = evaluate(problem, solution(
        at(1, TUE, hm(10, 30), 90, AMPHI),
        at(3, TUE, hm(13, 30), 60, CLASSROOM),
    ))
    assert result.short_gaps == 0 and result.long_gap_minutes == 0


def test_invalid_placements_are_rejected_not_scored():
    problem = tiny()
    result = evaluate(problem, solution(
        at(1, MON, hm(11), 90, AMPHI),  # would run over lunch
        at(2, TUE, hm(8, 30), 90, 999),  # unknown room
        at(3, TUE, hm(8, 45), 60, CLASSROOM),  # off the 30-minute grid
    ))
    assert result.hard["invalid_placement"] == 3
    assert result.unplaced == 1


def test_unplaced_sessions_are_counted_and_ranked_after_hard_violations():
    problem = tiny()
    empty = evaluate(problem, Solution())
    assert empty.unplaced == 4 and empty.hard_violations == 0
    assert not empty.feasible
    assert empty.rank() < (1, 0, 0.0)  # any hard violation ranks worse than unplaced sessions


def test_students_see_their_ancestors_classes():
    problem = tiny()
    placements = [at(1, MON, hm(8, 30), 90, AMPHI), at(2, TUE, hm(8, 30), 90, CLASSROOM)]
    timetables = leaf_timetables(problem, placements)
    assert set(timetables) == {TD2, TP1A}  # TD1 and the promotion have subgroups
    assert [p.session_id for p in timetables[TP1A]] == [1, 2]
    assert [p.session_id for p in timetables[TD2]] == [1]
