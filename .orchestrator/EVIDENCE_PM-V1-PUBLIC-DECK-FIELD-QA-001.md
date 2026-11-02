# Preuves — PM-V1-PUBLIC-DECK-FIELD-QA-001

**CODEX_LOCAL_REPORTED; AWAITING_AUDIT. V1 NOT_RELEASE_READY.**

## Autorisation et prévol

Démarrage manuel du propriétaire; D-196/D-210, mandat et NEXT_PROMPT concordants.
Branche `work/pm-v1-lotj-final-readiness-windows`; worktree initial propre,
ff-only de `81c82d4ec42954e10a2603f6a2c317ca7d984de1` vers
`b7b1e0d7d37cb6de39c32ffc7b2a7e240618861a`, 10 commits, sans perte.
[CI préalable 40005992772](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40005992772)
au SHA autorisant : jobs Windows `120593984385` et Ubuntu `120593984445`,
chacun `completed/success`; ce run ne remplace pas la CI finale de livraison.
Issue #1, audit précédent, matrice et règles lus.

Seules les deux SQLite PUBLIC nommées dans le mandat ont été ouvertes.
Le propriétaire a explicitement étendu la **lecture seule** au `requests.json`
et aux pages PUBLIC référencées du même cache compétitif; marqueurs PUBLIC
contrôlés par les lecteurs existants. Aucun scan de `data/local`, autre cache,
base personnelle ou ancien résultat consulté pour remplacer une entrée.

## Exécution terrain complète

Au 2026-10-23T20:28:40.929156+00:00, connaissances évaluées au 2026-10-23.
Deux événements, 32 placements publiés sélectionnés, 28 compositions et
15 étiquettes d'archétypes; 13 familles après regroupement descriptif des
variantes Dragapult par le moteur existant. Échantillon biaisé de placements,
aucun dénominateur de matchs ou classement de force déduit.

- 32/32 exports sérialisés puis reparsés à **60/60**, identité de composition
  recoupée avec la liste publiée en cache; aucun conflit source détecté.
- 28/28 fiches avec prévol présentiel **et** Live : **28 unknown sur chaque
  plateforme**, zéro verdict de légalité inventé. 626/698 lignes par composition
  possèdent un texte natif daté; 1439/1680 copies ont une identité résolue.
- Identité par ligne : 626 résolues, 7 ambiguës (`30C`) et 65 non résolues
  (`MEE`). Dix identités distinctes manquent : sept MEE et trois 30C.
  Les sept inconnues MEE des pilotes sont conservées; aucune équivalence de
  nom devinée, aucune ambiguïté 30C levée par convenance.
- Pilotes Dragapult/Basic Box/Hydrapple/Dhelmise : **87/97 lignes** avec texte
  daté, puis contrôle automatisé de toutes les autres compositions.
- Counter-Deck : quatre cibles × quatre alternatives = **16 exports60**;
  48 questions d'interaction conditionnelles cumulées, aucun contre démontré,
  proxy PUBLIC distinct d'un adversaire exact, aucune variante exportée sans validation.
- **52 fichiers PUBLIC** nommés et référencés contrôlés avant/après : deux DB,
  deux marqueurs, un registre de requêtes et 47 pages. Octets, taille, identité
  de fichier et mtime inchangés; sidecars absents. Pas d'inventaire récursif.
  Les empreintes restent en mémoire et ne sont pas publiées. Ce constat ne
  prouve pas l'exclusion absolue de processus concurrents.
- Exécution instrumentée : connexions SQLite limitées aux deux URI exactes
  `mode=ro`, sockets et processus enfants interdits dans le lecteur terrain,
  lectures locales limitées aux fichiers autorisés; **0 GET fournisseur**.
  Aucun deck joué, journal, collection, crédits ou compte personnel ouvert.

## Provenance de chaque placement et lien à la fiche

