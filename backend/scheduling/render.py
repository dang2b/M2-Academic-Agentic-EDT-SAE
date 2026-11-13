"""Static HTML view of solutions: one weekly grid per student group, algorithms side by side.

Usage, from backend/:
    python -m scheduling.render -i demo                      # every algorithm, seed 0, first 2 groups
    python -m scheduling.render -i demo -a greedy@1 random@1 --seed 3 -g "TP A1" "TP C2"

Algorithms are shown side by side (in the order given), one row per student group. Classes that
overlap in a group's timetable are outlined in red and shifted so that none is hidden.
"""
import argparse
import random
from html import escape
from pathlib import Path

from scheduling.algorithms import ALGORITHMS
from scheduling.evaluation import evaluate, leaf_timetables
from scheduling.io import INSTANCES_DIR, load_instance
from scheduling.model import Placement, Problem, Solution

RESULTS_DIR = Path(__file__).resolve().parent / "results"
WEEK_WIDTH_PX = 44 + 5 * 120 + 2  # time column, 5 day columns, borders (see .week)
DAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi")
COLORS = {"CM": "#cfe0fc", "TD": "#d3f2d6", "TP": "#fde2c4", "EXAM": "#f8cfd0"}

CSS = """
body { font-family: system-ui, sans-serif; margin: 24px; color: #1d1d1f; background: #fff; }
.compare { display: grid; gap: 24px; align-items: start; }
h2 { font-size: 18px; margin: 0; }
.summary { font-size: 13px; margin: 4px 0 0; }
.ok { color: #1a7f37; } .ko { color: #c62828; }
h3 { font-size: 14px; margin: 24px 0 6px; }
.week { display: grid; grid-template-columns: 44px repeat(5, 120px); grid-auto-rows: 22px; font-size: 11px;
        border: 1px solid #ccc; }
.head { text-align: center; font-weight: 600; padding: 3px; border-bottom: 1px solid #ccc; }
.time { color: #777; padding-right: 4px; text-align: right; border-top: 1px dotted #e5e5e5; }
.cell { border-top: 1px dotted #e5e5e5; border-left: 1px solid #eee; }
.lunch { background: #f4f4f4; }
.class { margin: 1px 2px; padding: 2px 4px; border-radius: 4px; border: 1px solid #999;
         overflow: hidden; line-height: 1.2; }
.conflict { border: 2px solid #c62828; }
"""


def _row(problem: Problem, minute: int) -> int:
    """Grid row of a time (row 1 is the header), one row per step from the first block's start."""
    return 2 + (minute - problem.grid.blocks[0][0]) // problem.grid.step_min


def _background(problem: Problem) -> list[str]:
    grid, cells = problem.grid, []
    first, last = grid.blocks[0][0], grid.blocks[-1][1]
    for minute in range(first, last, grid.step_min):
        lunch = not any(start <= minute < end for start, end in grid.blocks)
        row = _row(problem, minute)
        # Full hours, plus the start of each half-day (8h30, 13h30)
        shown = minute % 60 == 0 or any(minute == start for start, _ in grid.blocks)
        label = f"{minute // 60}h{minute % 60:02d}" if shown else ""
        cells.append(f'<div class="time" style="grid-row:{row};grid-column:1">{label}</div>')
        for day in range(grid.days):
            css = "cell lunch" if lunch else "cell"
            cells.append(f'<div class="{css}" style="grid-row:{row};grid-column:{day + 2}"></div>')
    return cells


def _group_name(problem: Problem, group_id: int) -> str:
    return problem.groups_by_id[group_id].name or f"groupe {group_id}"


def _ancestors(problem: Problem, group_id: int) -> list[int]:
    chain, parent = [], problem.groups_by_id[group_id].parent_id
    while parent is not None:
        chain.append(parent)
        parent = problem.groups_by_id[parent].parent_id
    return chain


def _class_box(problem: Problem, p: Placement, conflict: bool, shift: int = 0) -> str:
    session = problem.sessions_by_id[p.session_id]
    title = f"{session.session_type} {session.label or f'#{session.id}'}"
    teachers = ", ".join(problem.teacher_names.get(t, f"prof {t}") for t in sorted(session.teacher_ids))
    room = problem.rooms_by_id[p.room_id].name or f"salle {p.room_id}"
    color = COLORS.get(session.session_type, "#eee")
    css = "class conflict" if conflict else "class"
    return (
        f'<div class="{css}" style="grid-row:{_row(problem, p.start_min)}/{_row(problem, p.end_min)};'
        f'grid-column:{p.day + 2};background:{color};margin-left:{2 + 14 * shift}px" title="{escape(title)}">'
        f"<b>{escape(title)}</b><br>{escape(teachers)} · {escape(room)}</div>"
    )


