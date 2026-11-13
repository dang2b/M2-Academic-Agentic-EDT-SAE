from scheduling.algorithms.greedy import solve
from scheduling.examples import AMPHI, CLASSROOM, demo, tiny
from scheduling.model import Placement, Solution, hm
from scheduling.render import main, parse_tabs, render_html, select_groups


def test_page_shows_each_algorithm_and_each_student_group():
    problem = tiny()
    html = render_html(problem, {"greedy@1": solve(problem)}, "Instance tiny")
    assert "greedy@1" in html and "valide" in html
    assert html.count("<h3>Étudiant de") == 2  # TD2 and TP1a, the finest groups
    assert "Étudiant de TP1a (avec les cours de TD1, Promo)" in html
    assert "conflict" not in html.split("</style>")[1]  # a valid timetable has no red box


def test_overlapping_classes_are_outlined():
    problem = tiny()
    clash = Solution()
    clash.place(Placement(1, 0, hm(8, 30), hm(10), AMPHI))
    clash.place(Placement(3, 0, hm(9), hm(10), CLASSROOM))  # TD2 during the promotion's CM
    html = render_html(problem, {"clash": clash}, "t")
    assert 'class="class conflict"' in html and "invalide" in html


def test_cli_writes_the_page(tmp_path):
    output = tmp_path / "tiny.html"
    main(["-i", "tiny", "-a", "greedy@1", "-o", str(output)])
    assert output.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_only_two_groups_by_default_or_the_ones_asked_for():
    problem = demo()
    assert select_groups(problem, None, max_groups=2) == [5, 10]  # first and last TP group
    assert select_groups(problem, ["TP C2", "5"], max_groups=2) == [5, 10]  # by name or id


def test_algorithms_are_side_by_side_in_the_given_order():
    problem = demo()
    html = render_html(problem, {"greedy@1": solve(problem), "random@1": Solution()}, "demo")
    assert html.index("greedy@1") < html.index("random@1")
    assert html.count("<h3>") == 2 and "repeat(2, minmax(0, 1fr))" in html


def test_one_tab_per_comparison_with_buttons():
    problem = demo()
    solutions = {"greedy@1": solve(problem), "random@1": Solution(), "dsatur@1": Solution()}
    html = render_html(problem, solutions, "demo", tabs=[("greedy@1", "random@1"), ("greedy@1", "dsatur@1")])
    assert html.count('<section class="tab"') == 2 and html.count("<button") == 2
    assert "Glouton / Hasard" in html and "Glouton / DSatur" in html
    assert '<section class="tab" hidden>' in html  # second tab hidden until clicked


def test_tabs_from_the_command_line():
    assert parse_tabs(None, None) == [("greedy@1", "random@1"), ("greedy@1", "dsatur@1")]
    assert parse_tabs(["greedy@1,dsatur@1,random@1"], None) == [("greedy@1", "dsatur@1", "random@1")]
    assert parse_tabs(None, ["greedy@1"]) == [("greedy@1",)]


def test_unplaced_sessions_are_listed_by_name():
    problem = tiny()
    html = render_html(problem, {"empty": Solution()}, "t")
    assert "Non placées : CM #1 (Promo)" in html
