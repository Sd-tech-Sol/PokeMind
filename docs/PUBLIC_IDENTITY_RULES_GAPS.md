# Identités PUBLIC et règles : preuves manquantes

Mandat `PM-V1-PUBLIC-IDENTITY-RULES-SCOPED-002`, 23 octobre 2026.

**PARTIAL_WITH_EVIDENCE / CODEX_LOCAL_REPORTED. V1 NOT_RELEASE_READY.**

Les deux SQLite explicitement autorisées ont été lues sans écriture. Aucun registre local de requêtes, marqueur PUBLIC ou fichier de page additionnel lu. La revalidation complète des listes contre leurs pages est **BLOCKED_SOURCE_SCOPE**; les tableaux ci-dessous décrivent les enregistrements en cache, pas une nouvelle certification des listes publiées. L’ancien arrêt de session demeure clos.

## Dénominateurs observés

| Mesure | Résultat |
|---|---:|
| Placements en cache / compositions dédupliquées | 32 / 28 |
| Identités listées uniques résolues / total | 158 / 168 |
| Lignes résolues / lignes des compositions | 626 / 698 |
| Copies résolues / copies des compositions | 1439 / 1680 |
| Identités uniques encore inconnues | 10 |

Une ligne réutilisée dans deux compositions compte deux fois dans les lignes, mais une fois dans les identités uniques. Les placements dupliqués ne multiplient pas les compositions ni leurs copies.

## Dix identités encore inconnues

Niveau de preuve commun : observation descriptive du cache consulté le **22 octobre 2026**, snapshot Git épinglé; l’identité de liste demeure **unknown** pour chacune. Les codes MEE et 30C ne deviennent pas des équivalences officielles. Les liens permettent de retrouver les éditions/numéros candidats sans ouvrir de source supplémentaire pendant ce mandat.

Les liens ci-dessous viennent des métadonnées stockées du snapshot TCGdex épinglé `cbddf7e54033b1b58e44af1049c88832e55b94d0`. Aucune nouvelle consultation réseau. Le candidat de catalogue fournit un contexte descriptif; il ne remplace jamais l’identité demandée.

| Liste : nom / code / numéro | Candidat descriptif EN (édition) | Lignes / copies | Cause |
|---|---|---:|---|
| Jirachi ex / 30C / 102 | [Jirachi ex / 30th-102](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/30th%20Celebration/102.ts) | 2 / 2 | Code 30C partagé par deux éditions dans le pont |
| Mew ex / 30C / 66 | [Mew ex / 30th-066](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/30th%20Celebration/066.ts) | 4 / 7 | Code 30C partagé par deux éditions dans le pont |
| Unown / 30C / 72 | [Unown / 30th-072](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/30th%20Celebration/072.ts) | 1 / 1 | Code 30C partagé par deux éditions dans le pont |
| Fire Energy / MEE / 10 | [Basic Fire Energy / mee-010](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/010.ts) | 8 / 23 | Nom de liste et nom natif présent non concordants |
| Water Energy / MEE / 11 | [Basic Water Energy / mee-011](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/011.ts) | 6 / 8 | Nom de liste et nom natif présent non concordants |
| Lightning Energy / MEE / 12 | [Basic Lightning Energy / mee-012](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/012.ts) | 4 / 8 | Nom de liste et nom natif présent non concordants |
| Psychic Energy / MEE / 13 | [Basic Psychic Energy / mee-013](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/013.ts) | 21 / 61 | Nom de liste et nom natif présent non concordants |
| Fighting Energy / MEE / 14 | [Basic Fighting Energy / mee-014](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/014.ts) | 8 / 23 | Nom de liste et nom natif présent non concordants |
| Darkness Energy / MEE / 15 | [Basic Darkness Energy / mee-015](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/015.ts) | 9 / 35 | Nom de liste et nom natif présent non concordants |
| Grass Energy / MEE / 9 | [Basic Grass Energy / mee-009](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/Mega%20Evolution%20Energy/009.ts) | 9 / 73 | Nom de liste et nom natif présent non concordants |

Pour MEE, le numéro rempli de zéros correspond à un candidat dont le nom EN inclut « Basic ». Cette similarité et la classification d’Énergie ne démontrent aucune équivalence fonctionnelle. Les variants observés mentionnent une finition holo et un estampillage d’anniversaire; ils ne prouvent ni le support Live ni une identité avec un numéro voisin. Une preuve littérale d’identité de cette impression et une équivalence de noms sourcée demeurent nécessaires.

