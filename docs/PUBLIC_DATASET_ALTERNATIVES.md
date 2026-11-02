# Alternatives publiques au catalogue FR/EN — revue bornée

Mandat `PM-V1-PUBLIC-DATASET-ALTERNATIVES-001`, 2026-10-21 Québec
(consultations 2026-10-22 UTC). **RAPPORTÉ_PAR_CODEX_LOCAL**, audit indépendant
requis. **V1 NOT_RELEASE_READY**.

## Décision et architecture retenue

**Conserver le parcours REST TCGdex FR/EN existant.** Les deux alternatives
examinées ne satisfont pas ensemble les exigences de droits, langues, fraîcheur,
format et volume. Aucun importateur, convertisseur TypeScript/CSV, SDK,
compilateur, nouvelle dépendance ou schéma SQLite n'est ajouté. Aucun corpus
externe n'est importé dans une base, ni redistribué dans Git.

Le chemin retenu reste : sélection publique d'identifiants explicites →
campagne PUBLIC protégée → client REST borné → validateurs/upserts existants →
catalogue/FTS → consultation hors ligne avec provenance par langue. Il permet
de résoudre les détails utiles sans scanner d'abord l'index et les sets.
Cette décision ne déclenche aucune nouvelle campagne réseau.

## A — Inventaire du code et des preuves existantes

| Brique existante | Fonction effectivement présente | Limite |
| --- | --- | --- |
| `src/pokemind/cards.py` | client HTTPS et budget, validation JSON, listes/sets/détails FR/EN, upserts et FTS, show/search/coverage/reprints | le catalogue descriptif n'est pas un registre officiel de légalité ou de disponibilité Live |
| `src/pokemind/catalog_snapshots.py` | membres par scan/langue, pages/duplications/gaps, dates, fraîcheur, erreur, durée | pagination non atomique; un scan terminé n'est pas un total mondial actuel |
| `src/pokemind/public_campaign.py` | dry-run par défaut, espace PUBLIC dérivé, marqueur, garde owner/unknown, contrôle alias/reparse, verrou et budgets | aucune entrée arbitraire `--db` ou `--snapshot`; aucun acte personnel autorisé |
| `src/pokemind/public_card_selection.py` | 1–100 IDs, détails seulement, transaction par paire, reprise, cache30jours, absence404 distincte, refus d'accès persistant | index fournisseur non parcouru, complétude globale=false; cache frais ne prouve pas absence de changement amont |
| `src/pokemind/database.py` | schéma13 : sets, impressions et traductions, FTS, registres normatifs distincts | aucune migration d'une base réelle dans ce mandat |

Une impression a un ID public, son set et son numéro local. Les textes et noms
EN/FR ont un statut, une URL, une date de récupération et un hash de payload
propres. Variants, série, catégorie, caractéristiques et champs manquants restent
distincts. Un nom partagé ou un ID identique entre fournisseurs ne prouve pas
l'équivalence des cartes. `functional_identity=unknown` par défaut; les
réimpressions vérifiées exigent des assertions officielles séparées et datées.
Les sources d'errata, de légalité et de support Live ne sont pas remplacées.

| Échantillon historique versionné, non rejoué | Couverture rapportée | Portée exacte |
| --- | --- | --- |
| [PUBLIC-COVERAGE](../.orchestrator/EVIDENCE_PM_V1_PUBLIC_COVERAGE_001.md), 2026-10-18 Québec | index3200 membres cartes par langue,12 détails/langue; union3578 impressions | campagne séparée, fin cartes non atteinte; sets220 EN/202 FR, scans non atomiques; variantes/détails exhaustifs inconnus |
| [BULK-SOURCE](../.orchestrator/EVIDENCE_PM_V1_TCGDEX_BULK_SOURCE_001.md), 2026-10-19 Québec | sélection2 impressions;2 détails EN/1 FR et1 absence FR | autre espace PUBLIC, index non parcouru; reprise0GET rapportée |
| Présent mandat | 102 objets JSON EN et162 lignes CSV de sets examinés en mémoire | données de revue seulement; **0 impression/détail ajouté au catalogue** |

Ces chiffres ne sont jamais additionnés. Les bases/workspaces historiques n'ont
pas été consultés : l'inventaire s'appuie sur le code et les rapports versionnés.
Les fixtures synthétiques prouvent les mécanismes, pas les totaux du fournisseur.

## B — Deux alternatives réelles et le repli REST

