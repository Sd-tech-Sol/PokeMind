# Comparer et choisir des listes publiques hors ligne

Les options peuvent ensuite être examinées par le
[prévol de légalité PUBLIC](PUBLIC_DECK_LEGALITY_PREFLIGHT.md) : identités,
structure et règles datées, sans supposer leur disponibilité dans Live.

Le comparateur utilise le cache PUBLIC du [lot compétitif du22octobre2026](COMPETITIVE_DECKLISTS_20261022.md).
Il inventorie les compositions distinctes, compare deux listes de60cartes et
propose de2à4options de familles différentes. Les commandes lisent exclusivement
la base explicitement choisie et les pages déjà présentes dans ce même espace
PUBLIC. Elles ne lancent aucune collecte, migration ou modification de deck.

## Commandes

Depuis la racine PokeMind, sous PowerShell :

```powershell
$publicDb = 'data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3'
python -m pokemind meta competitive-inventory --db $publicDb --as-of 2026-10-22
python -m pokemind meta competitive-compare --db $publicDb --as-of 2026-10-22 --left 581:1 --right 582:1
python -m pokemind meta competitive-shortlist --db $publicDb --as-of 2026-10-22 --options 4
```

Ajouter `--json` donne les mêmes faits structurés. `--db` PUBLIC et `--as-of`
sont obligatoires pour ces trois commandes :aucun repli vers la base personnelle.
`581:1` signifie événement581,placement1. Les références et URL viennent de
l'inventaire;une composition réutilisée peut avoir plusieurs références.

`--as-of` exclut les événements postérieurs à la date choisie. Cette date de
consultation ne valide pas rétroactivement les règles,la disponibilité du jeu
ou la légalité d'une impression. Les dates d'événement et de collecte restent
distinctes dans les pointeurs de provenance.

## Inventaire et identité des cartes

L'inventaire rapporte séparément placements,compositions distinctes,étiquettes
d'archétypes,événements,dates,éventail de placements et URL des listes. Les textes
de listes complets ne sont pas inclus dans cette sortie. Plusieurs placements
de la même URL et une composition identique publiée sous des URL différentes
ne comptent qu'une fois dans le nombre de compositions.

L'identité réutilise la normalisation des candidats PokeMind :nom normalisé en
Unicode/casse/espaces,set et numéro d'impression. Le type et les quantités
entrent aussi dans l'identité de la composition. L'ordre des lignes n'a pas
d'incidence. Les équivalences de langue,de réimpression ou de numéros écrits
différemment ne sont pas déduites. Une même impression portant des noms/types
contradictoires demeure ambiguë;elle ne sert pas à choisir une shortlist.

Chaque commande recontrôle le marqueur PUBLIC,les chemins/alias,le journal de
pages,les empreintes PUBLIC,les métadonnées d'événement et l'index Standard.
Les listes SQLite sont comparées aux pages complètes déjà cachées et reparsées
avec les validateurs existants. Ni client réseau,ni réimport,ni écriture du
journal de collecte ne sont nécessaires. Le client `BoundedPages` n'est jamais
construit par le conseiller.

## Lire les différences

Une comparaison A→B décompose les60copies de chaque liste :

- `shared` :le minimum des deux quantités pour chaque identité exacte;
- `removed` :les copies de A en surplus par rapport à B;
- `added` :les copies de B en surplus par rapport à A.

Ainsi,partagées+retirées=60 et partagées+ajoutées=60. Une carte présente des deux
côtés peut apparaître à la fois dans les partagées et dans une variation de
quantité. Les sections Pokémon/Dresseurs/Énergies et les Énergies nommées sont
des faits de composition;leur effet sur la performance reste une hypothèse.

Par défaut,chaque groupe affiche au plus12identités et indique combien sont
omises. Les totaux sont toujours calculés sur toutes les cartes. Utiliser
`--limit 60` pour lire tous les détails locaux. Les sorties complètes restent
hors Git. Une paire de références réutilisant la même composition annonce
`same_composition=true`,60copies partagées et zéro ajout/retrait.

## Choisir une option et l'exporter

La shortlist commence par la famille Dragapult,puis utilise Basic Box,Hydrapple
et Dhelmise si disponibles. D'autres familles présentes peuvent compléter les
options manquantes. `--options 2`,3ou4 règle la longueur;`--base 581:1` permet de
choisir explicitement une référence Dragapult valide.

Dans chaque famille,le représentant automatique est la composition distincte
qui minimise la somme des différences en copies avec les autres compositions
distinctes de cette famille :un **médoïde descriptif**. Les placements réutilisés
n'ajoutent aucun poids. Les égalités utilisent l'identité stable de composition.
Le rang au tournoi ne décide pas du représentant. L'ordre des familles sert à
présenter des plans variés;aucun score de force ou classement de performance
n'est produit.