Pour 30C : aucun code natif observé; le pont sourcé propose **deux éditions**, `30th` et `30th-c`. Le moteur refuse cette collision avant de choisir une carte. Il faut établir le code, l’édition et le numéro de la liste avec une preuve directe; ne pas sélectionner le set simplement parce que le nom du candidat concorde.

Sources descriptives des deux alias 30C, déjà stockées et contrôlées par le pont : [30th](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/30th%20Celebration.ts) (consulté 2026-10-22T16:16:04Z, sortie déclarée 2026-09-16); [30th-c](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/data/Mega%20Evolution/30th%20Classic%20Collection.ts) (consulté 2026-10-22T16:16:04Z, sortie déclarée 2026-09-16). Les URLs de catalogue sont des références, non des lectures réseau supplémentaires.

## Pourquoi les verdicts restent inconnus

Les deux registres Git nommés ont été examinés intégralement. `official_rules_2026.json` borne ses assertions de rotation au 11 octobre; la revue `official_rules_20261022.json` borne les deux rotations et sa revue des restrictions au **22 octobre seulement**. Aucune de ces fenêtres ne couvre le 23 octobre. Ce constat décrit la couverture du cerveau; il ne prétend pas que les règles réelles ont changé.

| Preuve | Présentiel au 23 octobre | Live au 23 octobre |
|---|---|---|
| Assertions Standard actives vérifiées dans le cache | 0 | 0 |
| Rotation datée unique | non prouvée | non prouvée |
| Structure générale | règle de 60 cartes, base et quota disponibles; exceptions et limites spéciales incomplètes | même limite |
| Réimpressions / errata | exemples précis et revue datée du 22, aucune équivalence MEE/30C démontrée | aucun transfert implicite |
| Bannissements / sortie / promos | absence de couverture courante exhaustive; ne pas déduire une illégalité | restrictions client et disponibilité par impression non prouvées |
| Source complète des listes | BLOCKED_SOURCE_SCOPE | BLOCKED_SOURCE_SCOPE |

Les exemples de réimpression Git concernent notamment `sm1-129 → me01-125` et `swsh2-154 → me01-114`, et les errata nomment certains Minior et Diancie. Leur présence ne résout aucune des dix identités ci-dessus. Une abréviation descriptive TCGdex, une présence dans un tournoi ou une ligne de 60 cartes ne certifie aucune légalité.

## Chaque composition observée

Codes communs : **S** = source complète hors périmètre; **R** = rotation datée absente; **Q** = exceptions de quotas et limites spéciales incomplètes; **I** = identités ci-dessous inconnues; **L** = disponibilité Live de chaque impression inconnue. Les deux verdicts sont conservateurs, sans exécution du prévol complet et sans nouveau verdict `legal`.