| Critère | PokémonTCG/pokemon-tcg-data | tooniez/pokemoncards_tcg | REST TCGdex existant |
| --- | --- | --- | --- |
| Auteur/maintenance | organisation PokémonTCG; dernier commit observé par adback03; README déclare le projet legacy/déprécié | @tooniez, licence copyright2024; dernière activité observée2024-10-20 | TCGdex; preuves datées des lots PUBLIC/BULK, pas de nouvel appel fournisseur ici |
| Version épinglée | `39a26a144c8b6ef6c2fb17b2c29d0bb7121e3a11`, commit2026-09-17T00:28:23Z | `13cf376295d76c60e9842ef4e482f5ffca07ff33`, commit2024-10-20T07:20:37Z | APIv2 + provenance/hash/date par réponse; endpoint évolutif, pas un snapshot global immuable |
| Licence/conditions observées | README propose téléchargement historique, mais licence réutilisable non établie; `LICENSE`404 et aucune licence dans l'arbre racine observé | README annonce MIT; LICENSE entière MIT, copyright2024 @tooniez; conserver notice/permissions pour copies substantielles | revue antérieure MIT au commit TCGdex `cbddf7e54033b1b58e44af1049c88832e55b94d0`; cache recommandé; ni images/marques ni aspiration illimitée autorisées implicitement |
| Format mesuré | `cards/en/base1.json` : liste JSON102 objets/102 IDs uniques,112108 octets; `number`, `supertype`, `convertedRetreatCost`, pas `localId`/`set` dans l'objet examiné | `sets.csv` :162 lignes,11 colonnes,36008 octets; structures imbriquées sérialisées en texte; dates à slash | détails JSON FR/EN déjà validés, absence404 distincte; sérialisation et FTS existants |
| FR/EN | chemin EN et langue non déclarée dans les objets; FR **non prouvé**, aucune traduction demandée | README principalement EN; aucune couverture FR prouvée | mécanismes et petits échantillons FR/EN attestés; couverture totale toujours partielle |
| Fraîcheur | README déconseille nouvelles intégrations; annonce retrait de son API au2027-03-01, attribué à cette version documentaire | échantillon sets se termine àsv7, sortie2024-09-13; aucune preuve de maintenance du catalogue2026 | cache30jours et actualisation bornée déjà disponibles; pas de nouvelle mesure de fraîcheur réseau ici |
| Volume | seul fichier EN mesuré; taille totale/archives non mesurée, aucun téléchargement global | arbre annonce `cards.csv`12488295 octets (>5MiB); fichier **non téléchargé**; decks303163 octets également non téléchargés | coût unitaire par paire/langue; batch explicite, reprise et budget existants |
| Windows/local/sécurité | JSON lisible par bibliothèque standard sans exécution; IDs inter-fournisseurs à mapper, objets incomplets pour le schéma TCGdex; URLs images ignorées | CSV lisible par bibliothèque standard; champs imbriqués à valider sans eval, notice/amont à qualifier, aucune formule exécutée | pipeline Python/SQLite existant, sans dépendance supplémentaire; chemins PUBLIC, HTTPS, plafonds et arrêt sur refus |
| Coût d'intégration | adaptation des types, sets, identités, provenance, licence et FR; **non faible** avec les preuves actuelles | adaptation CSV/JSON imbriqué, dates, champs, amont, FR et gros fichier; **non justifié** | **aucun code produit nouveau**, tests de frontières et documentation seulement |
| Décision | **BLOCKED_WITH_REASON** : REUSE_LICENSE_NOT_ESTABLISHED, FR_COVERAGE_UNPROVEN, LEGACY_SOURCE | **BLOCKED_WITH_REASON** : FR_COVERAGE_UNPROVEN, STALE_SAMPLE, CARDS_FILE_EXCEEDS_LOT_BUDGET, UPSTREAM_PROVENANCE_INCOMPLETE | retenu pour les détails FR/EN bornés; catalogue complet PARTIAL_WITH_EVIDENCE |

Preuves primaires épinglées :

