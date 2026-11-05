"""Compte les tokens, le coût et les tours Claude Code sur ce projet (sous-agents inclus).

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


def session_files(since: datetime | None) -> list[Path]:
    sessions = sorted(TRANSCRIPTS.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not sessions:
        raise SystemExit(f"Aucun transcript dans {TRANSCRIPTS}")
    if since is None:
        sessions = sessions[-1:]
    files = []
    for s in sessions:
        files.append(s)
        files.extend((s.parent / s.stem / "subagents").glob("*.jsonl"))
    return files


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


def count(files: list[Path], since: datetime | None, until: datetime | None) -> dict:
    seen, prompts, local_commands, unpriced, stamps = set(), set(), set(), set(), []
    totals = defaultdict(float)
    output_by_model = defaultdict(int)
    for path in files:
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
            output_by_model[msg.get("model") or "?"] += u.get("output_tokens", 0)
            c = cost(msg.get("model", ""), u)
            if c is None:
                unpriced.add(msg.get("model"))
            else:
                totals["cout_usd"] += c
    totals["tours"] = len(prompts - local_commands)
    totals["reponses"] = len(seen)
    # Models that produced output, main one (most output tokens) first
    totals["modeles"] = sorted(((m, n) for m, n in output_by_model.items() if n), key=lambda mn: -mn[1])
    if stamps:
        totals["debut"], totals["fin"] = min(stamps), max(stamps)
        totals["duree_min"] = (totals["fin"] - totals["debut"]).total_seconds() / 60
    if unpriced:
        print(f"Attention : modèles sans tarif dans PRICES, exclus du coût : {unpriced}")
    return totals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=parse_local, help='heure locale, ex. "2026-11-05 14:00"')
    parser.add_argument("--until", type=parse_local)
    args = parser.parse_args()

    t = count(session_files(args.since), args.since, args.until)
    if "debut" in t:
        for k in ("debut", "fin"):
            print(f"{k:16} {t[k].astimezone():%Y-%m-%d %H:%M}")
        print(f"{'duree_min':16} {t['duree_min']:.0f}   (premier au dernier horodatage : base pour temps_reel_min)")
    print(f"{'duree_agent_min':16} {t['duree_agent_min']:.0f}   (temps où l'agent travaillait, tours terminés seulement)")
    if t["modeles"]:
        out = sum(n for _, n in t["modeles"])
        shares = ", ".join(f"{m} {n / out:.0%}" for m, n in t["modeles"])
        print(f"{'modele':16} {t['modeles'][0][0]}   (part des tokens de sortie : {shares})")
    for k in ("tours", "reponses", "entree", "cache_lu", "sortie"):
        print(f"{k:16} {int(t[k])}")
    print(f"{'cout_usd':16} {t['cout_usd']:.2f}")
    print("\nColonnes CSV (tours,tokens_entree,tokens_cache_lu,tokens_sortie,cout_usd) :")
    print(f"{int(t['tours'])},{int(t['entree'])},{int(t['cache_lu'])},{int(t['sortie'])},{t['cout_usd']:.2f}")


if __name__ == "__main__":
    main()
