"""Hand-written instances: `tiny` to check results by hand, `demo` to show the algorithms at work."""
from itertools import count

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
            Room(AMPHI, capacity=100, name="Amphi"),
            Room(CLASSROOM, capacity=35, name="Salle 35 places"),
            Room(LAB, capacity=20, room_type="TP_INFO", name="Salle TP"),
        ),
        groups=(
            Group(PROMO, size=60, name="Promo"),
            Group(TD1, size=30, parent_id=PROMO, name="TD1"),
            Group(TD2, size=30, parent_id=PROMO, name="TD2"),
            Group(TP1A, size=15, parent_id=TD1, name="TP1a"),
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
        teacher_names={ALICE: "Alice", BOB: "Bob"},
    )


# demo(): one L3 promotion, 3 TD groups, 2 TP groups per TD
DEMO_PROMO = 1
DEMO_TD = {"A": 2, "B": 3, "C": 4}
DEMO_TP = {"A1": 5, "A2": 6, "B1": 7, "B2": 8, "C1": 9, "C2": 10}
MARTIN, DURAND, BERNARD, PETIT, ROBERT, MOREAU, LEROY = range(20, 27)

# subject: (CM teacher, CM minutes) or None, (TD teachers by TD group, minutes) or None,
#          (TP teacher, minutes) or None
DEMO_SUBJECTS = {
    "Algorithmique": ((MARTIN, 90), ({"A": MARTIN, "B": MARTIN, "C": DURAND}, 90), (DURAND, 90)),
    "Bases de données": ((BERNARD, 90), ({"A": BERNARD, "B": BERNARD, "C": BERNARD}, 90), (PETIT, 90)),
    "Réseaux": ((ROBERT, 60), None, (ROBERT, 90)),
    "Génie logiciel": ((MOREAU, 90), ({"A": MOREAU, "B": MOREAU, "C": MOREAU}, 60), None),
    "Anglais": (None, ({"A": LEROY, "B": LEROY, "C": LEROY}, 90), None),
}


def _demo_sessions() -> tuple[SessionRequest, ...]:
    ids, sessions = count(1), []
    for subject_id, (label, (cm, td, tp)) in enumerate(DEMO_SUBJECTS.items(), start=1):
        common = {"subject_id": subject_id, "label": label}
        if cm:
            sessions.append(SessionRequest(next(ids), cm[1], frozenset({cm[0]}), frozenset({DEMO_PROMO}), "CM", **common))
        if td:
            teachers, minutes = td
            for name, group in DEMO_TD.items():
                sessions.append(SessionRequest(next(ids), minutes, frozenset({teachers[name]}), frozenset({group}), "TD", **common))
        if tp:
            for group in DEMO_TP.values():
                sessions.append(SessionRequest(
                    next(ids), tp[1], frozenset({tp[0]}), frozenset({group}), "TP", room_type="TP_INFO", **common
                ))  # fmt: skip
    return tuple(sessions)


def demo() -> Problem:
    """A realistic week for one L3 promotion: 34 classes, 7 teachers, 6 rooms.

    Each student has about 15 h of classes; Martin is away on Monday, Petit on Wednesday, the
    second lab is closed on Friday afternoon. Leroy prefers afternoons, Bernard Tuesdays.
    """
    groups = [Group(DEMO_PROMO, size=90, name="L3 Info")]
    groups += [Group(gid, size=30, parent_id=DEMO_PROMO, name=f"TD {name}") for name, gid in DEMO_TD.items()]
    groups += [Group(gid, size=15, parent_id=DEMO_TD[name[0]], name=f"TP {name}") for name, gid in DEMO_TP.items()]
    return Problem(
        rooms=(
            Room(100, capacity=120, name="Amphi A"),
            Room(101, capacity=35, name="Salle 101"),
            Room(102, capacity=35, name="Salle 102"),
            Room(103, capacity=30, name="Salle 103"),
            Room(110, capacity=18, room_type="TP_INFO", name="Labo 1"),
            Room(111, capacity=18, room_type="TP_INFO", name="Labo 2"),
        ),
        groups=tuple(groups),
        sessions=_demo_sessions(),
        teacher_unavailabilities=(
            Unavailability(MARTIN, day=0, start_min=hm(8, 30), end_min=hm(18, 30)),
            Unavailability(PETIT, day=2, start_min=hm(8, 30), end_min=hm(18, 30)),
        ),
        room_unavailabilities=(Unavailability(111, day=4, start_min=hm(13, 30), end_min=hm(18, 30)),),
        preferences=(Preference(LEROY, half_day="AFTERNOON"), Preference(BERNARD, day=1)),
        teacher_names={
            MARTIN: "Martin", DURAND: "Durand", BERNARD: "Bernard", PETIT: "Petit",
            ROBERT: "Robert", MOREAU: "Moreau", LEROY: "Leroy",
        },  # fmt: skip
    )
