"""Compte les tokens, le coût et les tours Claude Code sur ce projet (sous-agents inclus).

Les tokens et le coût additionnent l'orchestrateur et ses sous-agents ; chaque réponse est
facturée au tarif de son propre modèle. Le script donne aussi le nombre de sous-agents et
leur modèle principal, séparé de celui de l'orchestrateur, ainsi que leur part
des tokens de sortie et du coût.

Usage :
  python journal/tokens.py                                  # dernière session
  python journal/tokens.py --since "2026-11-05 14:00"       # depuis une heure donnée
  python journal/tokens.py --since "2026-11-05 14:00" --until "2026-11-05 16:30"

Lit les transcripts de ~/.claude/projects/<projet>/ (chacun sur sa machine).
Le coût est l'équivalent au tarif API, même avec un abonnement Claude.
"""
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(PROJECT_ROOT))

# $ par million de tokens : entrée, sortie, lecture de cache (tarifs API, octobre 2026).
# Écriture de cache : 1,25x l'entrée (TTL 5 min), 2x (TTL 1 h).
PRICES = {
    "claude-fable-5-1": (10.00, 50.00, 0.25),
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}


def parse_local(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def session_files(since: datetime | None) -> list[tuple[Path, bool]]:
    """Transcripts to read, each flagged True if it belongs to a subagent."""
    sessions = sorted(TRANSCRIPTS.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not sessions:
        raise SystemExit(f"Aucun transcript dans {TRANSCRIPTS}")
    if since is None:
        sessions = sessions[-1:]
    files = []
    for s in sessions:
        files.append((s, False))
        files.extend((f, True) for f in (s.parent / s.stem / "subagents").glob("*.jsonl"))
    return files


def by_output(output_by_model: dict) -> list[tuple[str, int]]:
    """Models that produced output, main one (most output tokens) first."""
    return sorted(((m, n) for m, n in output_by_model.items() if n), key=lambda mn: -mn[1])


def cost(model: str, u: dict) -> float | None:
    if model not in PRICES:
        return None
    p_in, p_out, p_read = PRICES[model]
    cache = u.get("cache_creation") or {}
    write_1h = cache.get("ephemeral_1h_input_tokens", 0)
    write_5m = u.get("cache_creation_input_tokens", 0) - write_1h
    return (
        u.get("input_tokens", 0) * p_in
        + write_5m * p_in * 1.25
        + write_1h * p_in * 2
        + u.get("cache_read_input_tokens", 0) * p_read
        + u.get("output_tokens", 0) * p_out
    ) / 1_000_000


def count(files: list[tuple[Path, bool]], since: datetime | None, until: datetime | None) -> dict:
    seen, prompts, local_commands, unpriced, stamps = set(), set(), set(), set(), []
    totals = defaultdict(float)
    # Orchestrator and subagents are kept apart: they may run on different models
    output_by_model = {False: defaultdict(int), True: defaultdict(int)}
    active_subagents = set()
    for path, is_subagent in files:
        for line in path.open(encoding="utf-8"):
            entry = json.loads(line)
            if "timestamp" not in entry:
                continue
            ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            if (since and ts < since) or (until and ts > until):
                continue
            stamps.append(ts)
            # Un tour = un prompt humain (les résultats d'outils partagent son promptId)
            if entry.get("type") == "user" and not entry.get("isSidechain") and entry.get("promptId"):
                prompts.add(entry["promptId"])
                # /model, /effort... are run by Claude Code itself: nothing is sent to the model
                content = (entry.get("message") or {}).get("content")
                if isinstance(content, str) and content.startswith("<local-command-"):
                    local_commands.add(entry["promptId"])
            # Claude Code écrit la durée de chaque tour terminé (du prompt à la fin de la réponse)
            if entry.get("subtype") == "turn_duration":
                totals["duree_agent_min"] += entry.get("durationMs", 0) / 60_000
            msg = entry.get("message")
            if not isinstance(msg, dict) or not msg.get("usage") or msg.get("id") in seen:
                continue
            seen.add(msg["id"])  # une même réponse est écrite une fois par bloc de contenu
            u = msg["usage"]
            totals["entree"] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            totals["cache_lu"] += u.get("cache_read_input_tokens", 0)
            totals["sortie"] += u.get("output_tokens", 0)
            output_by_model[is_subagent][msg.get("model") or "?"] += u.get("output_tokens", 0)
            if is_subagent:
                active_subagents.add(path)
                totals["sortie_sous_agents"] += u.get("output_tokens", 0)
            c = cost(msg.get("model", ""), u)
            if c is None:
                unpriced.add(msg.get("model"))
            else:
                totals["cout_usd"] += c
                if is_subagent:
                    totals["cout_sous_agents_usd"] += c
    totals["tours"] = len(prompts - local_commands)
    totals["reponses"] = len(seen)
    # A subagent counts if it answered at least once in the time range
    totals["sous_agents"] = len(active_subagents)
    totals["modeles"] = by_output(output_by_model[False])
    totals["modeles_sous_agents"] = by_output(output_by_model[True])
    if stamps:
        totals["debut"], totals["fin"] = min(stamps), max(stamps)
        totals["duree_min"] = (totals["fin"] - totals["debut"]).total_seconds() / 60
    if unpriced:
        print(f"Attention : modèles sans tarif dans PRICES, exclus du coût : {unpriced}")
    return totals


def print_models(label: str, models: list[tuple[str, int]], who: str) -> None:
    if not models:
        return
    out = sum(n for _, n in models)
    shares = ", ".join(f"{m} {n / out:.0%}" for m, n in models)
    print(f"{label:20} {models[0][0]}   (part des tokens de sortie, {who} : {shares})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=parse_local, help='heure locale, ex. "2026-11-05 14:00"')
    parser.add_argument("--until", type=parse_local)
    args = parser.parse_args()

    t = count(session_files(args.since), args.since, args.until)
    if "debut" in t:
        for k in ("debut", "fin"):
            print(f"{k:20} {t[k].astimezone():%Y-%m-%d %H:%M}")
        print(f"{'duree_min':20} {t['duree_min']:.0f}   (premier au dernier horodatage : base pour temps_reel_min)")
    print(f"{'duree_agent_min':20} {t['duree_agent_min']:.0f}   (temps où l'agent travaillait, tours terminés seulement)")
    print_models("modele", t["modeles"], "orchestrateur")
    print(f"{'sous_agents':20} {t['sous_agents']}")
    print_models("modele_sous_agents", t["modeles_sous_agents"], "sous-agents")
    for k in ("tours", "reponses", "entree", "cache_lu", "sortie"):
        print(f"{k:20} {int(t[k])}")
    print(f"{'cout_usd':20} {t['cout_usd']:.2f}")
    print(f"{'sortie_sous_agents':20} {int(t['sortie_sous_agents'])}")
    print(f"{'cout_sous_agents_usd':20} {t['cout_sous_agents_usd']:.2f}")
    sub_model = t["modeles_sous_agents"][0][0] if t["modeles_sous_agents"] else ""
    print("\nColonnes CSV (sous_agents,modele_sous_agents,tours,tokens_entree,tokens_cache_lu,tokens_sortie,cout_usd,"
          "tokens_sortie_sous_agents,cout_sous_agents_usd) :")
    print(f"{t['sous_agents']},{sub_model},{int(t['tours'])},{int(t['entree'])},{int(t['cache_lu'])},"
          f"{int(t['sortie'])},{t['cout_usd']:.2f},{int(t['sortie_sous_agents'])},{t['cout_sous_agents_usd']:.2f}")


if __name__ == "__main__":
    main()
