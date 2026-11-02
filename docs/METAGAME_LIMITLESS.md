# Métagame Limitless — fondation PM-0005B, reprise durable R2

## Portée

PokeMind conserve localement de petits instantanés des endpoints publics de la
**Limitless Tournament Platform**. Ils décrivent certains tournois gérés sur cette
plateforme; ils ne représentent ni tous les événements physiques, ni une autorité de
légalité, ni le rendement attendu du deck du joueur. `www.limitlesstcg.com` et
`labs.limitlesstcg.com` ne sont pas scrappés.

Les commandes sont manuelles. Aucun service résident, webhook, planificateur, compte,
clé API ou endpoint `/games/{id}/decks` n'est utilisé.

## Commandes

```powershell
python -m pokemind meta sync --dry-run --json
python -m pokemind meta sync --mode discover --max-requests 8 --max-tournaments 2 --format standard --platform PTCGL --online true --json
python -m pokemind meta sync --mode refresh --max-requests 8 --max-tournaments 2 --format standard --platform PTCGL --online true --json
python -m pokemind meta status --json
python -m pokemind meta tournaments --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind meta archetypes --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind meta coverage --format standard --platform PTCGL --online true --since 2026-01-01 --json
python -m pokemind meta matchups --archetype ID-PUBLIE --min-sample 5 --format standard --platform PTCGL --online true --since 2026-01-01 --json
```

`--dry-run` ne crée pas la base, ne la migre pas et ne contacte pas le réseau. Une
vraie synchronisation exige deux budgets explicites. Chaque tentative et retry compte
dans `--max-requests`. Le mode par défaut `discover` conserve un scope distinct par
jeu, format, plateforme et valeur `online`. Une exclusion terminale n'est réutilisée
que dans ce même contexte; les anciennes exclusions R1 `tournament:ID`, dépourvues de
contexte, ne sont jamais une preuve universelle. Un snapshot complet reste globalement
identifié par son ID public.

La découverte conserve aussi, dans `metadata`, un checkpoint JSON scoped : prochaine
page, horizon maximal observé et page inachevée éventuelle. Chaque nouvelle session
relit la tête puis une page de chevauchement avant de reprendre en profondeur. Si le
budget coupe le traitement d'un candidat, la page est reprise directement à la session
suivante; elle n'est avancée qu'après traitement complet. Une frontière vide ou
partielle est revisitée au lieu de remettre le curseur à 1. La sortie JSON expose
`discovery.scope`, `start_page`, `next_page`, `pending_page`, `pages_requested` et
`horizon_page`.

`--max-tournaments` compte les imports réussis : un candidat privé, incompatible ou
annulé ne bloque donc pas le candidat suivant. Les pages Limitless ne forment pas un
instantané atomique. Tête, chevauchement, checkpoint, déduplication et revisite de la
frontière réduisent les omissions lors d'insertions ou déplacements, sans garantir
l'exhaustivité globale.

`--mode refresh` est la voie qui revalide volontairement les snapshots existants et
les exclusions scoped, du plus ancien au plus récent, par petit lot. Cela permet de
recontrôler manuellement un tournoi dont la source a changé sans créer une boucle de
GET en mode découverte. Une unité tournoi n'est remplacée qu'après
validation de `details`, `standings` et `pairings`. Si `details` devient privé ou
incompatible, aucun classement/appariement n'est demandé et l'ancien snapshot passe à
`partial` : il sort des agrégats courants, mais son historique n'est pas supprimé. Un
échec réseau conserve également le dernier état sain hors ligne.

`details` est toujours validé avant `standings` et `pairings`. Seuls les événements
PTCG, format/plateforme/online demandés, publics et non annulés continuent. Un statut
fournisseur non documenté n'est pas transformé en preuve de tournoi terminé.

## Modèle local et confidentialité

Le schéma SQLite 7 est additif et sauvegarde une base existante par
`sqlite3.backup()` avant migration. Il contient :

- jeu, formats et plateformes publiés par `/games`;
- tournoi public PTCG avec date UTC, format, plateforme, `isOnline`, phases et modes;
- place, fiche W/L/T et archétype seulement quand `standing.deck.id` est publié;
- match, phase, ronde, table/label, issue et motif d'exclusion;
- URL, date de récupération, SHA-256 d'instantané et état de synchronisation.

R2 ne change pas ce schéma : les nouveaux scopes utilisent `meta_sync_state` et les
checkpoints utilisent la table `metadata` existante. Les lignes historiques non
scoppées restent intactes, mais ne sont plus interprétées comme exclusions globales.

