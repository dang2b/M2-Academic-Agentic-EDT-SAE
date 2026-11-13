# Reste à faire — Groupe 3

Échéances : soutenance en janvier 2027, rapport une semaine avant (dates exactes à confirmer).

## Décisions à prendre

- [ ] Contrat d'API EDT avec le groupe 2 : séances, génération, disponibilités, vues. Rien n'est défini au-delà du socle (`docs/infos.md`).
- [ ] Base partagée et déploiement final : où, qui héberge (« décidé avant la phase de dev » selon le cadrage).
- [ ] Données manquantes pour le MVP : jours fériés, salles spécialisées TP (`rooms.room_type` existe, mais rien n'indique quel type de séance ou quelle matière l'exige). Les créneaux horaires sont tranchés (voir Génération).
- [ ] Écarts de schéma déjà listés dans `CHANGELOG-schema-api.md`.
- [x] Valider les 2 lignes du changelog (passage à Alembic, pagination de `GET /roles`) : acceptées par Daniel le 2026-11-13.
- [ ] Quand utiliser l'ORM, quand utiliser du SQL brut (#9).
- [ ] Organisation : sprints, tableau GitHub Projects, rétros dans `docs/retros/`.

## Backend (MVP)

- [ ] Auth JWT (login, refresh, logout), `get_current_user`, RBAC.
- [ ] Erreurs communes 403 / 404 / 409.
- [ ] CRUD du socle : users, rôles, années, semestres, filières, matières, volumes, groupes, inscriptions.
- [ ] Salles et indisponibilités, disponibilités et préférences des profs.
- [ ] Séances : création, modification, suppression avec détection de conflits (salle, prof, groupe, capacité), en une transaction.
- [ ] Import CSV (salles, groupes, matières, profs).
- [ ] Vues filtrées : groupe, prof, salle ; semaine, jour.
- Hors MVP : notes perso, export iCal, notifications, historique des modifications, recherche.

## Génération (DE)

