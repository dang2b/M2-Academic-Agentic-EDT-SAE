"""Who is busy when, shared by every algorithm that builds a solution step by step."""
from collections import defaultdict

from scheduling.model import Placement, Problem, Room, SessionRequest

Interval = tuple[int, int]


def eligible_rooms(problem: Problem, session: SessionRequest) -> list[Room]:
    """Rooms big enough and of the required type, smallest first (big rooms stay free for big classes)."""
    size = problem.session_size(session)
    rooms = [
        r for r in problem.rooms
        if r.capacity >= size and (session.room_type is None or r.room_type == session.room_type)
    ]  # fmt: skip
    return sorted(rooms, key=lambda r: (r.capacity, r.id))


def _overlaps(intervals: list[Interval], start: int, end: int) -> bool:
    return any(s < end and start < e for s, e in intervals)


class Occupancy:
    """Busy intervals per (teacher, day), (group, day) and (room, day), unavailabilities included."""

    def __init__(self, problem: Problem) -> None:
        self.problem = problem
        self._teachers: dict[tuple[int, int], list[Interval]] = defaultdict(list)
        self._groups: dict[tuple[int, int], list[Interval]] = defaultdict(list)
        self._rooms: dict[tuple[int, int], list[Interval]] = defaultdict(list)
        for u in problem.teacher_unavailabilities:
            self._teachers[(u.resource_id, u.day)].append((u.start_min, u.end_min))
        for u in problem.room_unavailabilities:
            self._rooms[(u.resource_id, u.day)].append((u.start_min, u.end_min))

    def people_free(self, session: SessionRequest, day: int, start: int, end: int) -> bool:
        """Teachers free, and no class for the session's groups, their ancestors or descendants."""
        if any(_overlaps(self._teachers[(t, day)], start, end) for t in session.teacher_ids):
            return False
        related = {r for g in session.group_ids for r in self.problem.related_groups[g]}
        return not any(_overlaps(self._groups[(g, day)], start, end) for g in related)

    def room_free(self, room_id: int, day: int, start: int, end: int) -> bool:
        return not _overlaps(self._rooms[(room_id, day)], start, end)

    def add(self, placement: Placement) -> None:
        session = self.problem.sessions_by_id[placement.session_id]
        interval = (placement.start_min, placement.end_min)
        for teacher in session.teacher_ids:
            self._teachers[(teacher, placement.day)].append(interval)
        for group in session.group_ids:
            self._groups[(group, placement.day)].append(interval)
        self._rooms[(placement.room_id, placement.day)].append(interval)
