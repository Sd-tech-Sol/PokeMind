# PM-V1-CATALOG-COMPLETE-001 — preuves assainies

2026-10-22 Québec. Ordre manuel : terminer le catalogue complet.
**PINNED_CATALOG_COMPLETE / AWAITING_AUDIT**, sans auto-VERIFIED.
Toutes les observations sur le cache réel sont **CODEX_LOCAL_REPORTED**.
V1 **NOT_RELEASE_READY**. Aucun accès ou changement personnel.

## Prévol et périmètre

Lectures AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, premier
NEXT_ACTION, HANDOFF/RESULT/DECISIONS, skill executor, PROJECT_SPEC, NEXT_PROMPT
et mandat intégral. Arbre initial propre, fetch puis pull ff-only sans perte :
`beed12f9ff70b4495a6928f6982f4276666e0fab` →
`7d39a54461f52d8f8816d0eeaeeed273d7ff15db`.
Prévol exact [Actions39727231274](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39727231274) :
Windows119653833969 et Ubuntu119653833775 **completed/success** à7d39a54,
avant toute exécution fonctionnelle. Aucun besoin d'attente.

Nouveau mandat ciblé établi d'après l'ordre propriétaire courant. Les permissions
et campagnes historiques sont closes; aucun rejeu, cumul de données ou réemploi
de leur budget. Aucune base privée, deck, journal, collection, capture, OCR,
installation OS, backup, restauration, migration privée, suppression ou merge.

## Acquisition publique bornée

Enveloppe de cette tâche : 50 000 requêtes TCGdex, 30 GET de découverte primaire,
134 217 728 octets cumulés, intervalle minimal0,5s; trois tentatives maximales
par ressource, refus/challenge terminaux. Aucun compte, secret ou image de carte.

1. Schéma et route GraphQL publics relus, requêtes fixes POST de lecture seulement;
   filtres explicites et sélection de champs. Les erreurs de sérialisation sur
   noms d'attaque manquants déclenchent seulement un détail REST d'ID connu,
   dans le même budget. **349 requêtes / 30 108 183 octets** : SOURCE_STOP,
   HTTP503 final pendant un repli FR; cause fournisseur interne UNKNOWN.
   Aucune reprise ni requête TCGdex après cet arrêt. Les pages partiellement
   récupérées ne constituent pas le catalogue final.
2. Voie indépendante prévue au mandat : archive du dépôt officiel épinglé, pas
   un retry API. **30 GET de découverte / 25 605 685 octets**, archive comprise;
   total cumulé **55 713 868 octets**, sous128MiB. Tous les budgets sont clos.
   Le dernier GET de référence master confirme le même commit amont.
3. Archive : **14 718 039 octets** comprimés, SHA256 public
   `567ede3947fc53e4f7130437b29d2e54fe0e750ea486dcfbc93effb03c806721`.
   Flux décomprimé **115 998 720 octets**, sous192MiB; taille comprimée sous32MiB.
   Arbre non tronqué :43 199 blobs/82 676 026 octets déclarés.
   Sélection exacte :24 119 fichiers textuels/45 531 158 octets, maximum10 074
   par fichier sous128KiB :data/**/*.ts, traduction FR et LICENSE.
   Chaque fichier retenu a taille et objet Git SHA1 vérifiés contre l'arbre.
   Pas de lien ni traversal, aucune extraction générale `extractall`, aucune
   exécution amont. L'archive contient aussi des actifs du dépôt qui ne sont ni
   extraits ni utilisés; aucune image de carte demandée séparément.

