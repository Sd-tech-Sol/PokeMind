# Deck Intelligence — fondation PUBLIC

QA terrain du 23 octobre 2026 : [parcours liste sourcée → pilotage → export60](PUBLIC_DECK_FIELD_QA.md).
32 placements/28 compositions revérifiés hors ligne; couverture et inconnues
explicites, sans certification de légalité ou de données personnelles.

Tranche suivante : [bibliothèque et fondation Observer/Matchups](DECK_LIBRARY_MATCHUPS.md),
recherche des compositions et alternatives de construction; code d'analyse
adverse/statistique testé sur fixtures uniquement, sans vraie partie ouverte.

La CLI produit une fiche de pilotage et une liste PTCGL de **60 cartes** à partir
d'une liste de tournoi déjà en cache. Dragapult, Basic Box, Hydrapple et Dhelmise
ont des fiches pilotes locales. Ce sont des options descriptives issues de deux
tournois et de placements sélectionnés, avec un biais top16. Aucun classement de
force ni taux de victoire par matchup n'est calculé.

## Consulter et copier manuellement

Depuis la racine du dépôt, utiliser les deux caches **PUBLIC explicitement
sélectionnés**; aucun repli sur une base personnelle :

```powershell
$publicDb = 'data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3'
$referenceDb = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind meta deck-knowledge --selector 581:1 --as-of 2026-10-23 --db $publicDb --reference-db $referenceDb --set-aliases
python -m pokemind meta deck-knowledge --selector 581:1 --as-of 2026-10-23 --db $publicDb --reference-db $referenceDb --set-aliases --json
python -m pokemind meta competitive-export --event 581 --placement 1 --db $publicDb
```

| Fiche pilote | Sélecteur | Texte descriptif sourcé / lignes de la liste |
|---|---|---:|
| Dragapult | `581:1` | 21 / 24 |
| Basic Box | `582:13` | 23 / 28 |
| Hydrapple | `581:7` | 22 / 23 |
| Dhelmise | `581:4` | 21 / 22 |

L'export reprend le parseur/sérialiseur existant, historiquement
`FIELD_VALIDATED`. Il est comparé à la composition publiée puis reparsé à 60/60.
La fiche contient le texte à copier manuellement. Elle n'ouvre pas le jeu et
n'utilise pas le presse-papiers. Un export reconnu syntaxiquement ne certifie
ni légalité Live, ni disponibilité d'une impression, ni possession.

Les rapports complets JSON et humains, quatre exports et le pont dérivé sont
dans le nouvel espace isolé `data/local/public-campaigns/lot-i-deck-intelligence-20261023/`,
ignoré de Git. Aucun deck détaillé réel ne fait partie du dépôt ou de la CI.

## Ce que la fiche explique

Chaque carte conserve quantité, nom, code et numéro originaux. Si son identité et
son texte natif sont prouvés dans le cache, la fiche affiche langue, texte,
attaques/coûts/effets, talents et provenance datée. Les rôles inférés utilisent
des motifs conservateurs dans ces champs, jamais le nom seul. Ce sont des pistes
de lecture; les restrictions, cibles et coûts complets restent applicables.

Le guide relie les évolutions attestées présentes dans la liste, identifie les
outils de pioche/recherche/énergie/récupération/perturbation, propose un ordre
d'installation conditionnel, puis présente les attaques et un plan de test.
Le plan de K.O./Récompenses dépend du plateau visible, des protections, des PV et
des ressources; aucune suite de tours garantie ou erreur personnelle n'est
inventée. Les quantités d'Énergie de la liste publiée restent distinctes des
copies dont l'identité de catalogue est résolue.

Chaque affirmation a une catégorie :

- `fact` : texte descriptif effectivement observé, avec champ et source;
- `inference` : conseil conditionnel dérivé des cartes et champs référencés;
- `hypothesis_to_test` : séquence ou plan à éprouver en entraînement volontaire;
- `unknown` / `uncertainty` : preuve manquante, jamais complétée par génération.

Les quatre fiches restent **`PARTIAL_WITH_EVIDENCE`**. Les textes de sept
impressions uniques ne concordent pas avec les noms publiés; ce sont des
Énergies `MEE` dont le catalogue nomme l'impression « Basic … Energy » alors
que la liste emploie « … Energy ». Aucune équivalence de nom n'est inventée.
Légalité, errata exhaustifs, Live, collection, crédits et matchups restent
séparés; un nom résolu ne suffit jamais à déclarer une carte légale.

## Pont optionnel de codes d'extension

