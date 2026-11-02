# PM-V1-LEGACY-BATCH-BRIDGE-001 — preuves de livraison

2026-10-25. **AWAITING_AUDIT**, constats locaux **CODEX_LOCAL_REPORTED**.
Portée exclusivement code et fixtures inventées. Aucun vrai journal, rapport,
journal Learning Loop, cache PUBLIC ou SQLite du propriétaire ouvert.
Aucune nouvelle analyse réelle, migration7→13, sauvegarde, restauration, purge,
installation, OCR, jeu, clipboard ou recherche fournisseur.

## Prévol avant exécution fonctionnelle

Branche `work/pm-v1-lotj-final-readiness-windows`, arbre propre; fetch et pull
fast-forward sans perte de `a6efbde7aca9cce3ff39db225670e899a55bb80f` à
`14ac86f1a46f1e9e26fdf8bc3bdb520eb2f682fa`.
[CI40157291390](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40157291390)
`completed/success` au SHA READY exact : Windows job121061274784
**1213 passés/2 ignorés**, Ubuntu job121061274451 **1212/3**. Neuf marqueurs
hérités par job, huit JSON épinglés SHA/run et `ci_evidence` texte, registres
canoniques concordants. NEXT_PROMPT, mandat et audit précédent lus intégralement.
La spécification suivie est `.orchestrator/PROJECT_SPEC.md`.

## Consultation conservée, sans réanalyse

`battle batch-report --report CHEMIN [--learning CHEMIN] [--json]` est traité
avant découverte de racine et DB implicite. Seuls les fichiers explicitement
fournis sont ouverts, directement dans le dossier de rapports prévu. Aucun scan,
choix automatique d'alias, import, lecture SQLite ou GET. Un instantané canonique
est contrôlé par son empreinte sémantique; les fichiers nommés/alias sont marqués
`EXPLICIT_NAMED_SNAPSHOT_NOT_LATEST`. Ancien et corrigé restent indépendants.

Validation bornée :32MiB/JSON, profondeur48,750000nœuds,2millions de caractères
par chaîne, clés uniques, nombres finis, versions reconnues, portée/date,
cohérence matchs/groupes/W-L et schéma imbriqué via le rendu existant.
Exports PUBLIC reparsés à60 et différences de copies contrôlées, sans connaissance
externe. Traversées, ADS, redirections/reparse, liens multiples, taille et source
changeante refusés. Erreurs neutres sans traceback/contenu/chemin.

Réutilisation de `battle_batch.human_report`, du parseur d'exports et de
`learning_loop.view/validate`; pas de deuxième moteur ni nouvelle persistance.
Journal facultatif explicitement choisi, paire canonique et faits/version
correspondants, chaîne/révisions contrôlées avant projection d'affichage.
HTML, contrôles de terminal et chemins non fiables neutralisés; empreintes,
noms de fichiers source, identifiants de deck et exports personnels omis de la
projection. Le rendu dit **consultation seule**, date conservée et statut
**DB_IMPORT_BLOCKED_SCHEMA_7** si l'instantané le mentionne. Il ne prétend pas
que la DB a été importée, qu'un deck a été joué ou que sa légalité est vérifiée.

## Diagnostic legacy concret, sans exécuter la migration

`battle legacy-plan --db CHEMIN [--json]` exige le chemin connu explicitement,
sans défaut ni découverte. Avant connexion : en-tête/taille≤2GiB, identité,
absence de sidecar WAL/SHM/journal; en-tête WAL refusé même sans sidecar.
Connexion `mode=ro`, `query_only`, `trusted_schema=OFF`, FK actives, délai de
verrou et budget SQLite. Contrôles intégrité, violations/contrats FK, tables et
colonnes, index d'attestation active, contrat d'entraînement et stabilité après
lecture. Aucune sélection de données personnelles nominatives dans le diagnostic.
Version du produit future : contrat explicite à mettre à jour, pas de faux succès.