| Sélecteurs en cache | Lignes | Identités inconnues | Présentiel | Live | Source cache / date |
|---|---:|---|---|---|---|
| 581:1, 581:10, 582:5 | 24 | Fire Energy / MEE / 10; Psychic Energy / MEE / 13; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/29678) / 2026-10-22T23:44:50Z |
| 581:2 | 26 | Fire Energy / MEE / 10; Psychic Energy / MEE / 13; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30160) / 2026-10-22T23:45:02Z |
| 581:3 | 22 | Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30161) / 2026-10-22T23:45:03Z |
| 581:4 | 22 | Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30162) / 2026-10-22T23:45:04Z |
| 581:5 | 25 | Psychic Energy / MEE / 13; Fire Energy / MEE / 10; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30163) / 2026-10-22T23:45:05Z |
| 581:6, 581:9, 581:11 | 25 | Psychic Energy / MEE / 13; Fire Energy / MEE / 10; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/29519) / 2026-10-22T23:45:06Z |
| 581:7 | 23 | Grass Energy / MEE / 9 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30164) / 2026-10-22T23:45:07Z |
| 581:8 | 27 | Mew ex / 30C / 66; Jirachi ex / 30C / 102; Unown / 30C / 72; Psychic Energy / MEE / 13; Water Energy / MEE / 11; Fighting Energy / MEE / 14 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/29669) / 2026-10-22T23:45:08Z |
| 581:12 | 21 | Fighting Energy / MEE / 14 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/28875) / 2026-10-22T23:45:09Z |
| 581:13 | 24 | Mew ex / 30C / 66; Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30165) / 2026-10-22T23:45:10Z |
| 581:14 | 25 | Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30166) / 2026-10-22T23:45:11Z |
| 581:15 | 26 | Mew ex / 30C / 66; Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30167) / 2026-10-22T23:45:12Z |
| 581:16 | 29 | Jirachi ex / 30C / 102; Grass Energy / MEE / 9; Fighting Energy / MEE / 14; Lightning Energy / MEE / 12; Psychic Energy / MEE / 13; Water Energy / MEE / 11 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30168) / 2026-10-22T23:45:13Z |
| 582:1 | 27 | Grass Energy / MEE / 9; Psychic Energy / MEE / 13; Lightning Energy / MEE / 12; Fighting Energy / MEE / 14; Water Energy / MEE / 11 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/29659) / 2026-10-22T23:41:59Z |
| 582:2 | 21 | Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30517) / 2026-10-22T23:44:47Z |
| 582:3 | 23 | Grass Energy / MEE / 9 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30518) / 2026-10-22T23:44:48Z |
| 582:4 | 22 | Fire Energy / MEE / 10 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30519) / 2026-10-22T23:44:49Z |
| 582:6 | 26 | Fire Energy / MEE / 10; Psychic Energy / MEE / 13; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30520) / 2026-10-22T23:44:51Z |
| 582:7 | 26 | Darkness Energy / MEE / 15; Psychic Energy / MEE / 13; Fighting Energy / MEE / 14 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30521) / 2026-10-22T23:44:52Z |
| 582:8 | 27 | Grass Energy / MEE / 9 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/29616) / 2026-10-22T23:44:53Z |
| 582:9 | 26 | Grass Energy / MEE / 9; Psychic Energy / MEE / 13; Lightning Energy / MEE / 12; Fighting Energy / MEE / 14; Water Energy / MEE / 11 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30522) / 2026-10-22T23:44:54Z |
| 582:10 | 23 | Fire Energy / MEE / 10; Psychic Energy / MEE / 13; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/28322) / 2026-10-22T23:44:55Z |
| 582:11 | 26 | Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30523) / 2026-10-22T23:44:56Z |
| 582:12 | 24 | Psychic Energy / MEE / 13 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/29493) / 2026-10-22T23:44:57Z |
| 582:13 | 28 | Grass Energy / MEE / 9; Psychic Energy / MEE / 13; Fighting Energy / MEE / 14; Lightning Energy / MEE / 12; Water Energy / MEE / 11 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30524) / 2026-10-22T23:44:58Z |
| 582:14 | 29 | Mew ex / 30C / 66; Grass Energy / MEE / 9; Psychic Energy / MEE / 13; Water Energy / MEE / 11; Fighting Energy / MEE / 14 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30525) / 2026-10-22T23:44:59Z |
| 582:15 | 27 | Grass Energy / MEE / 9 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30526) / 2026-10-22T23:45:00Z |
| 582:16 | 24 | Psychic Energy / MEE / 13; Fire Energy / MEE / 10; Darkness Energy / MEE / 15 | unknown (S,R,Q,I) | unknown (S,R,Q,I,L) | [liste](https://www.limitlesstcg.com/decks/list/30527) / 2026-10-22T23:45:01Z |

## Poursuite et limites

Le module `public_deck_preflight.scoped_identity_rules_observations` possède deux chemins fixes, sans repli ni recherche de fichiers. Il réutilise le parseur compétitif, le pont TCGdex et le résolveur existants. Il ne certifie pas les listes à la place du vérificateur de pages. Le prévol complet appelé avec `source_scope="two_sqlite_only"` refuse avant toute inspection : `BLOCKED_SOURCE_SCOPE`.

La lecture SQLite utilise `mode=ro&immutable=1` et `query_only`, sans sidecars; un fichier principal au format WAL est refusé. Métadonnées et octets des deux fichiers comparés avant/après : inchangés. Ces comparaisons ne prouvent ni l’absence de tout écrivain concurrent, ni la complétude transactionnelle du cache, ni la protection du namespace contre une course. Aucune base utilisateur ouverte.

À rechercher seulement lors d’un futur mandat : preuve directe des noms/impressions MEE; désambiguïsation du code 30C; règles officielles valides à la date évaluée; preuves de sortie, promos, exceptions, errata et support Live par impression; autorisation distincte des pages requises si une revalidation complète est souhaitée. Aucun téléchargement, droit supplémentaire ni prochain lot n’est accordé par ce tableau.

Validation synthétique et état de livraison : [preuves assainies](../.orchestrator/EVIDENCE_PM-V1-PUBLIC-IDENTITY-RULES-SCOPED-002.md).