Décisions prises (détail dans `rapport/algorithme.typ`) : du lundi au vendredi, 8 h 30–12 h et 13 h 30–18 h 30, pas de 30 min, cours de 1 h ou 1 h 30 ; génération semaine par semaine ; trous pénalisés en priorité (1 point si moins d'une heure, 3 par heure sinon) ; pas de solveur externe (OR-Tools) pour l'instant.

Données :
- [ ] Table des **affectations d'enseignement** (prof, matière, type de séance, groupe, durée), avec sa migration et sa ligne de changelog : entrée principale de la génération.
- [ ] Table des jours fériés, avec sa migration.
- [ ] Répartition des volumes horaires du semestre en séances à placer, semaine par semaine, jours fériés exclus.
- [ ] Générateur de jeux de données (petit, moyen, grand), écrits en instances JSON dans `backend/scheduling/instances/`.
- [ ] Passerelle base ↔ modèle : charger la base dans `scheduling/`, réécrire la solution sous forme de séances.

Algorithmes (`backend/scheduling/`, Python pur) :
- [x] Modèle du problème en mémoire, graphe des conflits (#17).
- [x] Évaluateur commun : contraintes dures par type, séances non placées, score souple (#17).
- [x] Banc de comparaison : interface commune, `random@1` comme référence, résultats en CSV (#17).
- [x] V1 glouton `greedy@1` (#23).
- [ ] V2 coloration de graphe `dsatur@1`.
- [ ] V3 recuit simulé `annealing@1`.
- [ ] Piste : `greedy@2`, créneau le moins chargé plutôt que le premier (corrige le déséquilibre de la V1).
- [ ] Benchmark M9 sur les instances générées : qualité et temps selon la taille.
- Questions restantes :
  - Examens, rattrapages, changements en cours de semestre : générés ou saisis à la main ?
  - Correction manuelle après génération : comment garantir qu'elle ne casse pas les contraintes ?

## Front (DFS)

- [ ] Choix du framework, justifié.
- [ ] Types TypeScript générés depuis `/openapi.json`.
- [ ] Écrans :
  - login ;
  - calendrier semaine/jour avec couleurs par type ;
  - multi-vues ;
  - détail d'un créneau ;
  - écrans admin : séances, import, génération.

## Qualité, CI, déploiement

- [ ] CI GitHub Actions : pytest et couverture, radon, mutmut, bandit, pip-audit (voir `metriques.md`).
- [ ] SonarCloud : dette, duplication, code IA comparé au code manuel.
- [ ] Déploiement (CD sur push `main`) :
  - [x] Secrets du dépôt : `GHCR_USERNAME`, `GHCR_PAT`, `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`. Testés le 2026-11-05 par un workflow temporaire (connexion ghcr et SSH en vérification stricte).
  - [ ] Workflow `.github/workflows/deploy.yml` sur push `main` : build de l'image, push sur ghcr, puis en SSH sur le VPS `docker compose pull && docker compose up -d`.
  - [ ] Image construite pour `linux/arm64` : le VPS est en `aarch64` (Oracle Ampere A1), alors que les runners GitHub par défaut sont en x86_64. Prendre le runner `ubuntu-24.04-arm` ou `docker buildx --platform linux/arm64`.
  - [ ] `docker-compose` de production : image ghcr, pas de port Postgres exposé, pas de seed ni de compte de démo, pas de `--reload` ni de code monté. API sur `127.0.0.1:8000` (port libre sur le VPS).
  - [ ] Préparer le VPS : dossier du projet, `.env` hors GitHub (`POSTGRES_PASSWORD` fort, `CORS_ORIGINS`, plus tard le secret JWT), `docker login ghcr.io` si le package est privé.
  - [ ] Package ghcr (`ghcr.io/dang2b/...`) public, ou lié au dépôt avec héritage des droits : sinon le `GHCR_PAT` de Thomas ne peut pas le télécharger. À vérifier après le premier push.
  - [ ] Vhost nginx (déjà installé sur l'hôte) vers `127.0.0.1:8000`, nom de domaine, HTTPS.
  - [x] Protection de `main` et `dev` (ruleset GitHub : PR obligatoire, pas de force push ni de suppression), mise en place le 2026-11-06.
  - [ ] Tests obligatoires avant le déploiement.
  - [ ] Sauvegardes de la base (`pg_dump` planifié).
- [ ] Tests e2e, charge (k6/locust), Lighthouse, questionnaire SUS.

## Mesure et architecture agentique

- [ ] Une ligne de journal par tâche, avec l'estimation notée **avant** de commencer.
- [ ] `tokens.py` pour les autres outils, dont OpenCode (#8).
- [ ] Formaliser l'architecture agentique (`rapport/architecture-agentique.typ`) :
  - [x] socle commun, configurations de Daniel (#16) et de Thomas (#20) ;
  - [ ] sections de Clément, Simon et Thibaut ;
  - [ ] mesurer ce qu'apportent sous-agents, skills et hooks (coût fixe `infra-agent`).
- [ ] Une rétro par sprint.

## Rapport et soutenance

- [x] État de l'art (#3), justification des choix (#18), modélisation et historique des algorithmes commencés (#24), dans `rapport/`.
- [x] `rapport/etat-de-l-art.typ` cite `AGENTS.md` (et non plus `CLAUDE.md`).
- [ ] Comparaison avec le groupe 2 : quelles métriques communes, et leurs données sont-elles comparables (même format de journal) ?
- [ ] Sujets proposés dans l'issue #5 :
  - confidentialité et rétention des données envoyées aux IA ;
  - écologie de l'usage de l'IA ;
  - éthique de l'application.
- [ ] Partie algorithmique : compléter `rapport/algorithme.typ` à chaque version, avec les résultats du benchmark sur les instances générées.
