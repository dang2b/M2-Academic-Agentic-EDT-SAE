import csv
import random

from scheduling.algorithms import ALGORITHMS
from scheduling.benchmark import FIELDS, main, run_benchmark, summarize
from scheduling.evaluation import evaluate
from scheduling.examples import tiny
from scheduling.io import INSTANCES_DIR, load_instance, problem_from_dict, problem_to_dict

RANDOM = ALGORITHMS["random@1"]


def test_instances_survive_a_json_round_trip():
    problem = tiny()
    assert problem_to_dict(problem_from_dict(problem_to_dict(problem))) == problem_to_dict(problem)


def test_stored_tiny_instance_matches_the_example():
    assert problem_to_dict(load_instance(INSTANCES_DIR / "tiny.json")) == problem_to_dict(tiny())


def test_random_baseline_places_everything_on_the_grid():
    problem = tiny()
    result = evaluate(problem, RANDOM.solve(problem, random.Random(0), None))
    assert result.unplaced == 0
    assert result.hard["invalid_placement"] == 0


def test_same_seed_same_solution():
    problem = tiny()
    first = RANDOM.solve(problem, random.Random(42), None)
    second = RANDOM.solve(problem, random.Random(42), None)
    assert first.placements == second.placements


def test_one_row_per_seed_with_every_field():
    rows = run_benchmark([RANDOM], {"tiny": tiny()}, seeds=3, time_limit_s=None)
    assert [r["seed"] for r in rows] == [0, 1, 2]
    assert all(set(r) == set(FIELDS) for r in rows)
    assert rows[0]["sessions"] == 4 and rows[0]["instance"] == "tiny"
    assert len(summarize(rows)) == 2  # header + one line for (tiny, random@1)


def test_cli_writes_the_csv(tmp_path):
    output = tmp_path / "results.csv"
    main(["-a", "random@1", "-i", "tiny", "--seeds", "2", "-o", str(output)])
    with output.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2 and rows[0]["algorithm"] == "random"
