"""In-memory model of a one-week timetabling problem, shared by every algorithm.

Times are minutes since midnight, days are 0 (Monday) to 4 (Friday). A semester is solved
week by week, one `Problem` per week.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Literal

HalfDay = Literal["MORNING", "AFTERNOON"]


def hm(hours: int, minutes: int = 0) -> int:
    return hours * 60 + minutes


@dataclass(frozen=True, slots=True)
class TimeGrid:
    """Teaching blocks of a day; a session must fit entirely inside one block (no class over lunch)."""

    days: int = 5
    blocks: tuple[tuple[int, int], ...] = ((hm(8, 30), hm(12)), (hm(13, 30), hm(18, 30)))
    step_min: int = 30
    durations_min: tuple[int, ...] = (60, 90)

    def starts(self, duration_min: int) -> list[tuple[int, int]]:
        """Every (day, start_min) where a session of this duration fits, in chronological order."""
        return [
            (day, start)
            for day in range(self.days)
            for block_start, block_end in self.blocks
            for start in range(block_start, block_end - duration_min + 1, self.step_min)
        ]

    def fits(self, day: int, start_min: int, duration_min: int) -> bool:
        return 0 <= day < self.days and any(
            block_start <= start_min
            and start_min + duration_min <= block_end
            and (start_min - block_start) % self.step_min == 0
            for block_start, block_end in self.blocks
        )

    def half_day(self, start_min: int) -> HalfDay:
        return "MORNING" if start_min < self.blocks[-1][0] else "AFTERNOON"


@dataclass(frozen=True, slots=True)
class Room:
    id: int
    capacity: int
    room_type: str | None = None  # e.g. "TP_INFO"; None for an ordinary room
    name: str | None = None  # display only


@dataclass(frozen=True, slots=True)
class Group:
    id: int
    size: int
    parent_id: int | None = None  # a TD group belongs to its promotion, a TP group to its TD group
    name: str | None = None  # display only


@dataclass(frozen=True, slots=True)
class SessionRequest:
    """One class to place this week."""

    id: int
    duration_min: int
    teacher_ids: frozenset[int]
    group_ids: frozenset[int]
    session_type: str = "CM"
    subject_id: int | None = None
    room_type: str | None = None  # required room type, None if any room fits
    label: str | None = None  # subject name, display only


@dataclass(frozen=True, slots=True)
class Unavailability:
    resource_id: int  # teacher id or room id, depending on the list it is in
    day: int
    start_min: int
    end_min: int


@dataclass(frozen=True, slots=True)
class Preference:
    """A teacher would rather teach on this day and/or half-day; `weight` ranks preferences."""

    teacher_id: int
    day: int | None = None
    half_day: HalfDay | None = None
    weight: int = 1


@dataclass(frozen=True, slots=True)
class Placement:
    session_id: int
    day: int
    start_min: int
    end_min: int
    room_id: int

    def overlaps(self, other: "Placement") -> bool:
        return self.day == other.day and self.start_min < other.end_min and other.start_min < self.end_min


@dataclass
class Solution:
    """What every algorithm returns: sessions it could not place are simply left out."""

    placements: dict[int, Placement] = field(default_factory=dict)

    def place(self, placement: Placement) -> None:
        self.placements[placement.session_id] = placement

    def unplaced(self, problem: "Problem") -> list[int]:
        return [s.id for s in problem.sessions if s.id not in self.placements]


@dataclass
class Problem:
    rooms: tuple[Room, ...]
    groups: tuple[Group, ...]
    sessions: tuple[SessionRequest, ...]
    teacher_unavailabilities: tuple[Unavailability, ...] = ()
    room_unavailabilities: tuple[Unavailability, ...] = ()
    preferences: tuple[Preference, ...] = ()
    grid: TimeGrid = field(default_factory=TimeGrid)
    week: int | None = None  # week number in the semester, for reports only
    teacher_names: dict[int, str] = field(default_factory=dict)  # display only

    # Derived lookups, computed once in __post_init__
    rooms_by_id: dict[int, Room] = field(init=False, repr=False)
    groups_by_id: dict[int, Group] = field(init=False, repr=False)
    sessions_by_id: dict[int, SessionRequest] = field(init=False, repr=False)
    related_groups: dict[int, frozenset[int]] = field(init=False, repr=False)
    conflicts: dict[int, frozenset[int]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.rooms_by_id = _index(self.rooms, "room")
        self.groups_by_id = _index(self.groups, "group")
        self.sessions_by_id = _index(self.sessions, "session")
        self._check_references()
        self.related_groups = self._related_groups()
        self.conflicts = self._conflicts()

    def session_size(self, session: SessionRequest) -> int:
        return sum(self.groups_by_id[g].size for g in session.group_ids)

    def _check_references(self) -> None:
        self._check_groups()
        for session in self.sessions:
            self._check_session(session)
        for unavailability in self.room_unavailabilities:
            if unavailability.resource_id not in self.rooms_by_id:
                raise ValueError(f"room unavailability: unknown room {unavailability.resource_id}")

    def _check_groups(self) -> None:
        for group in self.groups:
            if group.parent_id is not None and group.parent_id not in self.groups_by_id:
                raise ValueError(f"group {group.id}: unknown parent {group.parent_id}")

    def _check_session(self, session: SessionRequest) -> None:
        if session.duration_min not in self.grid.durations_min:
            raise ValueError(f"session {session.id}: duration {session.duration_min} min not allowed")
        if not session.teacher_ids or not session.group_ids:
            raise ValueError(f"session {session.id}: needs at least one teacher and one group")
        unknown = session.group_ids - self.groups_by_id.keys()
        if unknown:
            raise ValueError(f"session {session.id}: unknown groups {sorted(unknown)}")

    def _ancestors(self, group_id: int) -> list[int]:
        chain, seen = [], {group_id}
        parent = self.groups_by_id[group_id].parent_id
        while parent is not None:
            if parent in seen:
                raise ValueError(f"group {group_id}: cycle in the group hierarchy")
            seen.add(parent)
            chain.append(parent)
            parent = self.groups_by_id[parent].parent_id
        return chain

    def _related_groups(self) -> dict[int, frozenset[int]]:
        """Groups that cannot have two classes at once: the group, its ancestors and its descendants."""
        related: dict[int, set[int]] = {g.id: {g.id} for g in self.groups}
        for group in self.groups:
            for ancestor in self._ancestors(group.id):
                related[group.id].add(ancestor)
                related[ancestor].add(group.id)
        return {g: frozenset(r) for g, r in related.items()}

    def _conflicts(self) -> dict[int, frozenset[int]]:
        """Sessions that may never overlap, because they share a teacher or related groups.

        This is the conflict graph used by the graph-colouring algorithm. Rooms are not edges:
        two sessions can share a room as long as they are at different times.
        """
        edges: dict[int, set[int]] = {s.id: set() for s in self.sessions}
        self._add_teacher_edges(edges)
        self._add_group_edges(edges)
        for session_id, neighbours in edges.items():
            neighbours.discard(session_id)
        return {s: frozenset(e) for s, e in edges.items()}

    def _add_teacher_edges(self, edges: dict[int, set[int]]) -> None:
        by_teacher: dict[int, list[int]] = defaultdict(list)
        for session in self.sessions:
            for teacher in session.teacher_ids:
                by_teacher[teacher].append(session.id)
        for bucket in by_teacher.values():
            for a, b in combinations(bucket, 2):
                edges[a].add(b)
                edges[b].add(a)

    def _add_group_edges(self, edges: dict[int, set[int]]) -> None:
        # Not a single bucket per promotion: TD2 and a TP group of TD1 are both related to the
        # promotion but not to each other, so only each session's own related groups count.
        by_group: dict[int, list[int]] = defaultdict(list)
        for session in self.sessions:
            for group in session.group_ids:
                by_group[group].append(session.id)
        for session in self.sessions:
            for group in session.group_ids:
                for related in self.related_groups[group]:
                    edges[session.id].update(by_group.get(related, ()))


def _index(items, kind: str) -> dict:
    index = {}
    for item in items:
        if item.id in index:
            raise ValueError(f"duplicate {kind} id {item.id}")
        index[item.id] = item
    return index
