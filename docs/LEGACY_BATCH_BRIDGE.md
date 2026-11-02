# Consulter une analyse conservée et comprendre le blocage legacy

Pour afficher automatiquement le dernier rapport valide, utiliser désormais
[`python -m pokemind battle coach`](BATTLE_COACH.md). La commande explicite
`batch-report` décrite ici demeure une consultation à chemin exact.

`battle batch-report` consulte un instantané existant. Il ne relit pas les
journaux, ne refait pas les recommandations, n'ouvre aucune SQLite et ne cherche
pas le fichier « le plus récent ». Aucun joueur ni dossier de combats n'est requis.
Cette livraison a été testée uniquement sur des données inventées; elle ne donne
aucune permission nouvelle de consulter des fichiers personnels.

## Lecture à chemin exact

Depuis la racine du projet, fournir le **chemin canonique retourné dans
`memory.report`** lors de l'analyse autorisée. Les valeurs ci-dessous sont à
renseigner localement, jamais dans Git ou une requête réseau :

```powershell
python -m pokemind battle batch-report --report "$env:POKEMIND_SAVED_REPORT"
python -m pokemind battle batch-report --report "$env:POKEMIND_SAVED_REPORT" --json
```

Le fichier doit être un JSON directement sous `data/local/battle-intelligence`.
Les chemins canoniques `analysis-<empreinte>.json` permettent de distinguer un
instantané corrigé d'une version précédente. Son empreinte sémantique est
contrôlée avant affichage. Un fichier explicitement nommé, notamment un alias
date/version, reste consultable avec `EXPLICIT_NAMED_SNAPSHOT_NOT_LATEST` :
**aucune redirection automatique vers une autre version**. Le contenu historique
peut être ancien; sa date est celle conservée dans le rapport.

Pour consulter aussi son journal Learning Loop, fournir **séparément** le chemin
exact retourné dans `memory.learning` :

```powershell
python -m pokemind battle batch-report --report "$env:POKEMIND_SAVED_REPORT" --learning "$env:POKEMIND_SAVED_LEARNING" --json
```

Le journal est facultatif et n'est jamais ouvert implicitement. La chaîne
immuable, les références et les révisions sont validées par Learning Loop
existant; le modèle et les faits doivent correspondre à l'instantané choisi.
Pour un rapport canonique, les deux noms canoniques doivent former la même paire.
La sortie JSON est une **projection d'affichage**, pas un nouvel export immuable
du journal : métadonnées privées et empreintes ne sont pas reproduites.

Le rendu réutilise `human_report` : W/L/inconnus/n, familles hypothétiques,
preuves d'événements déjà anonymisées, propositions et limites. Les exports
publics conservés sont reparsés à60 avec le parseur existant; aucun catalogue ou
site n'est consulté. Si l'instantané mentionne le schéma7, le lecteur affiche
**DB_IMPORT_BLOCKED_SCHEMA_7**. Lire ce rapport ne prouve pas un import SQLite,
une version jouée, une amélioration causale ou une légalité actuelle.

Versions de rapport reconnues : `battle-batch-v1` à `v4`, sous contrat de champs
validé; les champs ajoutés aux versions récentes ont des replis explicites lorsque
compatibles. Une version future ou une structure incompatible est refusée.
Maximum32MiB par JSON, limites de profondeur/nœuds/chaînes, nombres finis et
clés uniques. Refus des traversées, ADS, redirections, liens multiples et changements
de fichier pendant la lecture. HTML et contrôles de terminal sont rendus inertes;
les erreurs sont des codes neutres, sans chemin, contenu ou traceback personnel.

## Diagnostic SQLite sans migration

`battle legacy-plan --db CHEMIN --json` exige une DB explicitement choisie,
au chemin PokeMind fixe sous `data/local`. Aucun défaut, scan ou recherche de
racine. **Ne pas exécuter cette commande sur la DB personnelle sans un nouvel
ordre ciblé du propriétaire.** Les tests de cette livraison utilisent des racines
fictives avec le même chemin relatif.

