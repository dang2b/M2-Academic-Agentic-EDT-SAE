# AGENTS.md — SAE M2, Groupe 3 (emplois du temps, approche agentique)

Fork du starter commun aux 4 groupes : SIS/ERP éducatif, sous-projet B (emplois du temps). Nous sommes le groupe **agentique** : le plus de code possible produit par des agents, et chaque usage de l'IA est mesuré. Le groupe 2 travaille sur les mêmes objectifs en approche classique. L'intégration avec lui viendra plus tard, et chaque groupe a sa propre base.

## Fin de tâche : la ligne du journal IA

Le journal est une donnée centrale du rapport : une tâche n'est pas terminée tant que sa ligne n'est pas dans `journal/ia.csv`. C'est à l'agent d'y penser, sans attendre qu'on le lui demande :

1. Au début d'une tâche, noter l'heure (`date "+%Y-%m-%d %H:%M"`).
2. Une fois la tâche finie (PR ouverte, ou dernier commit poussé s'il n'y a pas de PR), **avant d'annoncer la fin**, lancer `python journal/tokens.py --since "<heure de début>"`.
3. Ajouter la ligne en fin de fichier, au format de `journal/README.md`, **sans attendre de validation** : colonnes recopiées de `tokens.py`, `temps_reel_min` compris (sa valeur `duree_min`, sans la remettre en doute) ; `interventions` comptées d'après la conversation, avec les messages comptés résumés dans `commentaire`. Ce que l'agent ne peut pas savoir (`estimation_min`, `temps_revue_min`) reste vide, jamais inventé : l'humain complète ou corrige après.
4. La commiter sur la branche de la tâche (`docs(journal): ...`, sans trailer) et la pousser sur la PR.

Si une nouvelle tâche commence dans la même conversation, faire d'abord la ligne de la précédente. Module `infra-agent` pour le travail sur l'architecture agentique elle-même.

## Commandes

```bash
docker compose up --build                 # API :8000 (/docs), Postgres :5432 (sae/sae/sae) ; migre la base et crée l'admin de démo
docker compose --profile tools up         # + Adminer :8080
docker compose exec backend pytest        # tests, sur une base <db>_test recréée à chaque lancement
docker compose exec backend alembic revision --autogenerate -m "<message>"   # nouvelle migration, à relire
docker compose down -v                    # SUPPRIME les données ; la base est recréée par les migrations au prochain up
typst compile rapport/<fichier>.typ       # documents pour l'enseignant
python journal/tokens.py --since "AAAA-MM-JJ HH:MM"   # tours/tokens/coût d'une tâche
python journal/stats.py                   # agrégation du journal et des trailers
```

- Pour ajouter une dépendance Python : l'ajouter dans `backend/requirements.txt` (`requirements-dev.txt` pour un outil de test), puis `docker compose up --build`.
- Pas encore de CI. Cible : GitHub Actions (pytest, couverture, mutmut, radon).

## Stack

FastAPI + PostgreSQL 16 (driver psycopg), SQLAlchemy 2.x, migrations Alembic, pytest. Configuration par variables d'environnement (`backend/config.py`). JWT + RBAC (pas encore implémenté). Docker compose. Front : React/Next.js + Tailwind + shadcn/ui (pas encore créé, géré par les DFS). Déploiement prévu, pas encore en place : sur push `main`, GitHub Actions construit les images, les pousse sur ghcr et les déploie sur un VPS (docker compose).

## Conventions de code

- Modulaire : un fichier de plus de 600 lignes se découpe, une fonction de complexité cyclomatique supérieure à 10 (radon : C ou pire) aussi. Un fichier = une responsabilité.
- Backend découpé par couche ; `GET /roles` est l'exemple complet à suivre (router, repository, schéma, test) :
  - `backend/routers/<domaine>.py` : HTTP seulement (validation, auth, codes de retour), aucun accès direct à la base ;
  - `backend/repositories/<domaine>.py` : tout l'accès à la base, via SQLAlchemy. Un repository ne commite jamais ;
  - `backend/models/<domaine>.py` : modèles SQLAlchemy, source de vérité du schéma. Un nouveau module s'importe dans `models/__init__.py`, sinon Alembic ne le voit pas ;
  - `backend/schemas/<domaine>.py` : modèles Pydantic, séparés en entrée (`XCreate`, `XUpdate`) et en sortie (`XOut`) ;
  - `backend/scheduling/` : algorithmes de génération en Python pur, sans import de FastAPI ni de SQLAlchemy. Ils prennent des données en mémoire et rendent une solution, ce qui permet de les tester et de les benchmarker sans base.
- La session SQLAlchemy et l'utilisateur courant sont injectés par `Depends`, jamais lus dans une variable globale ni décodés à la main dans chaque route.
- Une écriture sur plusieurs tables (une séance avec ses `session_teachers` et `session_groups`) se fait en une seule transaction, contrôle de conflits compris : le router appelle `session.commit()` une seule fois, après tous les appels aux repositories.
- Chaque route déclare son `response_model` : c'est lui qui empêche de renvoyer `password_hash` ou des champs internes.
- Routes de liste : pagination par `PageDep` (`backend/pagination.py`), et jamais une requête par ligne (N+1). Les `relationship()` se déclarent avec `lazy="raise"` et se chargent explicitement (`selectinload`, `joinedload`) : un accès à une relation non chargée lève une erreur au lieu de lancer une requête cachée.
- Codes d'erreur :
  - 409 avec le détail du conflit (ressource et séance en cause) ;
  - 403 si le rôle manque ;
  - 404 si la ressource n'existe pas, et aussi si elle appartient à quelqu'un d'autre (les notes perso par exemple), pour ne pas révéler son existence.
