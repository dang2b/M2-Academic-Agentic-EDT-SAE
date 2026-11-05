"""The single judge of every algorithm: hard constraint violations, unplaced sessions, soft score.

Solutions are ranked by (hard violations, unplaced sessions, soft score), lower is better.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from scheduling.model import Placement, Problem, Solution, Unavailability

HARD_CONSTRAINTS = (
    "invalid_placement",  # unknown session or room, or time outside the grid
    "teacher_overlap",
    "group_overlap",  # same group, or a group and one of its ancestors/descendants
    "room_overlap",
    "room_capacity",
    "room_type",
    "teacher_unavailable",
    "room_unavailable",
)


@dataclass(frozen=True)
class Weights:
    short_gap: float = 1.0  # a gap shorter than an hour, whatever its length
    gap_per_hour: float = 3.0  # a gap of an hour or more
    preference: float = 1.0  # per session placed outside all of its teacher's preferences
    imbalance_per_hour: float = 1.0  # per hour away from the group's daily average


@dataclass
class Evaluation:
    hard: Counter = field(default_factory=Counter)
    unplaced: int = 0
    short_gaps: int = 0
    long_gap_minutes: int = 0
    preference_misses: int = 0
    imbalance_minutes: float = 0.0
    weights: Weights = field(default_factory=Weights)

    @property
    def hard_violations(self) -> int:
        return sum(self.hard.values())

    @property
    def feasible(self) -> bool:
        return self.hard_violations == 0 and self.unplaced == 0

    @property
    def gap_score(self) -> float:
        return self.short_gaps * self.weights.short_gap + self.long_gap_minutes / 60 * self.weights.gap_per_hour

    @property
    def soft_score(self) -> float:
        return (
            self.gap_score
            + self.preference_misses * self.weights.preference
            + self.imbalance_minutes / 60 * self.weights.imbalance_per_hour
        )

    def rank(self) -> tuple[int, int, float]:
        return (self.hard_violations, self.unplaced, self.soft_score)


def evaluate(problem: Problem, solution: Solution, weights: Weights = Weights()) -> Evaluation:
    result = Evaluation(weights=weights, unplaced=len(solution.unplaced(problem)))
    placements = [p for p in solution.placements.values() if _valid(problem, p)]
    result.hard["invalid_placement"] = len(solution.placements) - len(placements)
    _check_overlaps(problem, placements, result.hard)
    _check_rooms(problem, placements, result.hard)
    _check_unavailabilities(problem, placements, result.hard)
    _score_gaps_and_balance(problem, placements, result)
    result.preference_misses = _preference_misses(problem, placements)
    return result


def _valid(problem: Problem, p: Placement) -> bool:
    session = problem.sessions_by_id.get(p.session_id)
    return (
        session is not None
        and p.room_id in problem.rooms_by_id
        and p.end_min - p.start_min == session.duration_min
        and problem.grid.fits(p.day, p.start_min, session.duration_min)
    )


def _check_overlaps(problem: Problem, placements: list[Placement], hard: Counter) -> None:
    by_day: dict[int, list[Placement]] = defaultdict(list)
    for p in placements:
        by_day[p.day].append(p)
    for day_placements in by_day.values():
        for i, a in enumerate(day_placements):
            for b in day_placements[i + 1 :]:
                if a.overlaps(b):
                    _count_overlap(problem, a, b, hard)


def _count_overlap(problem: Problem, a: Placement, b: Placement, hard: Counter) -> None:
    sa, sb = problem.sessions_by_id[a.session_id], problem.sessions_by_id[b.session_id]
    if sa.teacher_ids & sb.teacher_ids:
        hard["teacher_overlap"] += 1
    if any(problem.related_groups[g] & sb.group_ids for g in sa.group_ids):
        hard["group_overlap"] += 1
    if a.room_id == b.room_id:
        hard["room_overlap"] += 1


def _check_rooms(problem: Problem, placements: list[Placement], hard: Counter) -> None:
    for p in placements:
        session, room = problem.sessions_by_id[p.session_id], problem.rooms_by_id[p.room_id]
        if room.capacity < problem.session_size(session):
            hard["room_capacity"] += 1
        if session.room_type is not None and room.room_type != session.room_type:
            hard["room_type"] += 1


def _hits(p: Placement, u: Unavailability) -> bool:
    return p.day == u.day and p.start_min < u.end_min and u.start_min < p.end_min


def _check_unavailabilities(problem: Problem, placements: list[Placement], hard: Counter) -> None:
    for p in placements:
        session = problem.sessions_by_id[p.session_id]
        if any(u.resource_id in session.teacher_ids and _hits(p, u) for u in problem.teacher_unavailabilities):
            hard["teacher_unavailable"] += 1
        if any(u.resource_id == p.room_id and _hits(p, u) for u in problem.room_unavailabilities):
            hard["room_unavailable"] += 1


def leaf_timetables(problem: Problem, placements: list[Placement]) -> dict[int, list[Placement]]:
    """What a student of each finest group attends: its own classes and its ancestors' classes.

    A finest group has no descendants, so its related groups are exactly itself and its ancestors.
    """
    parents = {g.parent_id for g in problem.groups}
    return {
        g.id: [p for p in placements if problem.sessions_by_id[p.session_id].group_ids & problem.related_groups[g.id]]
        for g in problem.groups
        if g.id not in parents
    }


def _score_gaps_and_balance(problem: Problem, placements: list[Placement], result: Evaluation) -> None:
    for timetable in leaf_timetables(problem, placements).values():
        minutes_per_day = [0] * problem.grid.days
        for day in range(problem.grid.days):
            day_classes = sorted((p for p in timetable if p.day == day), key=lambda p: p.start_min)
            minutes_per_day[day] = sum(p.end_min - p.start_min for p in day_classes)
            for gap in _gaps(problem, day_classes):
                if gap < 60:
                    result.short_gaps += 1
                else:
                    result.long_gap_minutes += gap
        average = sum(minutes_per_day) / problem.grid.days
        result.imbalance_minutes += sum(abs(m - average) for m in minutes_per_day)


def _gaps(problem: Problem, day_classes: list[Placement]) -> list[int]:
    """Free time between consecutive classes of the same half-day; lunch is not a gap."""
    return [
        b.start_min - a.end_min
        for a, b in zip(day_classes, day_classes[1:])
        if b.start_min > a.end_min and problem.grid.half_day(a.start_min) == problem.grid.half_day(b.start_min)
    ]


def _preference_misses(problem: Problem, placements: list[Placement]) -> int:
    by_teacher = defaultdict(list)
    for preference in problem.preferences:
        by_teacher[preference.teacher_id].append(preference)
    misses = 0
    for p in placements:
        half_day = problem.grid.half_day(p.start_min)
        for teacher in problem.sessions_by_id[p.session_id].teacher_ids:
            preferences = by_teacher.get(teacher)
            if preferences and not any(
                (pref.day is None or pref.day == p.day) and (pref.half_day is None or pref.half_day == half_day)
                for pref in preferences
            ):
                misses += 1
    return misses
