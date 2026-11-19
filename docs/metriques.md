# Grille de métriques — Groupe 3 (EDT, agentique)

La grille a deux parties :

- **Partie A, le socle commun** : les métriques génériques fixées pour les 4 groupes (document « Métriques » mis au propre par les alternants). Elles sont mesurées de la même façon par tout le monde, c'est ce qui permet de comparer l'approche classique et l'approche agentique. Les définitions et les sources sont celles du socle ; cette grille ajoute seulement **comment le groupe 3 les mesure** (source dans le dépôt, outil).
- **Partie B, les métriques propres à l'agentique** : ce que seul un groupe qui délègue le code à des agents peut mesurer (autonomie, coût en tokens, origine du code, coût de l'architecture agentique).

Les numéros `M1`–`M10` renvoient aux 10 métriques du plan de projet (`docs/Plan_Projet_M2.md`) ; la partie C indique où chacune se trouve.

Légende : ✅ en place · 🔧 à brancher (script ou CI) · 🚀 au déploiement · 📋 manuel

Sources des données, déjà en place :

- `journal/ia.csv` : une ligne par tâche (temps, interventions, tours, tokens, coût), voir `journal/README.md` ;
- trailers de commit `IA: genere`, `IA: retouche`, `Corrige: <sha>` ;
- `python journal/stats.py` : agrégation du journal et des trailers.

Une tâche = une PR (ou une issue). Un sprint = l'intervalle de dates du tableau GitHub Projects.

## Partie A — Socle commun aux 4 groupes