Les identifiants C01–C28 sont des repères de cette preuve, pas de nouveaux IDs
persistants. La commande `meta deck-knowledge --selector EVENT:RANG` restitue
l'identité de composition complète et les preuves d'impression dans les deux
DB PUBLIC explicites. Les sources ci-dessous restent des listes de tournoi,
pas une certification réglementaire. Aucun export brut ni texte de carte
complet n'est versionné.

| Sélecteur | Composition | Archétype publié | Date événement | Source PUBLIC | Récupération UTC | Export reparsé |
|---|---|---|---|---|---|---|
| 581:1 | C12 | Dragapult | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/29678) | 2026-10-22T23:44:50Z | 60/60 |
| 581:2 | C16 | Dragapult Blaziken | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30160) | 2026-10-22T23:45:02Z | 60/60 |
| 581:3 | C25 | Sharpedo Toxtricity | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30161) | 2026-10-22T23:45:03Z | 60/60 |
| 581:4 | C09 | Dhelmise | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30162) | 2026-10-22T23:45:04Z | 60/60 |
| 581:5 | C13 | Dragapult | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30163) | 2026-10-22T23:45:05Z | 60/60 |
| 581:6 | C11 | Dragapult | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/29519) | 2026-10-22T23:45:06Z | 60/60 |
| 581:7 | C19 | Hydrapple | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30164) | 2026-10-22T23:45:07Z | 60/60 |
| 581:8 | C23 | Mew Box | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/29669) | 2026-10-22T23:45:08Z | 60/60 |
| 581:9 | C11 | Dragapult | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/29519) | 2026-10-22T23:45:06Z | 60/60 |
| 581:10 | C12 | Dragapult | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/29678) | 2026-10-22T23:44:50Z | 60/60 |
| 581:11 | C11 | Dragapult | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/29519) | 2026-10-22T23:45:06Z | 60/60 |
| 581:12 | C22 | Lucario Hariyama | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/28875) | 2026-10-22T23:45:09Z | 60/60 |
| 581:13 | C28 | Slowking | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30165) | 2026-10-22T23:45:10Z | 60/60 |
| 581:14 | C02 | Alakazam Dudunsparce | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30166) | 2026-10-22T23:45:11Z | 60/60 |
| 581:15 | C26 | Slowking | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30167) | 2026-10-22T23:45:12Z | 60/60 |
| 581:16 | C08 | Basic Box | 2026-10-10 | [liste](https://www.limitlesstcg.com/decks/list/30168) | 2026-10-22T23:45:13Z | 60/60 |
| 582:1 | C07 | Basic Box | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/29659) | 2026-10-22T23:41:59Z | 60/60 |
| 582:2 | C10 | Dhelmise | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30517) | 2026-10-22T23:44:47Z | 60/60 |
| 582:3 | C20 | Hydrapple | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30518) | 2026-10-22T23:44:48Z | 60/60 |
| 582:4 | C24 | Seaking Festival Lead | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30519) | 2026-10-22T23:44:49Z | 60/60 |
| 582:5 | C12 | Dragapult | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/29678) | 2026-10-22T23:44:50Z | 60/60 |
| 582:6 | C17 | Dragapult Dudunsparce | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30520) | 2026-10-22T23:44:51Z | 60/60 |
| 582:7 | C01 | Absol Audino | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30521) | 2026-10-22T23:44:52Z | 60/60 |
| 582:8 | C21 | Hydrapple | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/29616) | 2026-10-22T23:44:53Z | 60/60 |
| 582:9 | C05 | Basic Box | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30522) | 2026-10-22T23:44:54Z | 60/60 |
| 582:10 | C14 | Dragapult | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/28322) | 2026-10-22T23:44:55Z | 60/60 |
| 582:11 | C27 | Slowking | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30523) | 2026-10-22T23:44:56Z | 60/60 |
| 582:12 | C03 | Alakazam Dusknoir | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/29493) | 2026-10-22T23:44:57Z | 60/60 |
| 582:13 | C06 | Basic Box | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30524) | 2026-10-22T23:44:58Z | 60/60 |
| 582:14 | C04 | Basic Box | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30525) | 2026-10-22T23:44:59Z | 60/60 |
| 582:15 | C18 | Festival Lead | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30526) | 2026-10-22T23:45:00Z | 60/60 |
| 582:16 | C15 | Dragapult | 2026-10-17 | [liste](https://www.limitlesstcg.com/decks/list/30527) | 2026-10-22T23:45:01Z | 60/60 |

## Couverture par composition

Dénominateurs de lignes d'impression par composition, distincts des copies
et des placements répétés; les textes descriptifs ne prouvent pas les règles.
Tous les textes retenus proviennent du snapshot TCGdex épinglé et ont été
consultés le 22 octobre 2026. La fiche JSON conserve chaque URL et heure exacte.

| Repère | Sélecteur de fiche | Lignes avec texte / total | Identité résolue / ambiguë / non résolue | Copies résolues / 60 | Présentiel / Live |
|---|---|---:|---|---:|---|
| C01 | 582:7 | 23/26 | 23/0/3 | 49/60 | unknown/unknown |
| C02 | 581:14 | 24/25 | 24/0/1 | 58/60 | unknown/unknown |
| C03 | 582:12 | 23/24 | 23/0/1 | 59/60 | unknown/unknown |
| C04 | 582:14 | 24/29 | 24/1/4 | 48/60 | unknown/unknown |
| C05 | 582:9 | 21/26 | 21/0/5 | 45/60 | unknown/unknown |
| C06 | 582:13 | 23/28 | 23/0/5 | 46/60 | unknown/unknown |
| C07 | 582:1 | 22/27 | 22/0/5 | 45/60 | unknown/unknown |
| C08 | 581:16 | 23/29 | 23/1/5 | 46/60 | unknown/unknown |
| C09 | 581:4 | 21/22 | 21/0/1 | 58/60 | unknown/unknown |
| C10 | 582:2 | 20/21 | 20/0/1 | 57/60 | unknown/unknown |
| C11 | 581:6 | 22/25 | 22/0/3 | 52/60 | unknown/unknown |
| C12 | 581:1 | 21/24 | 21/0/3 | 51/60 | unknown/unknown |
| C13 | 581:5 | 22/25 | 22/0/3 | 51/60 | unknown/unknown |
| C14 | 582:10 | 20/23 | 20/0/3 | 51/60 | unknown/unknown |
| C15 | 582:16 | 21/24 | 21/0/3 | 51/60 | unknown/unknown |
| C16 | 581:2 | 23/26 | 23/0/3 | 52/60 | unknown/unknown |
| C17 | 582:6 | 23/26 | 23/0/3 | 52/60 | unknown/unknown |
| C18 | 582:15 | 26/27 | 26/0/1 | 57/60 | unknown/unknown |
| C19 | 581:7 | 22/23 | 22/0/1 | 46/60 | unknown/unknown |
| C20 | 582:3 | 22/23 | 22/0/1 | 47/60 | unknown/unknown |
| C21 | 582:8 | 26/27 | 26/0/1 | 47/60 | unknown/unknown |
| C22 | 581:12 | 20/21 | 20/0/1 | 49/60 | unknown/unknown |
| C23 | 581:8 | 21/27 | 21/3/3 | 47/60 | unknown/unknown |
| C24 | 582:4 | 21/22 | 21/0/1 | 58/60 | unknown/unknown |
| C25 | 581:3 | 21/22 | 21/0/1 | 51/60 | unknown/unknown |
| C26 | 581:15 | 24/26 | 24/1/1 | 55/60 | unknown/unknown |
| C27 | 582:11 | 25/26 | 25/0/1 | 56/60 | unknown/unknown |
| C28 | 581:13 | 22/24 | 22/1/1 | 55/60 | unknown/unknown |

## Défaut produit reproduit et correction ciblée

Le détecteur de rôles joignait la totalité des objets d'un champ natif en une
seule chaîne JSON. Une interdiction d'usage dans une phrase ultérieure masquait
une pioche conditionnelle permise; une mention de l'adversaire dans une condition
pouvait acquérir une défausse ou interdiction d'une autre phrase/objet.
Constats terrain : Flip the Script classé perturbation et pioche omise;
Rosa's Encouragement classée perturbation en reliant condition et défausse.

Correction minimale dans `deck_knowledge._roles` : lire les seuls champs
`effect`, séparément par objet et phrase; conserver les négations sur la phrase
concernée, y compris apostrophe typographique. Les noms de talents/attaques ne
créent plus de rôles. Sources, conditions et catégories fact/inference restent
présentes. Les tags sont des pistes conservatrices, pas un interpréteur complet
ni une autorisation d'action : une mécanique peut ne pas être détectée.

Le [guide joueur](../docs/PUBLIC_DECK_FIELD_QA.md) donne le parcours CLI et un
pilotage Dragapult ancré aux champs natifs datés : ouverture/recherche, chaîne,
pioche conditionnelle, Énergies, attaques et K.O./Récompenses, contre-jeu.
Aucun plan gagnant, matchup, possession ou règle manquante n'est fabriqué.

## QA et livraison

82 tests ciblés réussis en 55,08 s après correction de deux défauts du nouveau
harness de test (connexion de fixture non fermée, sélection Unicode de fixture).
La première exécution en échec n'est pas comptée comme réussite. Le harness CLI
terrain a aussi été ajusté pour permettre les imports Python tout en interdisant
la découverte des données locales; son premier refus n'est pas un défaut produit.
Les résidus de tests synthétiques en erreur n'ont pas fait l'objet d'une purge.

Prévol : `RUNTIME_READY`. Démo : `SYNTHETIC_REHEARSAL_PASSED`, 79 CLI,
13 checkpoints, espace de démo retiré par la routine, aucune opération privée.
**15 commandes CLI terrain réussies** : quatre fiches en humain et JSON,
quatre exports reparsés60, bibliothèque humaine, Counter-Deck humain et JSON.
Démarrage CP1252 puis UTF-8 strict de la CLI, zéro caractère de remplacement;
52 fichiers PUBLIC encore inchangés. Enfants instrumentés : deux seules URI
SQLite exactes en lecture seule, pas de réseau/processus enfant ou découverte
des données locales. Les imports Python nécessaires restent permis.
Compilation, tabnanny, hygiène et diffcheck passés avant livraison.
Suite complète finale : **1065 passed / 3 skipped en461,77s**, 1068 cas
collectés, zéro échec/erreur. Les15nouveaux tests du lot sont inclus et réussis;
aucun code/test modifié après cette collecte. Ignorés : deux OCR non installés
ou non attestés et un test de lien symbolique non permis sur ce Windows local.
Les8propriétés synthétiques héritées du JUnit ont été validées séparément,
sans se faire passer pour une exécution GitHub.

La CI de livraison doit être contrôlée au **HEAD distant exact**, deux jobs
Windows/Ubuntu `completed/success`, avec les neuf marqueurs existants :
`selected_match_review_evidence`, `counter_learning_evidence`,
`deck_library_matchup_evidence`, `deck_knowledge_evidence`,
`public_deck_preflight_evidence`, `competitive_advisor_evidence`,
`competitive_pages_evidence`, `rules_registry_evidence`, `ci_evidence`.
Les tests de ce lot doivent apparaître dans la suite finale; les empreintes
canoniques de registres doivent rester égales entre les deux OS.
La CI est pending à l'écriture du commit; son état durable est attaché dans
Actions au SHA exact après push. Les neuf marqueurs attestent des fixtures,
aucun cache réel ou PC certifié indépendamment par GitHub.

**AWAITING_AUDIT, execute_now=false, consumed=true. STOP exécuteur pour audit
indépendant ChatGPT; aucune tâche suivante créée, V1 NOT_RELEASE_READY.**