Le prévol historique garde son comportement par défaut. `--set-aliases` active
une vue en mémoire séparée, `public-set-code-bridge-v1`, sans modifier
`catalog_sets`, les impressions natives ou les deux DB historiques :

```powershell
python -m pokemind meta competitive-preflight --db $publicDb --reference-db $referenceDb --as-of 2026-10-23 --format standard --platform in_person --set-aliases --json
python -m pokemind meta competitive-preflight --db $publicDb --reference-db $referenceDb --as-of 2026-10-23 --format standard --platform live --set-aliases --json
```

Le pont exige un payload TCGdex vérifié par son empreinte, une provenance
d'import supportée, une abréviation concordante, langue, date de consultation,
date de sortie non future et source non périmée. Il conserve le lien de l'objet
de set du snapshot épinglé; l'ancien champ URL de la table peut pointer vers
une carte membre et n'est pas présenté comme la source de l'abréviation.
`abbreviation.official` est le **nom d'un champ descriptif TCGdex**, pas une
certification réglementaire Pokémon.

Le code doit identifier un seul set, y compris face aux codes natifs existants.
Le numéro, l'appartenance au set et le nom présent dans la langue observée sont
ensuite recoupés. Seul le remplissage décimal par zéros est normalisé (`8`/`008`);
aucun suffixe, préfixe de sous-série, nom d'Énergie ou numéro voisin n'est deviné.
Alias ambigu, preuve absente ou nom discordant donnent `unknown`.

| Mesure sur les quatre options | Avant | Avec pont |
|---|---:|---:|
| Lignes d'impressions uniques résolues | 0 / 69 | 62 / 69 |
| Lignes comptées par option résolues | 0 / 97 | 87 / 97 |
| Copies avec identité résolue, options cumulées | 0 / 240 | 201 / 240 |
| Lignes ambiguës par option | 0 | 0 |
| Decks à légalité inconnue en présentiel | 4 / 4 | 4 / 4 |
| Decks à légalité inconnue sur Live | 4 / 4 | 4 / 4 |

Ces mesures sont **CODEX_LOCAL_REPORTED** au 2026-10-23. Les dénominateurs ne
sont pas interchangeables : les copies répétées et impressions réutilisées
entre options ne créent pas de nouvelles identités. Les 14 codes peuvent être
reliés à leurs métadonnées sans nouvelle collecte; **0 GET, 0 octet réseau et
0 découverte fournisseur**. L'enveloppe autorisée de ce lot n'est pas transférable.

## Modèle minimal et réutilisation

`deck-knowledge-v1`, schéma 1 : `archetype`, `variant`, `source_list`,
`card_role`, `observed_card_text` par carte, `strategic_claim`, `uncertainty`,
`dated_provenance` et `version_sha256`. La version dépend du contenu, de la date,
du modèle et des sources. Aucun nouvel entrepôt ou framework : la vue réutilise
`competitive` (sources/pages/listes/déduplication/export), `rules.check_deck_entries`
(identité/structure/légalité), `cards.show_card` et les payloads natifs vérifiés.
Les recommandations privées et tables FTS existantes restent disponibles pour
leurs usages autorisés; elles ne sont pas copiées dans un second moteur.

Hiérarchie conservée : Pokémon officiel pour les normes; TCGdex pour la
description; Limitless pour liste/événement. Poképédia est un texte communautaire
distinct sous CC-BY-NC-SA-3.0; ses suppléments FR ne sont pas promus comme texte
officiel ni utilisés pour combler silencieusement ce pilote. Les textes détaillés
et données réelles restent dans le cache local. Sources publiques de contexte :
[catalogue épinglé](https://github.com/tcgdex/cards-database/tree/cbddf7e54033b1b58e44af1049c88832e55b94d0/data),
[tournoi 581](https://www.limitlesstcg.com/tournaments/581),
[tournoi 582](https://www.limitlesstcg.com/tournaments/582).

## Suite de l'EPIC, sans nouveau mandat lancé

[Issue #1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1) reste la feuille de
route. DKI-01 et le premier parcours de DKI-02 sont livrés pour audit. Compléter
la bibliothèque et les preuves de noms/errata demande un futur mandat public.
Opponent Observer (DKI-03), Matchup Analytics (DKI-04), Counter-Deck Lab (DKI-05)
et Learning Loop (DKI-06) ne sont pas livrés par ce lot. Toute vraie partie,
collection ou version personnelle exige une commande volontaire sélectionnant
les données. Les portes OCR, scheduler Windows et récupération A–J restent
ouvertes. **V1 NOT_RELEASE_READY; audit indépendant ChatGPT requis.**
