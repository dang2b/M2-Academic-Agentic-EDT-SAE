# Changelog du schéma de données et du contrat d'API

Toute modification du schéma (modèles et migrations Alembic) ou du contrat d'API passe par une ligne ici. Sert à tracer la coopération (métrique M10 : délai de validation, taux d'acceptation).

- **Statut** : `proposé`, `accepté`, `refusé`
- **Portée** : `groupe 3` (notre fork uniquement), `projet B` (avec le groupe 2), `commun` (les 4 groupes)
- **Délai** : jours entre la proposition et la décision

| Date proposition | Proposé par | Portée | Type | Changement | Raison | Validé par | Date décision | Statut |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-11-05 | Thomas | groupe 3 | schéma | `db/init.sql` remplacé par des modèles SQLAlchemy et des migrations Alembic (`0001` schéma, `0002` rôles et types de séance). Schéma identique (`pg_dump` comparé). Le compte admin de démo passe dans `backend/seed.py`, en local seulement | Faire évoluer le schéma sans recréer la base, et ne pas créer d'admin `admin1234` en production | | | proposé |
| 2026-11-05 | Thomas | groupe 3 | API | `GET /roles` accepte `limit` (1 à 200, défaut 50) et `offset` (défaut 0). Réponse inchangée | Convention de pagination des routes de liste | | | proposé |

## Écarts connus à arbitrer

Écarts entre le schéma (`backend/models/`) et le plan du groupe 3, à passer en ligne `proposé` ci-dessus quand on les traite :
- `calendar_syncs` : le plan prévoit `external_calendar_id` et `sync_token`.
- `semesters` : le plan n'a pas de dates.
- `audit_logs` : absent du plan.
