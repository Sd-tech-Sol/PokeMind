# Revoir une partie choisie volontairement

`python -m pokemind battle review-selected` assemble l'importeur, Opponent
Observer, Matchup Analytics, Deck Knowledge, Counter-Deck Lab et Learning Loop
déjà présents. Sortie lisible ou `--json`, entièrement locale. **Ce lot est
validé sur des données inventées seulement. V1 NOT_RELEASE_READY.**

## Essayer maintenant, sans données personnelles

Depuis le dépôt, avec l'environnement Python du projet déjà disponible :

```powershell
python -m pytest -q -s tests/test_owner_selected_match_review.py::test_synthetic_demo
```

Cette démonstration crée elle-même des fichiers artificiels dans un espace
temporaire de test sous `data/local/test-runs`. Aucun chemin de vrai journal
n'est accepté par ce scénario. Deux versions de deck et cinq matchs inventés
préparent le contexte; un sixième journal FR est ensuite sélectionné :

1. Aperçu sans mutation : une carte adverse visible, archétype **hypothétique**,
   version inconnue et historique de cinq matchs; le journal non importé reste
   exclu des statistiques.
2. Import volontaire avec consentement distinct, panne simulée après le commit,
   puis reprise du même journal : six parties, aucun doublon ajouté, aucune
   attestation implicite.
3. Attestation v2 avec date jouée distincte de la date d'import; retrait daté et
   motivé, puis correction vers v1. Les preuves originales restent conservées.
4. Proxy PUBLIC distinct du vrai deck adverse, fiche de pilotage, quatre listes
   artificielles exactes de 60 cartes, différences complètes et plan de test.
5. Journal Learning Loop local conservé seulement sur demande; une deuxième
   sauvegarde identique est idempotente. Les hypothèses restent séparées des
   événements observés. Aucun progrès causal ou avantage de matchup démontré.

La suite négative complète est reproductible avec :

```powershell
python -m pytest -q tests/test_owner_selected_match_review.py
```

## Trois gestes distincts pour une future utilisation réelle

**Les exemples qui suivent sont des modèles, pas une autorisation de les
exécuter sur les données du propriétaire.** Les noms en majuscules doivent
être remplacés seulement après sa sélection et son ordre explicites. Aucun
ancien journal, deck, collection ou base n'est découvert automatiquement.

Tous les chemins doivent rester lexicalement sous `data/local` du projet.
La base choisie doit déjà exister au schéma courant et contenir le deck choisi;
ce parcours ne crée ni ne migre une base. Un ancien schéma est refusé.
Le fichier sélectionné doit être un `.txt` ou `.log` unique, de 2 000 000
octets maximum, UTF-8, UTF-16 ou Windows-1252, avec une seule partie reconnue.
Liens, jonctions/reparse points, liens matériels et sidecars SQLite présents
sont refusés. Aucun accès au presse-papiers ou au jeu.

### 1. Lecture et aperçu

```powershell
python -m pokemind battle review-selected --db data/local/BASE_CHOISIE.sqlite3 --log-file data/local/JOURNAL_CHOISI.txt --deck DECK_CHOISI --as-of AAAA-MM-JJ --dry-run --confirm-owner-read --json
```

`--confirm-owner-read` autorise **la source précise, les matchs du deck choisi
dans cette base pour les statistiques et les deux caches PUBLIC si sélectionnés**.
Un aperçu lit ces éléments : `--dry-run` signifie aucune écriture, et ne vaut
jamais consentement de lecture par lui-même. `access_plan` décrit les lectures
et les écritures qui seraient faites. Sans consentement, sélection, deck,
date ou base explicites, le refus précède toute inspection des fichiers.

Pour une partie déjà importée, remplacer `--log-file ...` par
`--battle-id ID_CHOISI`; les deux options sont incompatibles. Aucun export
adverse complet n'est inventé à partir des cartes observées.

### 2. Importer ce journal seulement

```powershell
python -m pokemind battle review-selected --db data/local/BASE_CHOISIE.sqlite3 --log-file data/local/JOURNAL_CHOISI.txt --deck DECK_CHOISI --as-of AAAA-MM-JJ --apply --confirm-owner-read --confirm-owner-import --json
```

Le résultat fournit le `battle_id`. **L'import n'atteste aucune version.**
L'import garde les événements structurés, pas le texte brut; l'original n'est
ni modifié ni supprimé. Un import exact est idempotent. Un journal identique
déjà associé à un autre deck est refusé. Les doublons probables du moteur
existant sont exclus prudemment des dénominateurs sans transfert de version.

### 3. Attester ou corriger séparément

Inspecter d'abord l'ID choisi avec `--dry-run --version NUMERO_VERSION` et,
si connue, `--battle-date DATE_JOUEE`. Pour appliquer ensuite :