Commit source :`cbddf7e54033b1b58e44af1049c88832e55b94d0`, HEAD poussé2026-10-19.
SHA256 de l'arbre JSON public :
`c98bc633374df0480fad8a91f49a6adcd03932b026ce3c759d8a4f77463f471a`.
README et MIT complets relus; notice conservée localement, droits images distincts.
Sources primaires :
[README](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/README.md),
[MIT](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/LICENSE),
[données](https://github.com/tcgdex/cards-database/tree/cbddf7e54033b1b58e44af1049c88832e55b94d0/data),
[conversion cartes](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/server/compiler/utils/cardUtil.ts),
[résolution texte](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/server/compiler/utils/util.ts),
[schéma GraphQL](https://github.com/tcgdex/cards-database/blob/cbddf7e54033b1b58e44af1049c88832e55b94d0/meta/definitions/graphql.gql).

## Import hors ligne réel

Lecteur strict non exécutable :21Serie,223Set,23 873Card; zéro erreur de lecture
après prise en charge de deux concaténations de constantes texte. Aucun interpréteur
TypeScript, appel, expression dynamique, accès propriété ou instruction additionnelle.
Références typées Card→Set→Serie, cycles et collisions contrôlés.

Nouvel espace PUBLIC distinct :`lot-i-catalog-snapshot-20261022`.
**23 864 identifiants d'impression /223 extensions**. Neuf fichiers supplémentaires
déclarent un même ID dans un autre contexte de langue; toutes les origines sont
conservées, conflit de langue refusé. Union sans import d'une ancienne campagne.

| Couverture finale | EN | FR |
|---|---:|---:|
| Détails cartes disponibles |23 771|22 192|
| Détail indisponible dans cette langue |93|1 672|
| Détails extensions disponibles |220|202|
| Extensions sans nom localisé |3|21|
| En attente / erreur / périmé |0 / 0 / 0|0 / 0 / 0|
| Attaques / noms manquants |31 050 /14|29 039 /140|
| Talents / noms manquants |4 429 /20|4 171 /34|
| Pokémon / PV manquants |20 132 /0|18 797 /0|

Une disponibilité exige noms carte et extension référencée. Aucun repli EN→FR,
aucune absence déduite d'un HTTP404 fictif, aucun nom d'attaque complété.
`level`/`weight` pris en charge mais zéro valeur fournie ici. Champs absents
inconnus, prix/images/légalité exclus. Complétude descriptive pour `data/` au
commit épinglé, pas toutes langues, monde, Live ou équivalence officielle.

`cards coverage` :complete=true,current_indexes_complete=true,
details_complete_on_discovered=true; zéro travail obligatoire restant.
Les quatre ensembles de membres ont leur dénominateur et reçu; les pages sont
des tranches hors ligne d'une énumération immuable, pas des requêtes API.
SQL integrity_check=ok, foreign_key_check=0;47 728 traductions et47 728 lignesFTS,
zéro divergence d'identité/contenu; zéro payload/hachage incohérent ou origine
non attribuée. Les tables personnelles restent vides dans ce cache isolé.

Vérification réelle sous garde refusant socket/getaddrinfo/processus : recherches
Pikachu EN et FR (20 résultats chacune, limite demandée), fiches base1-58 types
Lightning/Électrique correctement séparés, provenance fichier épinglé.
Les cinq commandes CLI réelles coverage/search EN/search FR/show EN/show FR
sont également exécutées sous cette garde, exit0 et JSON valide. Dates de set et
raretés manquantes séparées par langue; régression dédiée.
Deuxième import :CACHE_HIT_COMPLETE,0HTTP et empreinte/mtime PUBLICDB inchangées;
ces empreintes de DB ne sont pas publiées. Aucun changement de schéma global.
Documentation d'usage :[CATALOGUE_TCGDEX_SNAPSHOT](../docs/CATALOGUE_TCGDEX_SNAPSHOT.md).

## Validation et livraison

Tests finaux : 663 passed /3 skipped, suite complète locale finale Python3.13.15 (304,39s);57 tests ciblés après revue bilingue. Tests synthétiques couvrent enveloppes,
refus, rollback atomique, provenance, source corrompue/tronquée/incomplète,
instructions rejetées, conflits de langue, champs manquants et import idempotent.
Prévol RUNTIME_READY Python3.13.15/SQLite3.50.4, sans DB personnelle/réseau/écriture.
Compilation, hygiène, diff préparé et contrôle des27chemins publiables réussis.
Trois skips : deux OCR sans opt-in, un symlink Windows indisponible; aucun OCR exécuté.
La CI de livraison est celle du HEAD contenant ce rapport, distincte du prévol;
les deux jobs doivent être completed/success au SHA exact avant réponse finale.
Le workflow publie son SHA et ses résultats synthétiques dans ses logs Actions.

Seulement code, tests, documentation et agrégats assainis dans Git. Aucun corpus,
base, archive, binaire, journal brut ou preuve privée. AWAITING_AUDIT,execute_now=false,
permission consommée; STOP audit indépendant ChatGPT. Aucun autre mandat préparé.
