from scheduling.algorithms.greedy import solve
from scheduling.examples import AMPHI, CLASSROOM, tiny
from scheduling.model import Placement, Solution, hm
from scheduling.render import main, render_html


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
