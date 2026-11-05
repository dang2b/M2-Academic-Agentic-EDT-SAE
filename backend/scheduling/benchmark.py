"""Run every algorithm on every instance and write one CSV row per run.

Usage, from backend/ (pure Python, no database or container needed):
    python -m scheduling.benchmark                       # all algorithms, all instances, 5 seeds
    python -m scheduling.benchmark -a random@1 -i tiny --seeds 10 --time-limit 30

Deterministic algorithms run once per instance, the others once per seed. Each row records the
commit it was produced with, so results stay comparable as the algorithms evolve.
"""
import argparse
import csv
import random
import statistics
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from scheduling.algorithms import ALGORITHMS
from scheduling.algorithms.base import Algorithm
from scheduling.evaluation import HARD_CONSTRAINTS, evaluate
from scheduling.io import INSTANCES_DIR, load_instance
from scheduling.model import Problem

RESULTS_DIR = Path(__file__).resolve().parent / "results"

FIELDS = [
    "run_at", "commit", "instance", "sessions", "rooms", "groups", "teachers", "conflict_density",
    "algorithm", "version", "seed", "time_limit_s", "time_s",
    "feasible", "hard_violations", *HARD_CONSTRAINTS, "unplaced",
    "short_gaps", "long_gap_minutes", "preference_misses", "imbalance_minutes", "gap_score", "soft_score",
]  # fmt: skip


def instance_stats(problem: Problem) -> dict:
    n = len(problem.sessions)
    edges = sum(len(neighbours) for neighbours in problem.conflicts.values()) // 2
    return {
        "sessions": n,
        "rooms": len(problem.rooms),
        "groups": len(problem.groups),
        "teachers": len({t for s in problem.sessions for t in s.teacher_ids}),
        "conflict_density": round(edges / (n * (n - 1) / 2), 4) if n > 1 else 0.0,
    }


def run_once(algorithm: Algorithm, problem: Problem, seed: int, time_limit_s: float | None) -> dict:
    started = time.perf_counter()
    solution = algorithm.solve(problem, random.Random(seed), time_limit_s)
    elapsed = time.perf_counter() - started
    result = evaluate(problem, solution)
    return {
        "algorithm": algorithm.name,
        "version": algorithm.version,
        "seed": seed,
        "time_limit_s": time_limit_s,
        "time_s": round(elapsed, 4),
        "feasible": result.feasible,
        "hard_violations": result.hard_violations,
        **{name: result.hard[name] for name in HARD_CONSTRAINTS},
        "unplaced": result.unplaced,
        "short_gaps": result.short_gaps,
        "long_gap_minutes": result.long_gap_minutes,
        "preference_misses": result.preference_misses,
        "imbalance_minutes": round(result.imbalance_minutes, 1),
        "gap_score": round(result.gap_score, 2),
        "soft_score": round(result.soft_score, 2),
    }


def run_benchmark(
    algorithms: list[Algorithm], instances: dict[str, Problem], seeds: int, time_limit_s: float | None
) -> list[dict]:
    context = {"run_at": datetime.now(UTC).isoformat(timespec="seconds"), "commit": git_commit()}
    rows = []
    for name, problem in instances.items():
        stats = {"instance": name, **instance_stats(problem)}
        for algorithm in algorithms:
            for seed in [0] if algorithm.deterministic else range(seeds):
                rows.append(context | stats | run_once(algorithm, problem, seed, time_limit_s))
    return rows


def summarize(rows: list[dict]) -> list[str]:
    """One line per (instance, algorithm): means over seeds, standard deviation of the soft score."""
    runs = defaultdict(list)
    for row in rows:
        runs[(row["instance"], f"{row['algorithm']}@{row['version']}")].append(row)
    lines = [f"{'instance':<12} {'algorithm':<14} {'runs':>4} {'feasible':>8} {'hard':>6} "
             f"{'unplaced':>8} {'soft (mean ± sd)':>18} {'time_s':>8}"]  # fmt: skip
    for (instance, key), group in runs.items():
        soft = [r["soft_score"] for r in group]
        sd = statistics.stdev(soft) if len(soft) > 1 else 0.0
        lines.append(
            f"{instance:<12} {key:<14} {len(group):>4} {_mean(group, 'feasible'):>8.0%} "
            f"{_mean(group, 'hard_violations'):>6.1f} {_mean(group, 'unplaced'):>8.1f} "
            f"{statistics.mean(soft):>10.2f} ± {sd:<5.2f} {_mean(group, 'time_s'):>8.3f}"
        )
    return lines


def _mean(rows: list[dict], key: str) -> float:
    return statistics.mean(float(r[key]) for r in rows)


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def git_commit() -> str:
    """Short hash of HEAD, with "-dirty" when uncommitted changes may have affected the results."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "."], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return sha.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")


def load_instances(names: list[str] | None) -> dict[str, Problem]:
    paths = sorted(INSTANCES_DIR.glob("*.json"))
    if names:
        paths = [INSTANCES_DIR / f"{name}.json" for name in names]
    return {path.stem: load_instance(path) for path in paths}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-a", "--algorithms", nargs="+", choices=sorted(ALGORITHMS), help="default: all")
    parser.add_argument("-i", "--instances", nargs="+", help="names in scheduling/instances/ (default: all)")
    parser.add_argument("--seeds", type=int, default=5, help="runs per instance for non-deterministic algorithms")
    parser.add_argument("--time-limit", type=float, default=None, help="seconds per run, for algorithms that use it")
    parser.add_argument("-o", "--output", type=Path, help="CSV file (default: scheduling/results/<date>.csv)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    algorithms = [ALGORITHMS[key] for key in args.algorithms or sorted(ALGORITHMS)]
    rows = run_benchmark(algorithms, load_instances(args.instances), args.seeds, args.time_limit)
    output = args.output or RESULTS_DIR / f"{datetime.now(UTC):%Y-%m-%d_%H%M%S}.csv"
    write_csv(rows, output)
    print("\n".join(summarize(rows)))
    print(f"\n{len(rows)} runs written to {output}")


if __name__ == "__main__":
    main()
