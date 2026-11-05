"""Calcule les métriques du journal à partir de journal/ia.csv et de l'historique git.

Usage : python journal/stats.py
"""
import csv
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

CSV_PATH = Path(__file__).parent / "ia.csv"
INFRA_MODULE = "infra-agent"  # mise en place de l'architecture agentique (AGENTS.md, skills, sous-agents)
CODE_FILE = re.compile(r"\.(py|ts|tsx|js|jsx|sql|css|html|ya?ml)$|Dockerfile$")
KINDS = ("genere", "retouche", "manuel")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def load_rows() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def filled(row: dict, key: str) -> bool:
    return bool((row.get(key) or "").strip())


def values(rows: list[dict], key: str) -> list[float]:
    """Valeurs renseignées seulement : une case vide n'est pas un 0."""
    return [float(r[key]) for r in rows if filled(r, key)]


def total(xs: list) -> float | None:
    return sum(xs) if xs else None


def mean(xs: list) -> float | None:
    return sum(xs) / len(xs) if xs else None


def summarize(rows: list[dict]) -> dict:
    # Le ratio ne compare que les tâches qui ont à la fois une estimation et un temps réel.
    both = [r for r in rows if filled(r, "estimation_min") and filled(r, "temps_reel_min")]
    est = sum(values(both, "estimation_min"))
    answers = [(r.get("succes_sans_intervention") or "").strip() for r in rows]
    success = [a == "oui" for a in answers if a in ("oui", "non")]
    return {
        "taches": len(rows),
        "interventions_par_tache": mean(values(rows, "interventions")),
        "taux_succes_sans_intervention": mean(success),
        "temps_estime_min": total(values(rows, "estimation_min")),
        "temps_reel_min": total(values(rows, "temps_reel_min")),
        "ratio_reel_estime": sum(values(both, "temps_reel_min")) / est if est else None,
        "temps_revue_min": total(values(rows, "temps_revue_min")),
        "tours_par_tache": mean(values(rows, "tours")),
        "tokens_entree": total(values(rows, "tokens_entree")),
        "tokens_cache_lu": total(values(rows, "tokens_cache_lu")),
        "tokens_sortie": total(values(rows, "tokens_sortie")),
        "tokens_sortie_par_tache": mean(values(rows, "tokens_sortie")),
        "cout_usd": total(values(rows, "cout_usd")),
        "cout_usd_par_tache": mean(values(rows, "cout_usd")),
    }


def git_commits() -> list[dict]:
    """Commits avec auteur, trailer IA, commits corrigés, lignes de code ajoutées/supprimées."""
    out = git("log", "--format=@@%H|%an|%(trailers:key=IA,valueonly,separator=)"
              "|%(trailers:key=Corrige,valueonly,separator=,)", "--numstat")
    commits = []
    for line in out.splitlines():
        if line.startswith("@@"):
            sha, author, kind, fixes = line[2:].split("|")
            commits.append({"sha": sha, "author": author, "kind": kind.strip().lower() or "manuel",
                            "fixes": [f.strip() for f in fixes.split(",") if f.strip()],
                            "added": 0, "deleted": 0})
        elif line and commits:
            added, deleted, path = line.split("\t", 2)
            if added.isdigit() and CODE_FILE.search(path):  # "-" pour les fichiers binaires
                commits[-1]["added"] += int(added)
                commits[-1]["deleted"] += int(deleted)
    return commits


def surviving_lines(commits: list[dict]) -> Counter:
    """Lignes de code encore présentes à HEAD, par origine (via git blame)."""
    kind_of = {c["sha"]: c["kind"] for c in commits}
    alive = Counter()
    for path in git("ls-files").splitlines():
        if not CODE_FILE.search(path):
            continue
        for line in git("blame", "--line-porcelain", "HEAD", "--", path).splitlines():
            sha = line.split(" ", 1)[0]
            if len(sha) == 40 and sha in kind_of and not line.startswith("\t"):
                alive[kind_of[sha]] += 1
    return alive


def print_block(title: str, stats: dict) -> None:
    print(f"\n## {title}")
    for k, v in stats.items():
        shown = "non renseigné" if v is None else f"{v:.2f}" if isinstance(v, float) else v
        print(f"  {k:32} {shown}")


def print_journal(rows: list[dict]) -> None:
    print_block("Global", summarize(rows))
    by_author = defaultdict(list)
    for r in rows:
        by_author[r["auteur"]].append(r)
    for author, author_rows in sorted(by_author.items()):
        print_block(author, summarize(author_rows))
    for column in ("outil", "modele"):
        groups = defaultdict(list)
        for r in rows:
            groups[(r.get(column) or "").strip() or "?"].append(r)
        for name, group_rows in sorted(groups.items()):
            print_block(f"{column} : {name}", summarize(group_rows))

    total_time = sum(values(rows, "temps_reel_min")) or 1
    by_module = defaultdict(list)
    for r in rows:
        by_module[r["module"]].append(r)
    print("\n## Répartition par module (tâches, temps, part du temps)")
    for module, module_rows in sorted(by_module.items()):
        t = sum(values(module_rows, "temps_reel_min"))
        print(f"  {module:20} {len(module_rows):4} taches {t:7.0f} min  {t / total_time:6.1%}")

    infra = by_module.get(INFRA_MODULE)
    if infra:
        print_block(f"Coût fixe de l'architecture agentique ({INFRA_MODULE})", {
            "temps_min": total(values(infra, "temps_reel_min")),
            "cout_usd": total(values(infra, "cout_usd")),
            "part_du_temps_total": sum(values(infra, "temps_reel_min")) / total_time,
        })


def print_git(commits: list[dict]) -> None:
    print("\n## Commits par auteur et origine")
    by_author = defaultdict(Counter)
    for c in commits:
        by_author[c["author"]][c["kind"]] += 1
    print(f"  {'auteur':20} " + " ".join(f"{k:>9}" for k in KINDS) + "     total")
    for author, counts in sorted(by_author.items()):
        print(f"  {author:20} " + " ".join(f"{counts[k]:9}" for k in KINDS) + f" {sum(counts.values()):9}")

    added, deleted = Counter(), Counter()
    for c in commits:
        added[c["kind"]] += c["added"]
        deleted[c["kind"]] += c["deleted"]
    alive = surviving_lines(commits)
    print("\n## Lignes de code par origine (ajoutées / supprimées / encore présentes)")
    for k in KINDS:
        print(f"  {k:20} {added[k]:7} {deleted[k]:7} {alive[k]:7}")
    if added["genere"]:
        survival = alive["genere"] / added["genere"]
        print(f"  {'taux de retouche':20} {added['retouche'] / added['genere']:.2%}  (lignes retouche / lignes generees)")
        print(f"  {'code IA modifie/supp':20} {1 - survival:.2%}  (lignes generees disparues de HEAD)")

    kind_of = {c["sha"]: c["kind"] for c in commits}
    bugs = Counter()
    for c in commits:
        for ref in c["fixes"]:
            bugs[next((k for sha, k in kind_of.items() if sha.startswith(ref)), "inconnu")] += 1
    print("\n## Bugs par origine (trailer Corrige)")
    for k in (*KINDS, "inconnu"):
        per_kloc = f"  ({bugs[k] / added[k] * 1000:.2f} / 1000 lignes)" if added.get(k) else ""
        print(f"  {k:20} {bugs[k]}{per_kloc}")


def main() -> None:
    rows = load_rows()
    if rows:
        print_journal(rows)
    else:
        print("Journal vide.")
    print_git(git_commits())


if __name__ == "__main__":
    main()