Le pseudo/ID participant est transformé en HMAC avec une clé aléatoire locale et le
tournoi dans le message. La même personne produit donc une référence différente dans
deux tournois. Nom, pays, pseudo, identifiant PTCGL et decklist ne sont pas conservés.
La clé et toutes les données réseau demeurent dans `data/local/`, ignoré par Git.

Le retraitement remplace transactionnellement placements et matchs du tournoi. La clé
de match inclut tournoi, phase, ronde, table/label et paire de participants triée : un
appariement inversé ne crée pas un doublon et une correction fournisseur recalcule les
statistiques.

Le client partage une allowlist exacte entre requête initiale, destination de
redirection et URL finale : `/api/games`, `/api/tournaments` et les seuls sous-chemins
`details`, `standings`, `pairings`. Schéma non HTTPS, autre hôte, credentials,
fragment, segment inattendu et `/api/games/{id}/decks` sont refusés. Les en-têtes
`RateLimit` et `X-RateLimit-Remaining` ne sont utilisés que s'ils sont parsables; un
reste explicite de zéro bloque tout GET additionnel de l'invocation. Un en-tête absent
ou malformé ne crée pas une politique fictive permanente. Un GET suivi par
redirection consomme lui aussi une unité du budget avant transmission.

## Règles descriptives

Chaque consultation fixe jeu `PTCG`, format, plateforme, `online`, date minimale,
visibilité publique et instantané complet. `PTCGL` et `isOnline` restent deux filtres
distincts. Les formats personnalisés, tournois privés/non listés, annulés explicitement
ou sans classement sont exclus.

Un archétype absent est `unknown`; PokeMind ne le déduit ni d'une carte, ni d'une
decklist, ni de TCGdex. La fraction classifiée, le nombre de placements et le nombre de
tournois sont toujours exposés.

`meta coverage` sépare les tournois publics du contexte, snapshots `complete` et
`partial`, statuts fournisseur non interprétés, période, dernière récupération,
placements classifiés, matchs admissibles et réellement classifiables, exclusions,
phases et BO1/BO3/BO5. Chaque ratio contient son numérateur et son dénominateur; avec
un dénominateur nul, le ratio vaut `null`. Cette commande ne calcule aucun winrate.

Un matchup compte une observation par **match publié**, séparée par type de phase et
BO1/BO3/BO5. Les deux participants doivent appartenir au même tournoi, être présents
au classement et avoir un archétype publié; le gagnant doit être l'un des deux ou `0`
pour un nul. Bye, perte automatique ambiguë, double perte, gagnant incohérent et
archétype absent restent exclus et comptés par motif.

Le dictionnaire `excluded` de `meta matchups` décrit toutes les exclusions dans
l'ensemble des tournois filtrés, et non uniquement les matchs où l'archétype demandé
est présent; `excluded_scope` rend ce périmètre explicite.

En dessous de `--min-sample`, aucun taux ni intervalle n'est affiché. Au-dessus, la
sortie fournit W/L/T, `n`, tournois, fraction observée de victoires et intervalle de
Wilson à 95 %. Cela demeure une estimation descriptive, sensible à la sélection des
tournois, aux top cuts, aux listes/archétypes manquants, aux rotations et aux modes de
match.

## État réel au 2026-10-12 UTC

L'essai manuel PM-0005B a utilisé exactement 5 GET et importé un tournoi public
Standard PTCGL : 5 placements, 16 appariements et 9 matchs admissibles. Aucun archétype
n'était publié (`0/5` classifié), donc aucune statistique de matchup réelle n'a été
fabriquée. La réponse exposait une politique de quota de 50 requêtes par fenêtre de
5 minutes; cette observation n'est pas une garantie contractuelle et le client suit
toujours les en-têtes reçus et son budget plus strict.

Audit de source : `docs/PM-0005B_SOURCE_AUDIT.md`. Preuves synthétiques des correctifs :
`docs/PM-0005B-R1_AUDIT.md` et `docs/PM-0005B-R2_AUDIT.md`.

Au 2026-10-13, aucune documentation d'API publique ni condition d'automatisation de
Trainer Hill n'a été vérifiée. L'intégration reste `BLOCKED_WITH_REASON`; PokeMind ne
scrape ni l'interface publique, ni Labs, ni un endpoint privé. Voir
`docs/LOT_A_SOURCE_AUDIT.md`.