Les faits de composition et les stades trouvés dans les textes de cartes déjà
cachés sont séparés des **hypothèses à tester** sur les évolutions,les Énergies,
les soutiens et l'échange des Récompenses. Une carte sans texte disponible garde
son stade inconnu. Une hypothèse attachée à une famille ne prouve ni la séquence
d'attaque exacte ni un avantage contre Dragapult.

Pour exporter séparément une option,reprendre son `export_selector`. Exemple :

```powershell
python -m pokemind meta competitive-export --db $publicDb --event 582 --placement 13
```

Cet export utilise le sérialiseur PTCGL existant,avec aller-retour à60cartes.
Il n'écrit pas dans le presse-papiers ni dans le jeu. Aucun nouveau test de
copier-coller TCG Live, historiquement `FIELD_VALIDATED`,n'est demandé.

## Résultat observé localement le22octobre2026

**CODEX_LOCAL_REPORTED** :2événements,32placements,28compositions distinctes,
15étiquettes d'archétypes;aucune anomalie de provenance détectée par ces commandes.
Les pages de résultats et de listes ont été relues hors ligne. Pour la comparaison
Dragapult581:1→Basic Box582:1 :**15copies partagées,45retirées,45ajoutées**.
Les références581:1 et582:5 donnent la même composition,60copies partagées.

| Option représentative | Source | Pokémon / Dresseurs / Énergies | Copies partagées avec la base / retirées / ajoutées |
|---|---|---|---|
| Dragapult581:1 | [Liste29678](https://www.limitlesstcg.com/decks/list/29678) |19/32/9|60/0/0|
| Basic Box582:13 | [Liste30524](https://www.limitlesstcg.com/decks/list/30524) |20/26/14|16/44/44|
| Hydrapple581:7 | [Liste30164](https://www.limitlesstcg.com/decks/list/30164) |21/25/14|15/45/45|
| Dhelmise581:4 | [Liste30162](https://www.limitlesstcg.com/decks/list/30162) |25/28/7|20/40/40|

Les représentants Basic Box/Hydrapple/Dhelmise peuvent différer des listes de
meilleur placement présentées dans le guide précédent :le critère est maintenant
la proximité de construction dans chaque famille. Ce choix n'exprime aucune
supériorité sportive. Les quatre options ont été exportées localement et relues
à60cartes. Les fichiers sont sous `data/local/competitive-advisor-20261022/`,
par exemple `event-582-rank-13.txt`;aucun contenu complet publié dans Git.

Le contrôle local a interdit réseau,client réseau,écritures SQLite et repli
personnel pendant les appels CLI. Les50fichiers PUBLIC contrôlés (base,marqueur,
journal et corps de pages référencés) sont inchangés. Les sorties QA sont écrites
dans un dossier distinct du cache PUBLIC. Ces constats sur Windows ne sont pas
une vérification indépendante du PC par GitHub.

## Données manquantes et limites

Une base PUBLIC absente,un schéma incomplet ou une source indispensable absente
produit `BLOCKED_WITH_REASON`,sans création de cache,migration ou téléchargement.
Les lignes invalides,les pages manquantes/corrompues et les sources ambiguës
sont signalées dans `issues`;l'inventaire devient `PARTIAL_WITH_EVIDENCE`.
Une comparaison refusée ne cherche pas d'autre liste à la place de celle demandée.
La shortlist écarte les compositions ambiguës;si Dragapult ou une alternative
distincte manque,elle refuse le choix. Un échantillon ne permettant que2ou3
options valides est explicitement partiel lorsqu'on en a demandé davantage.

Cet échantillon de bons placements et les statistiques de phase2 restent biaisés.
Les inconnues sont présentes dans les sorties :matchup,winrate,BO1/BO3,légalité
et disponibilité TCG Live,compatibilité à date,collection et crédits. Aucune
carte possédée,équivalence d'impression ou performance n'est inférée. Les textes
et listes restent attribués à leurs sources publiques et conservés localement;
aucune nouvelle licence de redistribution ou collecte n'est déduite du comparateur.

La CI utilise uniquement des pages et listes **inventées**. Sa preuve
`competitive_advisor_evidence` atteste déduplication,différences,shortlist,
absence de mutation et interdiction du réseau sur fixtures. Elle ne certifie
pas les28compositions du cache réel. V1 **NOT_RELEASE_READY**;les autres objectifs
visuels,planificateur Windows et récupération restent ouverts.