### A1. Temps

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| Temps de code total | somme de `temps_reel_min` dans `ia.csv` | ✅ |
| Temps passé / temps estimé (M2) | `temps_reel_min` / `estimation_min` (l'estimation se note **avant** de lancer l'agent) | ✅ |
| Temps de complétion par tâche | `temps_reel_min` (début de la tâche à l'ouverture de la PR) | ✅ |
| Temps de récupération après échec | ouverture → fermeture des issues `incident` | 🚀 |
| Temps de debug : détection d'un bug → correctif mergé | issue ou PR étiquetée `bug` → merge de la PR étiquetée `fix` (horodatages GitHub) ; le trailer `Corrige:` relie le correctif au commit fautif | 🔧 |
| Temps de génération IA : premier prompt → code mergé | début de la tâche (`tokens.py --since`) → date de merge de la PR (GitHub) | 🔧 |
| Productivité : fonctionnalités livrées / heures totales | fonctionnalités cochées dans la checklist du MVP / somme de `temps_reel_min` | 📋 |

### A2. Mesures quantitatives

**Volume et activité**

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| Nombre de lignes de code | git (`stats.py`, par origine) | ✅ |
| Nombre de commits par sprint | git → `stats.py` (aujourd'hui par personne et par origine ; découpage par sprint à ajouter) | 🔧 |
| Nombre de PR mergées par sprint | GitHub (PR) | 🔧 |
| Taille des PR (lignes ajoutées + supprimées) | GitHub (PR) | 🔧 |
| Nombre de fichiers source, fichiers par module, profondeur d'arborescence | script sur l'arborescence (`backend/` par couche, front) | 🔧 |
| Fichiers orphelins (importés par aucun autre fichier) | analyse des imports | 🔧 |

**Tests et intégration continue**

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| Nombre de tests unitaires / d'intégration | `pytest --collect-only` ; unitaires = `scheduling/` (Python pur), intégration = tests contre PostgreSQL | 🔧 |
| Taux de couverture (M7) | pytest-cov | 🔧 |
| Tests qui passent du premier coup | premier run CI de chaque PR | 🔧 |
| Taux de passage des tests au final | dernier run CI avant merge | 🔧 |
| Taux d'échec CI initial | premier run CI de chaque PR | 🔧 |

**Revue et acceptation**

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| Taux de première soumission acceptée | PR mergées sans demande de changement (GitHub) | 🔧 |
| Taux de rejet de PR | PR fermées sans merge (GitHub) | 🔧 |
| Nombre de PR rejetées ou avec retours | PR avec au moins une revue « changes requested » | 🔧 |
| Churn de reprise post-merge (lignes ajoutées + supprimées) | lignes modifiées après le merge sur les fichiers d'une PR ; côté IA, voir aussi la survie du code généré (B3) | 🔧 |

**Défauts, sécurité, documentation**

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| Taux de bugs en production | issues `bug` ouvertes après déploiement | 🚀 |
| Vulnérabilités par 1 000 LOC | bandit + SonarQube (code), pip-audit et `npm audit` (dépendances) | 🔧 |
| Nombre de secrets exposés | scan de l'historique git (outil à choisir, par exemple gitleaks) | 🔧 |
| Taux de dépendances ajoutées | diff de `requirements*.txt` et `package.json` par PR | 🔧 |
| Taux de documentation produite | PR qui touchent `docs/` ou un README ; densité de commentaires (SonarQube) | 🔧 |

**Usage de l'IA** (communes aux 4 groupes, mais au cœur de l'approche agentique)

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| Nombre de prompts par fonctionnalité | `tours` dans `ia.csv`, additionnés par fonctionnalité | ✅ |
| Nombre d'itérations generate → fix par tâche | `interventions` (corrections par re-prompt) + commits `IA: retouche` de la PR | ✅ |
| Nombre d'interventions humaines par tâche (M1) | `interventions` dans `ia.csv` | ✅ |

### A3. Dette technique (méthode SQALE, SonarQube)

| Métrique | Mesure au groupe 3 | État |
| :--- | :--- | :--- |
| SQALE index (minutes de remédiation) | SonarQube | 🔧 |
| SQALE debt ratio (M6) | SonarQube | 🔧 |
| SQALE rating (A à E) | SonarQube | 🔧 |
| Reliability rating (bugs) et Security rating (vulnérabilités) | SonarQube | 🔧 |
| Duplication de code (M8) | SonarQube | 🔧 |
| Compréhensibilité : complexité cognitive, densité de commentaires | SonarQube | 🔧 |

À noter : dans SonarQube, le *Reliability rating* porte sur les bugs et le *Security rating* sur les vulnérabilités ; le document commun les regroupe sous le premier. On relève les deux. SQALE ne mesure pas la dette d'architecture : pour le groupe 3, le respect des couches (`routers` → `repositories` → `models`) est vérifié à part (B4).

### A4. Qualitatif social et psychologique

Questionnaire commun aux 4 groupes, rempli par chaque membre en fin de sprint. 📋

- Plaisir à la réalisation du projet (échelle de 7 points, « Tout à fait d'accord » → « Pas du tout d'accord »).
- Estime de soi : échelle de Rosenberg adaptée (10 items notés de 1 à 4, items inversés : 5 − réponse ; 10-24 faible, 25-35 classique, 36-40 élevée).
- Confiance dans le code : « Je comprends le code que l'IA ou moi avons produit. »
- Apprentissage : « Je me sens progresser techniquement », « L'IA m'empêche d'apprendre », « L'IA m'aide à apprendre ».
- Collaboration d'équipe : facilité à relire le code des autres, répartition du travail perçue comme équitable.
- Relation à l'IA : « L'IA me fait gagner du temps », « L'IA génère du code que je ne comprends pas », « Je me sens superviseur plutôt que développeur ».

## Partie B — Métriques propres à l'agentique

Elles n'ont pas d'équivalent dans le groupe classique, ou n'y ont pas de sens : elles décrivent le travail de l'agent et de son superviseur.

### B1. Autonomie de l'agent

| Métrique | Source | État |
| :--- | :--- | :--- |
| Taux de réussite sans intervention : tâches menées à une PR acceptée sans aucune intervention humaine (M1) | `succes_sans_intervention` dans `ia.csv` | ✅ |
| Temps où l'agent travaille seul / temps total de la tâche | `duree_agent_min` (`tokens.py`) / `temps_reel_min` | ✅ |
| Temps de mise en place, de revue et de correction du code IA par l'humain (M3) | `temps_revue_min` dans `ia.csv` | ✅ |

### B2. Coût de l'agent

| Métrique | Source | État |
| :--- | :--- | :--- |
| Tours, tokens (entrée, cache relu, sortie) et coût en équivalent API, par tâche et par fonctionnalité | `ia.csv` (colonnes de `tokens.py`) | ✅ |
| Usage des sous-agents : nombre, modèle, part des tokens et du coût | `sous_agents`, `modele_sous_agents`, `cout_sous_agents_usd` | ✅ |
| Coût fixe de l'architecture agentique : temps et coût du module `infra-agent` (AGENTS.md, skills, sous-agents, hooks) | `ia.csv` → `stats.py` | ✅ |

### B3. Origine et devenir du code généré

| Métrique | Source | État |
| :--- | :--- | :--- |
| Commits et lignes par origine (généré, retouché, manuel) | trailers `IA:` → `stats.py` | ✅ |
| Taux de retouche : lignes retouchées / lignes générées (M4) | trailers `IA:` → `stats.py` | ✅ |
| Survie du code IA : part des lignes générées qui ne sont plus dans `HEAD` | `git blame` → `stats.py` | ✅ |
| Bugs par origine, pour 1 000 lignes (M5) | trailer `Corrige:` → `stats.py` | ✅ |
| Dette du code IA par rapport au code manuel | SonarQube, filtré par les commits `IA:` | 🔧 |

### B4. Pilotage de l'architecture agentique

| Métrique | Source | État |
| :--- | :--- | :--- |
| Respect des conventions par l'agent : imports interdits entre couches | import-linter | 🔧 |
| Respect des conventions par l'agent : fichiers > 600 lignes, fonctions de complexité > 10 (M8) | radon | 🔧 |
| Évolution de l'architecture agentique : modifications de `AGENTS.md`, des skills, sous-agents et hooks par sprint, avec leur raison | git + rétrospectives (`docs/retros/`) | 📋 |

## Partie C — Correspondance avec le plan de projet

| Plan | Métrique | Où |
| :--- | :--- | :--- |
| M1 | Interventions humaines, réussite sans intervention | A2 (usage de l'IA), B1 |
| M2 | Temps réel / temps estimé | A1 |
| M3 | Temps de mise en place, de revue et de correction du code IA | B1 |
| M4 | Taux de retouche | B3 |
| M5 | Défauts pour 1 000 lignes | B3 (par origine), A2 (bugs en production) |
| M6 | Ratio de dette technique | A3 |
| M7 | Couverture de tests et taux de mutation | A2 (couverture) ; mutation : ci-dessous |
| M8 | Complexité cyclomatique et duplication | A3 (duplication), B4 (complexité) |
| M9 | Qualité de la solution algorithmique, temps d'exécution | ci-dessous |
| M10 | Coopération via le changelog | ci-dessous |

Trois métriques du plan ne sont ni dans le socle commun ni propres à l'agentique. Elles restent suivies parce que le plan s'y engage :

| Métrique | Source | État |
| :--- | :--- | :--- |
| Taux de mutation (M7) | mutmut | 🔧 |
| Qualité de l'algorithme : contraintes dures violées (doit valoir 0), score des contraintes souples ; temps d'exécution selon la taille des données (M9) | script de benchmark | 🔧 |
| Coopération : délai de validation et taux d'acceptation (M10) | `docs/CHANGELOG-schema-api.md` | 📋 |

## Comment améliorer

Une rétrospective courte par sprint dans `docs/retros/sprint-N.md` :

1. Ce qui a marché
2. Ce qui a coincé (avec les chiffres du sprint : `python journal/stats.py`)
3. Ce qu'on change dans l'architecture agentique (prompts, skills, sous-agents, conventions)

Les rétros servent de matière première pour la partie « recul » du rapport : comment le processus a évolué et pourquoi.

## Sources du socle commun

Références retenues par le document commun, reprises telles quelles (à vérifier avant d'entrer dans `rapport/refs.bib`) :

- SPACE Framework, ACM Queue, 2021 — https://queue.acm.org/detail.cfm?id=3454124
- DORA Metrics — https://dora.dev/guides/dora-metrics-four-keys/
- METR, *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*, 2025 — https://metr.org/blog/2025-02-06-ai-and-open-source-dev/
- Harness, *State of Software Delivery 2025* — https://www.harness.io/state-of-software-delivery ; Stack Overflow Developer Survey 2025 — https://survey.stackoverflow.co/2025
- Chen & Stratton, *Artificial Intelligence in the Firm: Bottlenecks in Software Production*, 2026 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5131938
- Perera, Tempero, Tu & Blincoe, *A Systematic Mapping Study Exploring Quantification Approaches to Code, Design, and Architecture Technical Debt*, ACM TOSEM 33(7), 2024 — https://dl.acm.org/doi/10.1145/3675393
- *FeatureBench: Benchmarking Agentic Coding for Complex Feature Engineering*, 2026 — https://arxiv.org/abs/2602.10975
- *Do AI-Generated Pull Requests Get Rejected More? (Yes but Why?)*, 2026 — https://dl.acm.org/doi/10.1145/3793302.3793568
- *Where Do AI Coding Agents Fail? An Empirical Study of Agentic Pull Requests*, 2026 — https://dl.acm.org/doi/10.1145/3793302.3793579
- *Behind Agentic Pull Requests: An Empirical Study on Developer Interventions in AI Agent-Authored Pull Requests*, MSR 2026 — https://dl.acm.org/doi/full/10.1145/3793302.3793586
- *Understanding Security Risks of AI Agents' Dependency Updates*, 2026 — https://arxiv.org/html/2601.00205v1
- Meli, McNiece & Reaves, *How Bad Can It Git? Characterizing Secret Leakage in Public GitHub Repositories*, NDSS 2019 — https://www.ndss-symposium.org/ndss-paper/how-bad-can-it-git-characterizing-secret-leakage-in-public-github-repositories/
- Malaiya, Li, Bieman, Karcich & Skibbe, *The Relationship Between Test Coverage and Reliability* — https://www.cs.colostate.edu/~malaiya/p/li94coverage.pdf
- *A comprehensive review of agentic AI evaluation*, 2026 — https://link.springer.com/article/10.1007/s10462-026-11571-0
- SonarSource, *SQALE, the Ultimate Quality Model to Assess Technical Debt* ; Robredo Manero et al., *Evaluating Time-Dependent Methods and Seasonal Effects in Code Technical Debt Prediction*
- Questionnaire : https://www.sonarsource.com/blog/ai-coding-trust-gap/ , https://arxiv.org/pdf/2601.20245 , https://arxiv.org/pdf/2607.13196 , https://arxiv.org/pdf/2502.18658
