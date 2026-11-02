# Actualisation des connaissances publiques — LOT D

## Portée

L’updater est un processus Python déterministe : il ne lance ni Codex, ni LLM, ni
client Pokémon TCG Live. Il ne lit et ne transmet aucun deck, collection, crédit,
journal, capture, pseudo ou identifiant de joueur. Seuls des URL, identifiants et
filtres publics quittent la machine.

Les trois sources demeurent séparées :

- TCGdex décrit les impressions et textes FR/EN;
- Pokémon officiel fournit des documents normatifs, mais une détection HTTP de
  changement reste `non_verified` ou `conflict` jusqu’à lecture et validation datée;
- Limitless fournit un échantillon compétitif descriptif, jamais la légalité.

Le schéma 12 ajoute seulement l’historique de cycles publics, les exécutions par
source, les empreintes de sources officielles et les alertes locales. Les anciennes
tables, FTS5 et données personnelles ne sont ni vidées ni réinterprétées.

## Prévisualiser sans effet

```powershell
python -m pokemind knowledge update --mode daily --dry-run --json
python -m pokemind knowledge update --mode deep --deep-time 19:30 --dry-run --json
python -m pokemind knowledge update --mode auto --deep-time 19:30 --dry-run --json
```

Le dry-run normal garantit `network_used=false`, `writes=0` : il ne crée pas la
base, ne la migre pas, ne crée aucun fichier de log et ne prend aucun verrou. Le
mode `auto` choisit une réconciliation profonde seulement lorsqu’un mardi/vendredi
configuré est dû; sinon il planifie le contrôle quotidien.

Un diagnostic réseau ponctuel est volontairement distinct et ne persiste rien :

```powershell
python -m pokemind knowledge update --dry-run --probe-public-network --json
```

Il sonde au plus une source Pokémon publique dans son budget, sans faire de cette
réponse une preuve normative.

## Appliquer une fenêtre publique bornée

Une application est réservée à une demande directe du propriétaire :

```powershell
python -m pokemind knowledge update --mode daily --apply --confirm-owner --json
python -m pokemind knowledge update --mode deep --deep-time 19:30 --apply --confirm-owner --json
```

Budgets par défaut : quotidien 4 GET TCGdex, 2 Pokémon officiel et 4 Limitless;
profond 20, 4 et 10. Chaque retry et redirection débite le client source avant le
GET. Les limites peuvent être abaissées ou augmentées explicitement :

```powershell
python -m pokemind knowledge update --mode daily --tcgdex-budget 4 --official-budget 1 --limitless-budget 4 --apply --confirm-owner --json
```

Une fenêtre épuisée conserve ses checkpoints et peut être `partial`; elle ne
remplace pas une donnée saine par une réponse incomplète. Les collecteurs TCGdex et
Limitless réutilisent leurs curseurs existants. Les sondes officielles conservent
uniquement URL, en-têtes, empreinte bornée et état, jamais le corps du document.

## Lire l’état hors ligne

```powershell
python -m pokemind knowledge update status --json
python -m pokemind knowledge update status --deep-time 19:30 --json
```

La commande ne migre pas SQLite et ne contacte pas le réseau. Elle expose le dernier
cycle, les compteurs `new/changed/missing/unknown`, `last_successful` par source,
les échecs consécutifs, les alertes ouvertes et l’échéance Toronto. Une tentative
incomplète ne modifie jamais `last_successful`.

États persistés : `planned`, `attempted`, `completed`, `partial`, `blocked`.
`completed` décrit la fenêtre bornée exécutée, pas la couverture mondiale. Une source
officielle modifiée produit une alerte locale et garde l’ancien registre normatif.

## Cadence Toronto et résilience

La cadence profonde utilise `zoneinfo` avec la clé IANA `America/Toronto`. Un repli
TZif moderne embarqué couvre Windows lorsque Python n’a pas le paquet `tzdata`.
Les offsets EST/EDT sont testés en hiver et en été. L’heure n’est jamais inventée :
elle doit être fournie par le propriétaire.

Les mardi et vendredi sont traités selon la date locale. Après une machine éteinte,
un seul rattrapage vise le plus récent cycle manqué dans la fenêtre de 14 jours. Un
jour déjà `completed` n’est pas répété. Les jours fériés n’ont pas de règle cachée :
ils suivent la cadence normale. Le verrou `data/local/knowledge-update.lock` empêche
les processus concurrents; un verrou vieux de plus de six heures est archivé comme
stale avant reprise.

Chaque unité source termine son GET avant une courte transaction de journalisation.
Les cycles et logs JSONL anonymisés restent sous `data/local/`. Les logs contiennent
codes, états et compteurs, sans chemin absolu, carte, montant, compte ou payload
externe. Après trois fenêtres incomplètes consécutives, une alerte locale est créée.

## Planificateur Windows : simulation seulement

Le LOT D n’installe et n’active aucune tâche. Les manifests sont seulement rendus en
mémoire :

```powershell
python -m pokemind knowledge scheduler --action install --daily-time 08:15 --deep-time 19:30 --windows-timezone "Eastern Standard Time" --dry-run --json
python -m pokemind knowledge scheduler --action status --dry-run --json
python -m pokemind knowledge scheduler --action uninstall --dry-run --json
```

La prévisualisation crée deux tâches à privilège minimal : quotidienne et mardi/
vendredi, `StartWhenAvailable`, `IgnoreNew`, durée maximale 30 minutes, répertoire de
travail explicite. Elles appelleraient `scripts/pokemind_update.ps1`, qui lance
uniquement la CLI Python.

Le LOT E refuse maintenant la génération si le fuseau Windows observé ou simulé
n’est pas exactement `Eastern Standard Time`, équivalent Windows de
`America/Toronto` avec DST. Sur Linux, l’option explicite permet seulement de tester
le manifeste. Le lanceur profond reçoit `-DeepTime`, transmet `--deep-time` et
enregistre la date Toronto réellement due; un mardi/vendredi complété n’est plus
reproposé et seul le plus récent cycle manqué est rattrapé.

Toute commande sans `--dry-run` refuse avec
`SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D`, même avec `--confirm-owner`. Une future
activation devra faire l’objet d’un consentement distinct et d’un nouveau changement
de ce verrou logiciel. Aucun `schtasks /Create`, `Register-ScheduledTask`, service,
autorun ou processus résident n’a été exécuté pendant ce lot.

## Limites conservées

- Catalogue historique, détails FR/EN, réimpressions, errata, promos, restrictions
  et métagame global restent `PARTIAL_WITH_EVIDENCE` selon la couverture mesurée.
- Trainer Hill reste `BLOCKED_WITH_REASON`; aucun scraping de repli.
- Une empreinte HTTP différente n’explique pas la modification et ne valide aucune
  rotation, restriction ou règle.
- La vision locale réelle et l’essai de capture du LOT C demeurent partiels.
- Sauvegarde/restauration complète, rétention et stabilisation finale restent LOT E.

