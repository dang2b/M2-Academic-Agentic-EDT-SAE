"""Small hand-written instances, small enough to check results by hand."""
from scheduling.model import Group, Preference, Problem, Room, SessionRequest, Unavailability, hm

PROMO, TD1, TD2, TP1A = 1, 2, 3, 4
ALICE, BOB = 10, 11  # teachers
AMPHI, CLASSROOM, LAB = 100, 101, 102


def tiny() -> Problem:
    """One promotion split in two TD groups, with a TP group under TD1.

    Conflicts: the CM clashes with everything (whole promotion), TD1 and TD2 share Bob,
    TD1 and its TP group are related. TD2 and the TP are independent.
    """
    return Problem(
        rooms=(
            Room(AMPHI, capacity=100),
            Room(CLASSROOM, capacity=35),
            Room(LAB, capacity=20, room_type="TP_INFO"),
        ),
        groups=(
            Group(PROMO, size=60),
            Group(TD1, size=30, parent_id=PROMO),
            Group(TD2, size=30, parent_id=PROMO),
            Group(TP1A, size=15, parent_id=TD1),
        ),
        sessions=(
            SessionRequest(1, 90, frozenset({ALICE}), frozenset({PROMO}), "CM"),
            SessionRequest(2, 90, frozenset({BOB}), frozenset({TD1}), "TD"),
            SessionRequest(3, 60, frozenset({BOB}), frozenset({TD2}), "TD"),
            SessionRequest(4, 90, frozenset({ALICE}), frozenset({TP1A}), "TP", room_type="TP_INFO"),
        ),
        teacher_unavailabilities=(Unavailability(BOB, day=0, start_min=hm(8, 30), end_min=hm(12)),),
        room_unavailabilities=(Unavailability(LAB, day=4, start_min=hm(13, 30), end_min=hm(18, 30)),),
        preferences=(Preference(ALICE, half_day="MORNING"),),
    )