```powershell
python -m pokemind battle review-selected --db data/local/BASE_CHOISIE.sqlite3 --battle-id ID_CHOISI --deck DECK_CHOISI --as-of DATE_EVALUATION --version NUMERO_VERSION --battle-date DATE_JOUEE --apply --confirm-owner-read --confirm-owner-attest --json
```

Une version ne peut être attestée dans la même commande que l'import.
Une version conflictuelle ne remplace jamais silencieusement l'ancienne.
Pour corriger : retirer l'attestation avec l'ID, `--revoke-version`,
`--reason "Motif choisi"`, `--apply`, `--confirm-owner-read` et
`--confirm-owner-attest`; puis attester la bonne version dans une nouvelle
commande. Le moteur conserve la ligne révoquée et sa date; le motif détaillé
est une note propriétaire datée et dédupliquée dans `battle_lessons`, sans
modifier le schéma ni transformer cette note en fait indépendant.
Une consultation à une date antérieure au retrait conserve l'état historique.

`--as-of` est la date d'évaluation, pas la date jouée. La date jouée reste
inconnue si non déclarée; la date d'import ne la remplace pas. Aucune écriture
ne peut être antidatée via `--as-of`. W/L/unknown et `n` sont séparés par version
attestée et hypothèse adverse; petits effectifs, inconnus et biais restent
visibles. Un log incomplet peut avoir une issue inconnue; un texte sans
événements/tour/référence suffisants est refusé sans import.

## Fiches, listes60 et expérience

Ajouter **les deux** options explicites `--public-db CHEMIN_PUBLIC_LISTES`
et `--reference-db CHEMIN_PUBLIC_CATALOGUE` pour obtenir les proxies, la fiche
Deck Knowledge et Counter-Deck Lab. `--set-aliases` active le pont sourcé
existant. Les caches sont consultés hors ligne en lecture seule.
Sans ces caches, ou si l'adversaire reste ambigu/inconnu, le rapport le dit
et propose de recueillir les preuves manquantes. Aucun archétype cible n'est
choisi arbitrairement. Les alternatives restent des listes publiées à tester,
pas des contres prouvés. Les différences se rapportent à la **base PUBLIC du
Counter-Deck Lab**, pas nécessairement à la version personnelle jouée.

Le texte des exports60 est affiché et présent dans le JSON. Pour le copier,
sélectionner l'export voulu et utiliser soi-même la commande de copie de son
terminal. Le logiciel ne touche pas au presse-papiers. Syntaxe/export60 ne
certifie ni légalité Live, disponibilité, collection, crédits ni victoire.
Le guide et les inconnus de légalité restent joints à chaque option.

Le JSON contient `learning_journal` : observations et version du parseur,
statistiques versionnées, hypothèse séparée et protocole testable.
Rien n'est conservé automatiquement. Pour conserver un instantané, sélectionner
un ID déjà importé, un chemin `.json` local **nouveau**, puis ajouter
`--learning-out CHEMIN_JSON --apply --confirm-owner-read --confirm-owner-attest`.
Le même contenu au même chemin est idempotent; un contenu différent ou un
fichier partiel est conservé et refusé à l'écrasement. Utiliser un nouveau
chemin explicitement choisi pour un nouvel instantané; les valeurs sont
compatibles avec `learning_loop.append_record/view` pour les révisions.

Les étapes existantes ont leurs transactions propres. Si une lecture après
import échoue, la sortie `PARTIAL_LOCAL_REVIEW_REQUIRED` et le code retour 2
indiquent le `battle_id` et les étapes déjà terminées. Les analyses du rapport
peuvent être antérieures aux écritures (`analysis_current_after_writes=false`).
Réexécuter la même sélection et les mêmes consentements reprend sans doublon.
Un échec de conservation JSON préserve l'artefact; aucun effacement ou rollback
des preuves déjà commises n'est tenté. Une panne pendant la transaction
d'import annule les événements de cette transaction.

## Empreintes des registres Windows/Ubuntu

Au SHA `1317c37`, les SHA bruts observés dans les deux jobs sont exactement
reproduits en encodant les mêmes JSON avec LF (Ubuntu) ou CRLF (Windows).
Les fichiers officiels n'ont pas été modifiés. `registry_sha256` continue de
décrire les octets du checkout; `registry_canonical_sha256` ajoute le SHA256
de `json.dumps(payload, ensure_ascii=False, sort_keys=True,
separators=(",", ":")).encode("utf-8")`, algorithme
`JSON_UTF8_SORTED_KEYS_COMPACT_UNESCAPED_UNICODE_V1`.

Ce format canonique interne ignore indentation, ordre des clés et fins de
ligne du fichier JSON. Il conserve l'ordre des tableaux et les valeurs des
chaînes, y compris leurs retours à la ligne. Il ne prétend pas implémenter
RFC8785 ni revalider les documents officiels. Les deux preuves restent
obligatoires et filtrées dans les logs CI, au SHA exact testé.
