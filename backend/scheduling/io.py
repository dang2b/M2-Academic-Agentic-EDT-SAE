"""JSON storage of problem instances, so every algorithm runs on exactly the same data."""
import json
from dataclasses import asdict
from pathlib import Path

from scheduling.model import Group, Preference, Problem, Room, SessionRequest, TimeGrid, Unavailability

INSTANCES_DIR = Path(__file__).resolve().parent / "instances"


def problem_to_dict(problem: Problem) -> dict:
    return {
        "week": problem.week,
        "grid": asdict(problem.grid),
        "rooms": [asdict(r) for r in problem.rooms],
        "groups": [asdict(g) for g in problem.groups],
        "sessions": [
            asdict(s) | {"teacher_ids": sorted(s.teacher_ids), "group_ids": sorted(s.group_ids)}
            for s in problem.sessions
        ],
        "teacher_unavailabilities": [asdict(u) for u in problem.teacher_unavailabilities],
        "room_unavailabilities": [asdict(u) for u in problem.room_unavailabilities],
        "preferences": [asdict(p) for p in problem.preferences],
    }


def problem_from_dict(data: dict) -> Problem:
    grid = data["grid"]
    return Problem(
        week=data.get("week"),
        grid=TimeGrid(
            days=grid["days"],
            blocks=tuple(tuple(b) for b in grid["blocks"]),
            step_min=grid["step_min"],
            durations_min=tuple(grid["durations_min"]),
        ),
        rooms=tuple(Room(**r) for r in data["rooms"]),
        groups=tuple(Group(**g) for g in data["groups"]),
        sessions=tuple(
            SessionRequest(**s | {"teacher_ids": frozenset(s["teacher_ids"]), "group_ids": frozenset(s["group_ids"])})
            for s in data["sessions"]
        ),
        teacher_unavailabilities=tuple(Unavailability(**u) for u in data.get("teacher_unavailabilities", [])),
        room_unavailabilities=tuple(Unavailability(**u) for u in data.get("room_unavailabilities", [])),
        preferences=tuple(Preference(**p) for p in data.get("preferences", [])),
    )


def save_instance(problem: Problem, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(problem_to_dict(problem), indent=1) + "\n", encoding="utf-8")


def load_instance(path: Path) -> Problem:
    return problem_from_dict(json.loads(path.read_text(encoding="utf-8")))