Fixture7 créée depuis les seuls DDL `CREATE` du
[`database.py` suivi019ee534](https://github.com/Sd-tech-Sol/PokeMind-dev/blob/019ee5348dd9771f9dd30d92dfb079e8c6d65c61/src/pokemind/database.py),
sans copier de données et sans abaisser le numéro d'une DB13. Fixture13 neuve
initialisée à partir de0. **Aucune migration7→13 exécutée, même sur fixture.**
Hors tables internes FTS :23tables en7,37en13,14ajouts, colonnes des23communes
inchangées. V8attestations, V9règles de construction, V10collection/crédits/leçons/
candidats, V11entraînement, V12actualisations et correction d'unicité,
V13contrat local_vision. Contrats de tables/colonnes testés contre le module actuel.

Les tables de combats/versions existent déjà en7. L'import reste bloqué par la
politique13; une référence exacte60 ou un ancien lien temporel ne vaut jamais
attestation du couple partie/version. Aucun lien ou consentement inventé.
Les états compatibles sont limités au contrat contrôlé, pas une certification
opérationnelle globale ni FTS/connaissances du PC.

Plan futur descriptif uniquement, sans SQL exécutable ni `--apply`. L'initialiseur
existant déclenche backup/DDL, valide des étapes séparées et peut reconstruire
des tables avec FK temporairement OFF; rollback d'étape ≠ restauration globale.
Certains helpers fixent13 avant la fin : numéro seul insuffisant. Toute opération
personnelle exige un nouveau mandat, accès exclusif, revue des preuves de
récupération existantes et plan de retour. **Aucune nouvelle création de backup
autorisée par ce plan.**

## Correctif de compatibilité d'événements

Les qualificatifs parseur `ambiguous_owner`/`owner_unknown` échouaient au CHECK
SQL `high/medium/low`, commun aux schémas7 et13. `_insert_events` les projette vers
`low`; faits, cible et ambiguïté du parseur sont conservés, sans créditer une
carte cible à l'acteur. Qualificatif inconnu refusé. Deux tests d'écriture
d'événements **inventés** sur les fixtures7/13, sans import de journal ni appel
d'initialiseur sur une ancienne DB. Aucun changement du schéma/migrations.

## Tests et périmètre des lectures

**115 tests ciblés réussis en11,32s :51 nouveaux +64 hérités**
(`test_legacy_batch_bridge.py`51, `test_battle_batch.py`40,
`test_battle_logs.py`24). Collecte littérale de ces trois modules, sans conftest,
découverte de tests, plugins externes, cache pytest ou bytecode. Fixtures neuves
isolées conservées, aucun nettoyage de résidus. Garde locale refusant sockets,
ouvertures des vrais emplacements privés et connexions à la vraie SQLite.
Les parcours récursifs hérités portent uniquement sur des arbres inventés.

Cas : vrais contrats v7/v13 plutôt que PRAGMA seul, version future/DB incomplète,
FK invalide/dérivée, verrou, corruption, sidecars/en-tête WAL, liste exacte60 sans
attestation, confidence SQL; rapport actuel/corrigé/ancien, pairage et chaîne
Learning Loop, intégrité canonique, reprise identique, JSON/chemins hostiles,
changement de fichier, HTML/ANSI/bidi, absence de données privées dans la projection.
Quatre CLI humain/JSON CP1252→UTF-8 strict avec garde d'audit : sockets, scans,
écritures/suppressions/renommages, découverte de racine, migration/backup/import
interdits; ouvertures locales limitées au fichier demandé et connexion SQLite
au seul URI `mode=ro` explicite. Octets des trois fichiers fixtures inchangés.

Fichiers nouveaux nécessaires et nommés : `src/pokemind/legacy_bridge.py`,
`tests/test_legacy_batch_bridge.py`, `tests/fixtures/legacy_schema7.sql`,
`docs/LEGACY_BATCH_BRIDGE.md`. Les modules/fichiers préexistants lus sont ceux du
mandat; référence historique de `database.py` pour reconstruire la fixture.
Le parseur d'exports existant est réutilisé via l'API déjà importée dans
`battle_batch`; aucune nouvelle inspection de dossier. `pyproject.toml` fournit
la configuration pytest explicite. Compilation en mémoire/tabnanny des quatre
Python changés/nouveaux, diffcheck et contrôle des seuls chemins préparés.

## CI finale et arrêt

La suite complète Windows/Ubuntu est celle du workflow existant, au SHA du commit
de livraison. Sa réussite sera contrôlée **après push et avant réponse finale**;
les logs Actions liés au SHA exact constituent la preuve durable, sans commit
autoréférent prétendant connaître son propre futur résultat. Neuf marqueurs
hérités conservés, aucun workflow modifié. Hashes canoniques attendus par OS :

- `official_rules_2026.json` : `6039ba349a5dcb3a0af605fb2b2834108a0c5c58b1fb5e1b610ea22cf996b7ba`
- `official_rules_20261022.json` : `330790df14d7d5474503d04b31c29c36eddd1ba8b003736271ab82704f55e3d7`

**AWAITING_AUDIT,execute_now=false,consumed=true**, STOP audit ChatGPT. Aucun
nouveau mandat ni droit sur les données privées. Le blocage personnel n'a pas
été levé par des fixtures; portes A–J non promues, **V1 NOT_RELEASE_READY**.