def _week(problem: Problem, timetable: list[Placement]) -> str:
    head = ['<div class="head" style="grid-column:1"></div>'] + [
        f'<div class="head" style="grid-column:{d + 2}">{DAYS[d]}</div>' for d in range(problem.grid.days)
    ]
    ordered = sorted(timetable, key=lambda p: (p.day, p.start_min, p.session_id))
    boxes = []
    for i, p in enumerate(ordered):
        conflict = any(p is not q and p.overlaps(q) for q in ordered)
        shift = sum(p.overlaps(q) for q in ordered[:i])  # offset so overlapping classes stay visible
        boxes.append(_class_box(problem, p, conflict, shift))
    return '<div class="week">' + "".join(head + _background(problem) + boxes) + "</div>"


def _heading(problem: Problem, group_id: int) -> str:
    parents = [_group_name(problem, g) for g in _ancestors(problem, group_id)]
    suffix = f" (avec les cours de {', '.join(parents)})" if parents else ""
    return f"Étudiant de {_group_name(problem, group_id)}{suffix}"


def _summary(problem: Problem, label: str, solution: Solution) -> str:
    result = evaluate(problem, solution)
    status = '<span class="ok">valide</span>' if result.feasible else '<span class="ko">invalide</span>'
    return (
        f'<div><h2>{escape(label)}</h2><p class="summary">{status} · {result.hard_violations} violation(s) · '
        f"{result.unplaced} non placée(s) · score souple {result.soft_score:.2f}</p></div>"
    )


def _row_of(cells: list[str]) -> str:
    """One column per algorithm, in the order given, side by side."""
    # Fixed column width (one week grid) so summaries line up with the grids below them
    return f'<div class="compare" style="grid-template-columns:repeat({len(cells)}, {WEEK_WIDTH_PX}px)">{"".join(cells)}</div>'


def _spread(items: list, count: int) -> list:
    """`count` items evenly spread over the list, first and last included."""
    if len(items) <= count:
        return items
    if count == 1:
        return items[:1]
    step = (len(items) - 1) / (count - 1)
    return [items[round(i * step)] for i in range(count)]


def select_groups(problem: Problem, wanted: list[str] | None, max_groups: int) -> list[int]:
    """Finest groups to show, by name or id; by default `max_groups` of them, spread over the list."""
    parents = {g.parent_id for g in problem.groups}
    leaves = [g for g in problem.groups if g.id not in parents]
    if wanted:
        return [g.id for g in leaves if g.name in wanted or str(g.id) in wanted]
    return [g.id for g in _spread(leaves, max_groups)]


def render_html(
    problem: Problem, solutions: dict[str, Solution], title: str, groups: list[int] | None = None
) -> str:
    groups = groups if groups is not None else select_groups(problem, None, max_groups=2)
    timetables = {
        label: leaf_timetables(problem, list(solution.placements.values())) for label, solution in solutions.items()
    }
    parts = [_row_of([_summary(problem, label, s) for label, s in solutions.items()])]
    for group in groups:
        parts.append(f"<h3>{escape(_heading(problem, group))}</h3>")
        parts.append(_row_of([_week(problem, timetables[label][group]) for label in solutions]))
    return (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{escape(title)}</title>'
        f"<style>{CSS}</style></head><body><h1>{escape(title)}</h1>{''.join(parts)}</body></html>"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--instance", default="tiny", help="name in scheduling/instances/")
    parser.add_argument("-a", "--algorithms", nargs="+", choices=sorted(ALGORITHMS), help="default: all")
    parser.add_argument("--seed", type=int, default=0, help="seed for non-deterministic algorithms")
    parser.add_argument("-g", "--groups", nargs="+", help="finest groups to show, by name or id (default: the first 2)")
    parser.add_argument("-o", "--output", type=Path, help="default: scheduling/results/<instance>.html")
    args = parser.parse_args(argv)

    problem = load_instance(INSTANCES_DIR / f"{args.instance}.json")
    keys = args.algorithms or sorted(ALGORITHMS)
    solutions = {key: ALGORITHMS[key].solve(problem, random.Random(args.seed), None) for key in keys}
    output = args.output or RESULTS_DIR / f"{args.instance}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    groups = select_groups(problem, args.groups, max_groups=2)
    output.write_text(render_html(problem, solutions, f"Instance {args.instance}", groups), encoding="utf-8")
    print(f"Written to {output}")


if __name__ == "__main__":
    main()