- PokémonTCG : [commit](https://github.com/PokemonTCG/pokemon-tcg-data/commit/39a26a144c8b6ef6c2fb17b2c29d0bb7121e3a11),
  [README](https://github.com/PokemonTCG/pokemon-tcg-data/blob/39a26a144c8b6ef6c2fb17b2c29d0bb7121e3a11/README.md),
  [racine](https://github.com/PokemonTCG/pokemon-tcg-data/tree/39a26a144c8b6ef6c2fb17b2c29d0bb7121e3a11),
  [JSON EN échantillonné](https://github.com/PokemonTCG/pokemon-tcg-data/blob/39a26a144c8b6ef6c2fb17b2c29d0bb7121e3a11/cards/en/base1.json).
  L'absence d'une licence racine n'établit pas l'absence de tout droit partout;
  elle interdit de présumer une autorisation de réutilisation dans ce lot.
- tooniez : [commit](https://github.com/tooniez/pokemoncards_tcg/commit/13cf376295d76c60e9842ef4e482f5ffca07ff33),
  [README](https://github.com/tooniez/pokemoncards_tcg/blob/13cf376295d76c60e9842ef4e482f5ffca07ff33/README.md),
  [LICENSE](https://github.com/tooniez/pokemoncards_tcg/blob/13cf376295d76c60e9842ef4e482f5ffca07ff33/LICENSE),
  [arbre mesuré](https://api.github.com/repos/tooniez/pokemoncards_tcg/git/trees/13cf376295d76c60e9842ef4e482f5ffca07ff33?recursive=1),
  [sets CSV](https://github.com/tooniez/pokemoncards_tcg/blob/13cf376295d76c60e9842ef4e482f5ffca07ff33/sets.csv).
  README : sections de collecte, annotation et citation encore génériques;
  la licence MIT du dépôt ne certifie pas les droits de tous les contenus amont.
- REST : [revue des sources](SOURCES_CONNAISSANCES.md) et preuves historiques
  citées plus haut. Le dépôt TypeScript TCGdex n'a été ni redemandé ni réimporté.

La recherche GitHub ciblée FR n'a retourné aucun dépôt dans **cette requête**;
cela ne prouve pas qu'aucune source FR n'existe. La seconde recherche a aussi
signalé PocketDecks/pokemon-tcg-pocket-cards (autre jeu, Pocket), des analyses et
des scrapers : simples métadonnées de recherche, licences non relues, aucun
code/fichier téléchargé ni source supplémentaire intégrée. Aucun compte ou
produit commercial suggéré par un README n'a été consulté.

## C — Collecte réellement bornée

**12 GET /12 maximum; 214753 octets de corps /5242880 maximum (5MiB).**
Onze réponses200 et une404 de14octets incluse; zéro redirection/retry,
401/403/429 ou challenge observé. Dernier GET2026-10-22T00:19:53Z.

| # | Document public | Octets lus |
| --- | --- | ---: |
| 1 | recherche GitHub `pokemon tcg data french`,5 résultats max,0 résultat | 55 |
| 2 | PokémonTCG dernier commit,1 résultat max | 3310 |
| 3 | recherche GitHub `pokemon tcg dataset`,8 résultats max | 47522 |
| 4 | PokémonTCG README épinglé | 3979 |
| 5 | PokémonTCG LICENSE épinglée,404 | 14 |
| 6 | tooniez dernier commit,1 résultat max | 3251 |
| 7 | PokémonTCG arbre racine épinglé,non tronqué | 1978 |
| 8 | tooniez arbre récursif épinglé,non tronqué | 1319 |
| 9 | tooniez README épinglé | 4145 |
| 10 | tooniez LICENSE épinglée | 1064 |
| 11 | tooniez sets CSV épinglé | 36008 |
| 12 | PokémonTCG JSON EN épinglé | 112108 |

Compteur persistant dans un **nouvel espace de revue public ignoré**,
indépendant des campagnes historiques. GET incrémenté avant transmission;
lecture en flux plafonnée par réponse et au cumul, Accept-Encoding identity,
timeout15s, délai minimal0,5s, HTTPS/hôtes fixes, redirections refusées sans
nouveau GET, aucun jeton, arrêt sur refus/challenge. Mesure des corps lus,
hors en-têtes/TLS. Aucun lecteur web à sous-requêtes cachées n'a été utilisé.
Les contrôles Git/GitHub du dépôt de travail sont distincts de ces12GET.
Ce helper local est un outil de revue ponctuel, pas un collecteur livré.

Les réponses brutes restent hors Git; aucune archive, image, binaire, deck,
script fournisseur ou extension n'a été téléchargé/exécuté. Les champs d'URL
images et les instructions des README sont restés du texte inerte. Le budget
est épuisé; aucune requête fournisseur supplémentaire n'est autorisée par ce lot.

## D–E — Repli et validation

Le gain du parcours retenu est celui déjà prouvé par le test synthétique
`test_detail_yield_improves_without_spending_budget_on_sets` : à4GET égaux,
4 paires cartes résolues (3 présentes/1 absence), contre2 détails cartes et
2 détails sets dans le parcours général. **Aucun nouveau gain réel ou total
catalogue n'est revendiqué.** Aucune ancienne campagne n'a été rejouée.

Sept nouveaux cas dans `tests/test_dataset_alternatives.py` vérifient le refus
des listes JSON/CSV/objets étrangers, même munis d'une étiquette MIT; le refus
d'une provenance brute étrangère ou de mauvaise langue avant écriture; et
l'absence EN sans repli FR avec reprise0GET. Tous les objets sont synthétiques,
les sockets/DNS sont bloqués et les bases sont des fixtures temporaires.

Les suites héritées testent aussi format corrompu, FR absent, doublons/alias,
réimpressions non inférées du nom, variants, dates invalides/futures/stale,
provenance, idempotence, budgets, rollback, owner/unknown et refus d'accès.
Le test existant de `--snapshot`/`--db` interdit une entrée JSON sans licence,
TypeScript ou fauxZIP : **refus de surface inexistante**, pas validation de
licence ou d'archive. Le validateur/importeur de datasets et ses tests de
licence manquante restent **BLOCKED_WITH_REASON**, conformément au choix D.
Le contrôle documentaire des licences ne devient pas un validateur logiciel.

Résultats d'exécution et CI exacte dans
[EVIDENCE du mandat](../.orchestrator/EVIDENCE_PM-V1-PUBLIC-DATASET-ALTERNATIVES-001.md).
La qualification des deux alternatives est terminée pour ce budget; un snapshot
FR/EN complet, autorisé, maintenu et exploitable demeure non prouvé. Aucune tâche
suivante n'est préparée. STOP AWAITING_AUDIT après livraison.
