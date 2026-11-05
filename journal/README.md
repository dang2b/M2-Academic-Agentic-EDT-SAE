# Journal d'usage de l'IA

Sert à mesurer :
- les métriques 1 à 4 (interventions humaines, temps réel/estimé, temps de revue/correction, taux de retouche) ;
- la consommation par tâche : tours, tokens, coût ;
- le coût fixe de l'architecture agentique ;
- les bugs venant du code généré par rapport au code écrit à la main.

## 1. Une ligne par tâche dans `ia.csv`

| Colonne | Contenu |
| :--- | :--- |
| `date` | `AAAA-MM-JJ` |
| `auteur` | prénom (ex. `daniel`) |
| `modele` | modèle principal, ex. `claude-opus-5-5`. Donné par `tokens.py` : celui qui a produit le plus de tokens de sortie (les autres vont dans `commentaire`). Vide si `outil = aucun` |
| `tache` | n° de PR (ou d'issue) puis courte description, ex. `#12 routes /auth` |
| `module` | `auth`, `api`, `bdd`, `algo`, `front`, `ci`… et **`infra-agent`** pour la mise en place de l'architecture agentique (AGENTS.md, skills, sous-agents, hooks) |
| `outil` | `claude-code`, `copilot`, `chatgpt`, `cursor`… ou `aucun` |
| `estimation_min` | temps estimé **avant** de commencer |
| `temps_reel_min` | du début du travail à l'ouverture de la PR ; **inclut** l'écriture des prompts, la revue et les corrections |
| `temps_revue_min` | relecture du code généré **par vous** (pas par une IA), et corrections qui en découlent, à la main ou par re-prompt |
| `interventions` | nombre d'interventions humaines (voir définition ci-dessous) |
| `succes_sans_intervention` | `oui` si `interventions = 0` et que la tâche aboutit à une PR, sinon `non` (tâche abandonnée comprise). Passer à `non` si la PR est refusée ensuite |
| `tours` | nombre de prompts envoyés (donné par `tokens.py`) |
| `tokens_entree` | tokens d'entrée hors lecture de cache (donné par `tokens.py`) |
| `tokens_cache_lu` | tokens relus depuis le cache : contexte répété à chaque tour (donné par `tokens.py`) |
| `tokens_sortie` | tokens générés par le modèle (donné par `tokens.py`) |
| `cout_usd` | coût équivalent au tarif API, en $ (donné par `tokens.py`) |
| `commentaire` | ce qui a coincé, sans virgule ou entre guillemets |

Exemple :

```csv
2026-11-05,daniel,claude-sonnet-5-5,#12 routes /auth (login + refresh),auth,claude-code,60,95,30,3,non,10,148076,1744442,28482,1.89,"bcrypt oublié, refresh token mal expiré"
```

Ajoutez vos lignes **en fin de fichier** pour limiter les conflits git.

### Définitions

- **Tâche** : une PR (ou une issue). Si elle s'étale sur plusieurs sessions, lancer `tokens.py` sur chaque plage et additionner.
- **Intervention** : compte +1 pour chaque message qui corrige, réoriente ou refuse ce que l'agent a produit ou s'apprête à faire, et +1 pour chaque retouche du code généré faite à la main. Ne comptent pas : répondre à une question de l'agent, valider (« oui », « go »), ajouter une demande nouvelle qui ne remet pas en cause le travail déjà fait.
  - Compte : « non, on déploie avec GitHub Actions vers notre VPS, pas avec Caddy » (correction).
  - Ne compte pas : « oui, applique » (validation), « ajoute aussi l'export iCal » (nouvelle demande).

### Tours, tokens, coût

Notez l'heure de début de la tâche. À la fin, lancez :

```bash
python journal/tokens.py --since "2026-11-05 14:00"   # ou sans argument : dernière session
```

La dernière ligne affichée se colle telle quelle dans les colonnes `tours` à `cout_usd`, et la ligne `modele` donne la colonne du même nom. Les commandes locales (`/model`, `/effort`…) ne comptent pas comme des tours : rien n'est envoyé au modèle. Le script lit les transcripts Claude Code locaux, sous-agents compris : chacun le lance sur sa propre machine.

Le script affiche aussi des durées, calculées à partir des horodatages du transcript :
- `debut`, `fin`, `duree_min` : du premier au dernier horodatage de la plage. C'est la base de `temps_reel_min`, à compléter avec le temps passé hors de Claude Code (IDE, GitHub, réunions).
- `duree_agent_min` : temps pendant lequel l'agent travaillait, d'après la durée de chaque tour terminé enregistrée par Claude Code. La différence avec `duree_min`, c'est le temps passé côté humain (lecture, réflexion, prompts).

`temps_revue_min` reste à remplir à la main : la relecture et les corrections faites hors de Claude Code n'apparaissent dans aucun transcript.

Une case vide n'est pas un zéro : `stats.py` l'exclut des moyennes et affiche `non renseigné` si aucune ligne n'a la valeur.

Le coût est calculé au tarif API (grille dans `PRICES`, en tête du script), même si vous êtes sur un abonnement : c'est ce que la tâche aurait coûté en API.

**Sans Claude Code** : comptez `tours` à la main (nombre de prompts envoyés), notez le modèle si l'outil l'affiche, et laissez les colonnes de tokens et de coût vides si l'outil ne les donne pas. Le reste du journal s'applique à tout le monde.

## 2. Trailers dans les commits

**Origine du code**, trailer `IA:` :
- Code généré par l'agent, commité **tel quel** : `IA: genere`
- Corrections faites à la main ensuite, dans un commit **séparé** : `IA: retouche`
- Code écrit à la main sans IA : pas de trailer

**Correction de bug**, trailer `Corrige:` avec le hash du commit qui a introduit le bug (`git blame` ou `git log -L` pour le retrouver) :

```bash
git commit -m "feat(auth): login JWT" --trailer "IA: genere"
git commit -m "fix(auth): expiration du refresh token" --trailer "IA: retouche"
git commit -m "fix(auth): token accepté après logout" --trailer "Corrige: 3f2a91c"
```

Le script en déduit :
- **commits par auteur et par origine** ;
- **taux de retouche** = lignes de code `retouche` / lignes de code `genere` ;
- **code IA modifié ou supprimé** = part des lignes `genere` qui ne sont plus dans `HEAD` (via `git blame`) ;
- **bugs par origine** : nombre de bugs et bugs pour 1000 lignes, pour le code généré, retouché et manuel.

Seuls les fichiers de code sont comptés (`.py`, `.ts`, `.tsx`, `.js`, `.sql`, `.css`, `.html`, `.yml`, Dockerfile), pas la doc ni le CSV.

## 3. Calcul

```bash
python journal/stats.py
```

Les métriques 5 à 8 (défauts, dette, couverture/mutation, complexité/duplication) viendront de la CI, pas de ce journal.
