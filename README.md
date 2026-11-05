# SAE M2 — Emplois du temps, Groupe 3 (agentique)

Module de gestion des emplois du temps d'un SIS/ERP éducatif (sous-projet B de la SAE M2 DFS & DE, 2026-2027).

Nous sommes le groupe **agentique** : le code est produit autant que possible par des agents IA, sous contrôle humain, et chaque usage de l'IA est mesuré (voir [`journal/`](journal/README.md)). Le groupe 2 développe le même module en approche classique ; la comparaison des deux approches fait partie du rendu.

Ce dépôt est notre fork du starter commun aux 4 groupes (même schéma de base, même socle d'API).

## Équipe

| Nom | Parcours | Rôle |
| :--- | :--- | :--- |
| Daniel GUERRA | DE | Référent Data : BDD, import CSV, génération des emplois du temps |
| Thomas SANNA | DE | BDD, import CSV, génération des emplois du temps |
| Clément LORIEAU | DFS | Référent API : auth, API, front |
| Simon COSSAIS | DFS | Auth, API, front |
| Thibaut RENAUD | DFS | Auth, API, front |

## Lancer

```bash
docker compose up --build
```

- API : http://localhost:8000, documentation interactive : http://localhost:8000/docs
- Postgres : `localhost:5432`, utilisateur / mot de passe / base : `sae` / `sae` / `sae`
- Adminer (facultatif) : `docker compose --profile tools up`, puis http://localhost:8080

Si un port est déjà pris, copiez `.env.example` en `.env` et changez `POSTGRES_PORT` ou `API_PORT`.

### Base de données

Le schéma est défini par les modèles SQLAlchemy (`backend/models/`) et appliqué par les migrations Alembic (`backend/migrations/versions/`). Au démarrage, le backend applique les migrations en attente (`alembic upgrade head`) : il n'y a pas besoin de recréer la base après une modification du schéma.

Pour modifier le schéma :

```bash
# 1. modifier le modèle dans backend/models/, puis générer la migration :
docker compose exec backend alembic revision --autogenerate -m "add rooms.accessible"
# 2. relire le fichier créé dans backend/migrations/versions/ (renommages, contraintes, downgrade)
# 3. l'appliquer (ou redémarrer le backend) :
docker compose exec backend alembic upgrade head
```

Données présentes après le démarrage :
- rôles : `ADMIN`, `MANAGER`, `TEACHER`, `STUDENT` (migration `0002`)
- types de séance : `CM`, `TD`, `TP`, `EXAM`, avec leurs couleurs (migration `0002`)
- un compte admin de démo : `admin@example.com` / `admin1234`, mot de passe haché en bcrypt. Il est créé par `backend/seed.py`, en local seulement. On peut le changer avec `DEMO_ADMIN_EMAIL` et `DEMO_ADMIN_PASSWORD` dans `.env`.

Pour repartir d'une base vide : `docker compose down -v` (supprime les données), puis `docker compose up`.

### Backend

Le code est rechargé automatiquement à chaque sauvegarde. Pour ajouter une dépendance Python : l'ajouter dans `backend/requirements.txt` (ou `requirements-dev.txt` pour un outil de test), puis `docker compose up --build`.

Tests, contre le PostgreSQL du compose (une base `sae_test` est recréée à chaque lancement, la base de dev n'est pas touchée) :

```bash
docker compose exec backend pytest
```

## Organisation du dépôt

```
AGENTS.md          consignes pour les agents IA (et conventions de code)
backend/           API FastAPI
  main.py          création de l'application, montage des routers
  routers/         HTTP : validation, codes de retour
  repositories/    accès à la base (SQLAlchemy)
  schemas/         modèles Pydantic d'entrée et de sortie
  models/          modèles SQLAlchemy : schéma de la base (source de vérité)
  migrations/      migrations Alembic
  tests/           tests pytest
docs/              cadrage, spécification, métriques, changelog du schéma et de l'API
journal/           journal d'usage de l'IA et scripts de métriques
rapport/           documents pour l'enseignant (Typst)
```

## Travailler sur le projet

- **Branches** : `feature/<nom>`, `fix/<nom>` ou `docs/<nom>`, puis PR vers `dev`. `main` ne reçoit que des PR depuis `dev`.
- **Commits** : Conventional Commits en anglais, avec le trailer d'origine du code (`IA: genere`, `IA: retouche`, rien pour du code écrit à la main). Activez le modèle : `git config commit.template .gitmessage`.
- **Schéma et API** : toute modification passe par une ligne dans [`docs/CHANGELOG-schema-api.md`](docs/CHANGELOG-schema-api.md).
- **Journal** : une ligne par tâche dans `journal/ia.csv`, mode d'emploi dans [`journal/README.md`](journal/README.md).
- **Agents IA** : ils lisent [`AGENTS.md`](AGENTS.md), qui contient les règles du projet (commandes, conventions de code, sécurité, limites).
