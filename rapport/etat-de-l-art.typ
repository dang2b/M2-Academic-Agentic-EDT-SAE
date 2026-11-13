#import "template.typ": *

#show: rapport.with(
  title: "État de l'art : architectures agentiques",
  subtitle: "Groupe 3 — Projet B (emplois du temps), approche agentique",
  date: "Novembre 2026",
)

= Qu'est-ce qu'un agent ?

Un *workflow* enchaîne des appels au LLM selon un chemin fixé dans le code. Un *agent* décide lui-même de ses étapes : il lit, agit avec des outils (fichiers, terminal, tests), observe le résultat et recommence jusqu'au but @anthropic2024agents.

= Les architectures possibles

#table(
  columns: (auto, 1fr, 1fr),
  [Architecture], [Principe], [Exemples],
  [Agent seul avec outils], [Un LLM en boucle : lire → modifier → tester → corriger], [SWE-agent @yang2024sweagent, Claude Code],
  [Orchestrateur + sous-agents], [Un agent principal découpe la tâche et délègue à des agents spécialisés (contexte et outils séparés)], [sous-agents Claude Code @claudecode2026subagents],
  [Multi-agents à rôles], [Agents « chef de projet », « développeur », « testeur » qui s'échangent des documents], [MetaGPT @hong2024metagpt, ChatDev @qian2024chatdev],
)

Recommandation de la littérature : *commencer simple* et n'ajouter des agents que si le gain est mesurable @anthropic2024agents.

= Les outils, du moins au plus autonome

#table(
  columns: (1fr, 1fr, 1fr, 1fr),
  [Autocomplétion], [Chat], [Agent dans l'IDE], [Agent en terminal],
  [Copilot], [ChatGPT, Claude.ai], [Cursor, Copilot agent], [Claude Code, Codex CLI],
  table.cell(colspan: 2, align: center)[groupe classique], table.cell(colspan: 2, align: center)[groupe agentique (nous)],
)

= Ce que disent les études

#table(
  columns: (auto, 1fr),
  [Étude], [Résultat clé],
  [Peng et al. 2023 @peng2023copilot], [Avec Copilot, une tâche simple est faite *56 % plus vite*.],
  [METR 2025 @becker2025metr], [Développeurs expérimentés sur leurs propres projets : *19 % plus lents* avec l'IA, alors qu'ils pensaient être 20 % plus rapides.],
  [Pearce et al. 2022 @pearce2022asleep], [*≈ 40 %* du code généré dans des scénarios à risque contient une faille de sécurité.],
  [DORA 2025 @google2025dora], [L'IA augmente le débit de livraison mais *dégrade la stabilité* sans tests automatisés solides.],
  [Denisov-Blanch et al. 2026 @denisovblanch2026ramp], [Les projets qui versionnent la configuration de leur agent voient leur complexité *deux fois moins* augmenter.],
)

#note(title: "En résumé")[
  L'IA peut accélérer, mais pas toujours, et le ressenti surestime le gain. La qualité dépend des garde-fous : tests, revue, configuration de l'agent.
]

= Ce qu'on en retient pour notre projet

- *Architecture* : Claude Code comme agent principal, avec un contexte projet versionné (`AGENTS.md`) et des sous-agents ajoutés seulement s'ils apportent un gain.
- *Garde-fous* : revue humaine par pull request, tests et analyse statique en CI.
- *Mesurer plutôt que ressentir* : temps réel contre temps estimé, taux de retouche du code généré, bugs selon l'origine du code (IA ou humain).
- *L'algorithme reste à nous* : nous concevons et justifions la génération d'emploi du temps (glouton, coloration de graphe, recuit simulé) ; l'agent aide à l'implémenter.

#pagebreak()
#bibliography("refs.bib", title: "Références", style: "ieee")
