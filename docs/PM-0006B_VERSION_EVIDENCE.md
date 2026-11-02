# PM-0006B — comparaison de versions et preuves combat→version

## Commandes et garanties

```powershell
python -m pokemind deck compare <deck-id> --from-version 1 --to-version 2 --json
python -m pokemind deck compare <deck-id> --from-version 1 --to-version 2 --as-of 2026-10-12 --show-changes
python -m pokemind deck version-evidence <deck-id> --as-of 2026-10-12 --json
```

Les deux commandes ouvrent une base existante en SQLite `mode=ro`, activent
`query_only`, ne migrent rien, ne créent aucun fichier et ne font aucun appel réseau.
Le JSON expose `read_only:true` et `network_used:false`. Base absente, schéma ancien
ou erreur SQLite donnent un état contrôlé; le texte brut d'une exception, un chemin,
un token ou une donnée de deck ne sont jamais recopiés dans la sortie.

## Comparaison descriptive

La comparaison lit exactement les deux numéros demandés pour le même `deck_id`; elle
ne choisit aucune autre version en silence. Il faut deux versions `exact_confirmed`,
un total enregistré de 60, une somme de quantités de 60, des lignes valides et des
compteurs cohérents. Une seule version produit `INSUFFICIENT_DECK_VERSIONS`; une
version absente, étrangère, non confirmée, à 59 cartes ou avec quantité invalide est
refusée explicitement.

La clé d'impression est le quadruplet suivant, après Unicode NFC, espaces regroupés
et casse ignorée :

```text
card_type + set_code + collector_number + card_name
```

Le nom seul ne prouve jamais une identité ni une équivalence FR/EN. Deux codes de set
ou numéros différents restent deux impressions distinctes. L'absence de set ou de
numéro porte `identity_uncertain`; aucune identité fonctionnelle de réimpression
n'est inventée. L'ordre et la section textuelle d'origine ne changent pas le résultat
si les mêmes impressions et quantités sont présentes.

Les faits donnent, pour chaque version, statut, dates, applicabilité historique,
quantités et lignes par section, sections présentes sur trois, identités distinctes
et contrôles 60/60. Les changements donnent impressions ajoutées/retirées, impressions
dont la quantité change, quantités augmentées/diminuées et `delta_total`. Entre deux
versions valides, `delta_total=0`.

Par défaut, aucune carte n'est listée. `--show-changes` ajoute volontairement les noms,
codes, numéros et quantités à la sortie locale, avec l'avertissement « PRIVÉ — ne pas
partager ». Les tests et documents utilisent uniquement des cartes synthétiques.

## Provenance des liens combat→version

`battle_logs.deck_id` signifie seulement « deck déclaré lors de l'import ». Seule une
ligne `battle_deck_versions` peut constituer une preuve explicite de version. L'audit
déduplique les combats par leur identité locale sans afficher l'empreinte, filtre les
imports postérieurs à `as_of`, ventile W/L/nul/ambigu et fournit une période basée sur
les dates d'import.

Chaque lien est ensuite classé :

- `proven_same_deck_links` : version existante du même deck, exacte, 60/60 et
  provenance temporelle cohérente;
- `unlinked` : deck déclaré sans version explicitement reliée;
- `conflicting_links` : version absente, autre deck, version non fiable ou provenance
  de lien incohérente;
- `temporal_doubts` : version effective après la date d'import ou date inexploitable.

La date d'import du journal n'est pas nécessairement la date réelle de la partie.
Une concordance chronologique ne prouve donc jamais l'identité à elle seule; un doute
demande confirmation au lieu de réécrire l'historique. Les demandes utilisent
`local-observation-NNN` et la date d'import, sans pseudo, adversaire, SHA, chemin ou
contenu du journal. PM-0006B n'écrit aucun lien et n'implémente aucun outil de liaison.

## Limites avant recommandation

Les issues attribuées sont des comptes descriptifs avec `n`, jamais un taux prédictif.
Un bilan de cinq parties reste exploratoire. Aucune comparaison de rendement n'est
produite dans cette tranche, même si plusieurs versions existent. Une future
recommandation exigera versions exactes, liens explicitement confirmés, cohérence
temporelle, échantillons suffisants, identités/légalité vérifiées et, lorsque requis,
collection et coûts fournis volontairement. Aucun changement d'impression ne prouve
une amélioration stratégique.

## Couverture synthétique

Les tests couvrent version unique, versions différentes, version absente ou étrangère,
non confirmée, 59 cartes, quantité négative, réordonnancement, mêmes noms sous deux
impressions, identité incomplète, `delta_total=0`, cinq W/W/W/W/L sans lien, un seul
lien explicite, lien vers un autre deck, doute temporel, doublon d'empreinte, combat
futur, sortie JSON/humaine, caviardage d'erreur, absence de réseau et identité
byte-for-byte de la base avant/après les commandes.
