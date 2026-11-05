import pytest

from scheduling.examples import PROMO, TD1, TD2, TP1A, tiny
from scheduling.model import Group, Placement, Problem, Room, SessionRequest, Solution, TimeGrid, hm


def test_grid_starts_fit_inside_blocks():
    grid = TimeGrid()
    one_hour = grid.starts(60)
    ninety = grid.starts(90)
    # Morning 8:30-12:00 and afternoon 13:30-18:30, every 30 min, 5 days
    assert len(one_hour) == 5 * (6 + 9)
    assert len(ninety) == 5 * (5 + 8)
    assert (0, hm(8, 30)) in ninety and (0, hm(10, 30)) in ninety
    assert (0, hm(11)) not in ninety  # would end at 12:30, over lunch
    assert (0, hm(17)) in ninety and (0, hm(17, 30)) not in ninety


def test_half_day():
    grid = TimeGrid()
    assert grid.half_day(hm(11)) == "MORNING"
    assert grid.half_day(hm(13, 30)) == "AFTERNOON"


def test_related_groups_follow_the_hierarchy():
    problem = tiny()
    assert problem.related_groups[PROMO] == {PROMO, TD1, TD2, TP1A}
    assert problem.related_groups[TD1] == {TD1, PROMO, TP1A}
    assert problem.related_groups[TD2] == {TD2, PROMO}
    assert problem.related_groups[TP1A] == {TP1A, TD1, PROMO}


def test_conflict_graph():
    problem = tiny()
    assert problem.conflicts[1] == {2, 3, 4}  # the CM involves the whole promotion
    assert problem.conflicts[2] == {1, 3, 4}  # same teacher as 3, parent group of 4
    assert problem.conflicts[3] == {1, 2}
    assert problem.conflicts[4] == {1, 2}  # same teacher as the CM, child group of TD1


def test_session_size_sums_its_groups():
    problem = tiny()
    assert problem.session_size(problem.sessions_by_id[1]) == 60
    assert problem.session_size(problem.sessions_by_id[4]) == 15


def test_overlap_is_strict():
    first = Placement(1, day=0, start_min=hm(8, 30), end_min=hm(10), room_id=100)
    assert first.overlaps(Placement(2, 0, hm(9, 30), hm(11), 101))
    assert not first.overlaps(Placement(2, 0, hm(10), hm(11), 101))  # back to back
    assert not first.overlaps(Placement(2, 1, hm(8, 30), hm(10), 101))  # other day


def test_unplaced_lists_missing_sessions():
    problem = tiny()
    solution = Solution()
    solution.place(Placement(1, 0, hm(8, 30), hm(10), 100))
    assert solution.unplaced(problem) == [2, 3, 4]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"rooms": (Room(1, 10), Room(1, 20))}, "duplicate room"),
        ({"groups": (Group(1, 10, parent_id=99),)}, "unknown parent"),
        ({"groups": (Group(1, 10, parent_id=2), Group(2, 10, parent_id=1))}, "cycle"),
        ({"sessions": (SessionRequest(1, 45, frozenset({1}), frozenset({1})),)}, "duration"),
        ({"sessions": (SessionRequest(1, 60, frozenset(), frozenset({1})),)}, "at least one teacher"),
        ({"sessions": (SessionRequest(1, 60, frozenset({1}), frozenset({7})),)}, "unknown groups"),
    ],
)
def test_invalid_problems_are_rejected(kwargs, message):
    base = {"rooms": (Room(1, 10),), "groups": (Group(1, 10),), "sessions": ()}
    with pytest.raises(ValueError, match=message):
        Problem(**(base | kwargs))