Le diagnostic ouvre la DB en `mode=ro`, `query_only`, sans schéma de confiance,
avec délai de verrou et budget de calcul. Avant connexion : taille≤2GiB, en-tête,
identité du fichier et absence de `-wal`, `-shm`, `-journal`; un en-tête WAL est
refusé même sans sidecar. Il contrôle intégrité, violations et contrats FK,
tables/colonnes connues, index d'attestation active et contrat d'entraînement.
La stabilité est contrôlée après lecture. Il n'appelle **jamais**
`initialize_schema`, `connect_writable` ou une fonction de migration/backup.

La fixture7 provient des DDL suivis de
[`database.py` au commit019ee534](https://github.com/Sd-tech-Sol/PokeMind-dev/blob/019ee5348dd9771f9dd30d92dfb079e8c6d65c61/src/pokemind/database.py).
Elle est créée vide depuis ces `CREATE`, sans données utilisateur et sans
dégrader une DB13. Hors tables internes FTS, les contrats contiennent23tables en7
et37en13 : **14tables nouvelles, aucun changement de colonne des23tables communes**.
La fixture13 est initialisée à partir d'une DB neuve; aucune migration7→13 n'est
exécutée, même en test. Un simple `PRAGMA user_version=13` ne suffit pas.

| Version historique | Delta du contrat |
| --- | --- |
| 8 | `battle_version_attestations`, index d'unicité active et historique/révocation |
| 9 | `official_deck_structure_rules` |
| 10 | Collection/crédits volontaires, leçons, candidats et leurs cartes :6tables |
| 11 | `training_sessions` et `training_observations` |
| 12 | Cycles/sources/observations/alertes d'actualisation :4tables; retrait de l'ancienne unicité globale d'observation |
| 13 | Contrat `local_vision`, reconstruction conditionnelle des observations d'entraînement |

Le schéma7 possède déjà les tables de combats, événements, observations, listes
exactes et liens historiques. La politique actuelle attend13 avant import.
L'attestation explicite du **couple partie/version jouée** est distincte d'une
liste enregistrée exacte60 et d'un ancien lien temporel; le diagnostic ne la
fabrique pas. Une référence exacte60 n'implique ni possession ni légalité.
La correspondance des tables/colonnes ne certifie pas tout le produit, les index
FTS, les connaissances ou l'état opérationnel du PC.

Le code d'écriture d'événements a aussi été corrigé : `ambiguous_owner` et
`owner_unknown` restent des qualificatifs du parseur, mais sont projetés vers
`low` pour le `CHECK` SQL déjà commun aux schémas7 et13. La cible n'est pas
transformée en carte de l'acteur. Tests avec événements inventés; aucune écriture
personnelle et aucun élargissement du schéma.

## Déblocage futur distinct

Le plan retourné est descriptif, sans SQL exécutable ni option `--apply`.
Les helpers actuels peuvent inscrire13 avant la fin de toutes les étapes : il
faut contrôler les contrats complets, pas uniquement ce numéro. Les migrations
existantes valident plusieurs transactions séparées et peuvent reconstruire une
table avec les FK temporairement désactivées. Un rollback d'étape ne constitue
pas une restauration globale.

**Ne pas lancer l'initialiseur sur une ancienne DB pour la diagnostiquer** :
il déclenche actuellement une sauvegarde et des DDL. Aucune nouvelle création de
backup n'est autorisée. Tout futur déblocage personnel exige un mandat séparé :
autorisation exacte, accès exclusif, revue des preuves de récupération existantes,
plan de retour et contrôles post-opération. Cette livraison ne teste ni n'autorise
une migration/restauration réelle et ne retire pas le blocage de la DB personnelle.

**V1 NOT_RELEASE_READY. Après livraison : AWAITING_AUDIT, STOP ChatGPT.**