- Dates toujours avec fuseau (`datetime.now(UTC)`), jamais de `datetime` naïf.
- Tests contre le vrai PostgreSQL du compose, sans mocker la base : fixtures `client` et `session` de `backend/tests/conftest.py`, chaque test tourne dans une transaction annulée à la fin. Tout correctif de bug ajoute le test qui l'aurait détecté.
- Front : les types TypeScript de l'API sont générés depuis `/openapi.json`, jamais écrits à la main.
- Tout changement de schéma passe par une migration Alembic, jamais par une modification directe en base. Une migration `--autogenerate` se relit toujours : elle prend un renommage pour une suppression suivie d'un ajout (perte de données) et rate certaines contraintes ou extensions. Chaque migration a un `downgrade` qui fonctionne, et une migration de données n'importe pas les modèles (copie figée avec `sa.table`, voir `0002`). `tests/test_migrations.py` échoue si les modèles et les migrations divergent.
- Le compte admin de démo vient de `backend/seed.py`, lancé par le compose de dev seulement. Les données dont toute instance a besoin (rôles, types de séance) vont dans une migration.

## Où trouver quoi

| Besoin | Fichier |
| :--- | :--- |
| Schéma BDD (source de vérité) | `backend/models/`, historique dans `backend/migrations/versions/` |
| Routes et modèle de données du socle | `docs/infos.md` |
| Fonctionnalités, MVP, contraintes, algos du groupe 3 | `docs/Document de cadrage Groupes EDT.md` |
| Cadrage de l'enseignant | `docs/document_cadrage_M2_2026_2027_projet_SAE.md` |
| Plan complet des 4 groupes | `docs/Plan_Projet_M2.md` : images base64, **lire par plage de lignes** (groupe 3 : l. 247-483) |
| Métriques et rétrospectives | `docs/metriques.md`, `docs/retros/sprint-N.md` |
| Journal IA et trailers | `journal/README.md` |

## Règles

### Toujours

- Avant toute modification, check état des branches, créer une branche `<type>/<nom>` (`feature/`, `fix/`, `docs/`…) si pas déjà fait, puis ouvrir une PR vers `dev`. La PR `dev` → `main` se fait seulement sur demande.
- Toute modification du schéma (migration) ou du contrat d'API va dans le même commit/PR qu'une ligne de `docs/CHANGELOG-schema-api.md` (statut `proposé`).
- Langue : titres et descriptions de PR, et documentation (`docs/`, README) en français ; code, identifiants, commentaires, messages de commit et noms de branches en anglais. Les clés des trailers (`IA: genere`, `IA: retouche`, `Corrige:`) restent telles quelles, car `journal/stats.py` les lit.
- Commits en Conventional Commits (`.gitmessage`) avec le trailer d'origine : `IA: genere` (code généré commité tel quel), `IA: retouche` (corrections à la main, commit séparé), aucun trailer pour le code écrit à la main. Un fix de bug porte `Corrige: <sha du commit fautif>`.
- Sécurité, avant d'écrire du code et en relisant le diff :
  - requêtes via SQLAlchemy ; du SQL brut seulement avec `text()` et des paramètres liés, jamais de f-string ni de concaténation ;
  - chaque route vérifie le JWT et le rôle requis (RBAC), et un utilisateur n'accède qu'à ses propres données (notes, préférences, disponibilités) ;
  - entrées validées par des modèles Pydantic, imports CSV compris ;
  - mots de passe hachés en bcrypt ; aucun secret, token ou mot de passe dans le code, les logs ou les réponses d'API.
- Une ligne par tâche dans `journal/ia.csv`, proposée par l'agent dès la fin de la tâche (voir « Fin de tâche » en haut de ce fichier).
- Les scripts de `journal/` doivent tolérer les données manquantes : les conventions ne sont pas suivies par tout le monde, et une partie de l'équipe n'a pas Claude Code.
- Documents pour l'enseignant : dans `rapport/`, en Typst, avec le gabarit `rapport/template.typ` et la bibliographie `rapport/refs.bib` (IEEE). Chaque source est vérifiée, jamais inventée. L'enseignant note le recul critique plus que le résultat, et le rapport compare deux manières d'utiliser l'IA (classique et agentique), pas l'humain contre l'IA.

### Algorithmes de génération (glouton/coloration de graphe/recuit simulé/...)

- Ne pas livrer un algorithme que l'équipe ne comprend pas : concevoir avec l'humain, et documenter la complexité, les limites et les alternatives.
- Garder l'historique des versions de chaque algorithme.
- L'application n'appelle pas de LLM pour générer les emplois du temps.

### Demander avant

- `docker compose down -v`, ou toute autre commande qui supprime des données.
- Ajouter une dépendance.
- Modifier ce qui est partagé : schéma ou routes du socle (portée `commun`), contrat d'API EDT commun avec le groupe 2 (portée `projet B`).

### Jamais

- Committer `.env` ou un secret.
- Pousser directement sur `main` ou `dev`.

## Équipe

- DFS : Clément (référent API), Simon, Thibaut. Auth, API, front.
- DE : Daniel (référent Data), Thomas. BDD, import CSV, génération des emplois du temps, générateur de jeux de données (sert aussi au benchmark M9).

Un référent coordonne, mais il n'est pas le seul à toucher à son domaine. Les validations du changelog se font entre ces personnes.
