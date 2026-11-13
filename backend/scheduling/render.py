"""Static HTML view of solutions: one weekly grid per student group, algorithms side by side.

Usage, from backend/:
    python -m scheduling.render -i tiny                      # every algorithm, seed 0
    python -m scheduling.render -i tiny -a greedy@1 random@1 --seed 3 -o /tmp/tiny.html

Classes that overlap in a group's timetable are outlined in red.
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
DAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi")
COLORS = {"CM": "#cfe0fc", "TD": "#d3f2d6", "TP": "#fde2c4", "EXAM": "#f8cfd0"}

CSS = """
body { font-family: system-ui, sans-serif; margin: 24px; color: #1d1d1f; background: #fff; }
.algorithms { display: flex; gap: 32px; flex-wrap: wrap; align-items: flex-start; }
.summary { font-size: 13px; margin: 4px 0 12px; }
.ok { color: #1a7f37; } .ko { color: #c62828; }
h3 { font-size: 14px; margin: 16px 0 4px; }
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


def _class_box(problem: Problem, p: Placement, conflict: bool) -> str:
    session = problem.sessions_by_id[p.session_id]
    teachers = ", ".join(str(t) for t in sorted(session.teacher_ids))
    groups = ", ".join(str(g) for g in sorted(session.group_ids))
    color = COLORS.get(session.session_type, "#eee")
    css = "class conflict" if conflict else "class"
    return (
        f'<div class="{css}" style="grid-row:{_row(problem, p.start_min)}/{_row(problem, p.end_min)};'
        f'grid-column:{p.day + 2};background:{color}">'
        f"<b>{escape(session.session_type)} #{session.id}</b> · gr. {groups}<br>prof {teachers} · salle {p.room_id}</div>"
    )


def _week(problem: Problem, timetable: list[Placement]) -> str:
    head = ['<div class="head" style="grid-column:1"></div>'] + [
        f'<div class="head" style="grid-column:{d + 2}">{DAYS[d]}</div>' for d in range(problem.grid.days)
    ]
    boxes = [_class_box(problem, p, any(p is not q and p.overlaps(q) for q in timetable)) for p in timetable]
    return '<div class="week">' + "".join(head + _background(problem) + boxes) + "</div>"


def _algorithm_column(problem: Problem, label: str, solution: Solution) -> str:
    result = evaluate(problem, solution)
    status = '<span class="ok">valide</span>' if result.feasible else '<span class="ko">invalide</span>'
    summary = (
        f"{status} · {result.hard_violations} violation(s) · {result.unplaced} non placée(s) · "
        f"score souple {result.soft_score:.2f}"
    )
    grids = "".join(
        f"<h3>Groupe {group} (avec ses groupes parents)</h3>{_week(problem, timetable)}"
        for group, timetable in leaf_timetables(problem, list(solution.placements.values())).items()
    )
    return f'<section><h2>{escape(label)}</h2><p class="summary">{summary}</p>{grids}</section>'


def render_html(problem: Problem, solutions: dict[str, Solution], title: str) -> str:
    columns = "".join(_algorithm_column(problem, label, s) for label, s in solutions.items())
    return (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{escape(title)}</title>'
        f"<style>{CSS}</style></head><body><h1>{escape(title)}</h1>"
        f'<div class="algorithms">{columns}</div></body></html>'
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--instance", default="tiny", help="name in scheduling/instances/")
    parser.add_argument("-a", "--algorithms", nargs="+", choices=sorted(ALGORITHMS), help="default: all")
    parser.add_argument("--seed", type=int, default=0, help="seed for non-deterministic algorithms")
    parser.add_argument("-o", "--output", type=Path, help="default: scheduling/results/<instance>.html")
    args = parser.parse_args(argv)

    problem = load_instance(INSTANCES_DIR / f"{args.instance}.json")
    keys = args.algorithms or sorted(ALGORITHMS)
    solutions = {key: ALGORITHMS[key].solve(problem, random.Random(args.seed), None) for key in keys}
    output = args.output or RESULTS_DIR / f"{args.instance}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(problem, solutions, f"Instance {args.instance}"), encoding="utf-8")
    print(f"Written to {output}")


if __name__ == "__main__":
    main()
