# Validation propriétaire V1 sur Windows — après audit ChatGPT de J

**NOT_RELEASE_READY. Aucun acte réel ci-dessous exécuté par LOT J.**
Cette page prépare cinq décisions distinctes. ChatGPT les soumet après son audit;
une décision n'autorise pas les quatre autres. Chaque ordre doit nommer les
fichiers et les effets permis. Collection et crédits facultatifs, aucune dépense.
Tout résultat comportant des données/chemins personnels reste sous `data/local/`.

## Commencer dans Codex sans données personnelles

Ouvrir ce dépôt sur Windows, lire AGENTS/HANDOFF/NEXT_ACTION, puis demander :
« Lance le prévol et la démo synthétique hors ligne. »

```powershell
python -m pokemind preflight --json
python -m pokemind demo --json
python -m pokemind match preflight --json
```

Attendus : `RUNTIME_READY`, `SYNTHETIC_REHEARSAL_PASSED`, `NOT_RELEASE_READY`;
OCR absent ou non attesté sans exécution. Ces commandes n'ouvrent pas la base
personnelle. Les autres commandes de données **sans `--db` choisissent la base
personnelle par défaut**; elles ne font pas partie de la démo. Les chemins
`SOURCE_CHOISIE`, `SNAPSHOT_CHOISI`, `CLONE7_NEUF` et `CLONE13_NEUF` ci-dessous
sont des substituts à choisir dans `data/local/`, pas des fichiers déjà validés.

## Décision 1 — choisir la base et autoriser une sauvegarde personnelle

Entrées : base source précise, dossier de backups privé, espace libre; portée
lecture du source puis création d'un backup et de son manifeste sans modifier
le source. Examiner ACL/héritage et protection du stockage local avant copie;
PokeMind ne les atteste pas et n'active aucun chiffrement. Prévisualisation 1 :

```powershell
python -m pokemind owner-plan --step backup --db "data/local/SOURCE_CHOISIE.sqlite3" --json
python -m pokemind backup plan --destination "data/local/backups" --db "data/local/SOURCE_CHOISIE.sqlite3" --json
```

Après ordre spécifique de création seulement : même `backup create` avec
`--destination`, `--db`, `--apply --confirm-owner`. Preuve : source inchangé,
SQLite/FK/FTS sains, manifeste et SHA concordants. Prévisualisation 2, requérant
l'autorisation de lire le backup choisi :

```powershell
python -m pokemind owner-plan --step verify --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --db "data/local/SOURCE_CHOISIE.sqlite3" --json
python -m pokemind backup verify --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --db "data/local/SOURCE_CHOISIE.sqlite3" --json
```

Rollback : abandon avant création; après création garder source/backup/résidus,
aucune purge automatique. Risques : copie privée supplémentaire, panne entre
deux fichiers, accès disque/ACL et dernière écriture externe non exclus. Un backup
vérifié ne prouve pas que le source n'a pas changé ensuite.

## Décision 2 — clone neuf, migration hors ligne et choix du clone actif

Entrées : backup vérifié et deux nouveaux noms de clones; source conservé.
La migration est limitée à un clone distinct, jamais à l'original. Prévisualisation 3 :

```powershell
python -m pokemind owner-plan --step clone --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --clone "data/local/CLONE7_NEUF.sqlite3" --db "data/local/SOURCE_CHOISIE.sqlite3" --json
python -m pokemind restore plan --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --db "data/local/CLONE7_NEUF.sqlite3" --json
```

Après ordre précis : `restore apply` sur ce **nom neuf** avec
`--apply --confirm-owner`, sans `--migrate-clone`. Si le backup est en schéma7,
ce premier clone conserve 7. Prévisualisation 4 de migration dans un AUTRE clone :

```powershell
python -m pokemind owner-plan --step migration --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --db "data/local/CLONE7_NEUF.sqlite3" --json
python -m pokemind restore plan --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --migrate-clone --db "data/local/CLONE13_NEUF.sqlite3" --json
```

L'essai `restore verify --backup ... --migrate-clone` écrit un clone temporaire;
il exige lui aussi un ordre, ce n'est pas une vérification purement en lecture.
Après autorisation de migration : `restore apply --backup ... --migrate-clone
--db "data/local/CLONE13_NEUF.sqlite3" --apply --confirm-owner --json`.
Comparer localement versions, combats, liens, observations, recherche et FK/FTS
avant sélection. Prévisualisation 5 :

```powershell
python -m pokemind owner-plan --step activate --backup "data/local/backups/SNAPSHOT_CHOISI.sqlite3" --db "data/local/CLONE13_NEUF.sqlite3" --json
python -m pokemind status --db "data/local/CLONE13_NEUF.sqlite3" --json
```

Activation après ordre : transmettre explicitement `--db` pointant le clone13
aux commandes de consultation choisies. Aucun renommage/remplacement ni changement
automatique de la base par défaut. Rollback : cesser d'utiliser le clone et choisir
explicitement la base précédente; garder tous les artefacts. Risques : sauvegarde
périmée, concurrence externe, confidentialité, disponibilité de liens durs et
durabilité Windows. Cible existante et rétention apply demeurent bloquées même
avec confirmation. [Protocole et modèle d'audit local](LOT_J_RECOVERY_PROTOCOL.md).

## Décision 3 — exports de decks, journaux et versions réellement jouées

Entrées : export volontaire de 60 cartes, journaux originaux et choix du deck/base
validés. Portée : importer localement, sans brut durable, sans modifier le client
Pokémon. Préparer d'abord les fichiers et afficher `deck import --help`,
`log import --help` et `deck link-battle --help`; **ces imports n'ont pas de dry-run**.
Leur exécution est elle-même l'acte d'écriture à autoriser, pas un prévol.

Après ordre : `deck import FICHIER --deck ID --db BASE --json` et
`log import FICHIER --deck ID --db BASE --json`, puis réimport du même journal
pour confirmer déduplication et `profile summary/review --deck ID --db BASE --json`.
Ces imports écrivent directement après l'ordre reçu; aucun `--apply` n'est
requis par leur CLI. Ne jamais scanner le dossier de journaux en lot.

Attestation combat/version : `deck link-battle --deck ID --battle-id N --version V
--db BASE --dry-run --json`, puis seulement la paire confirmée avec
`--apply --confirm-owner`; révocation volontaire `deck unlink-battle`.
Preuve : 60 exactes ≠ légalité complète; résultat/log idempotent, n et période,
au moins cinq parties valides pour premier constat prudent; aucune version
inférée des cartes observées. Rollback des liens par révocation, import historique
conservé; annuler l'essai en revenant à un nouveau clone de backup sans écraser
un fichier. Risque : association/dates erronées à corriger explicitement.

## Décision 4 — moteur OCR puis trois décisions d'entraînement permises

Deux actes séparés dans cette décision : sélection/installation, puis captures
volontaires et traitement. Entrées avant installation : URL exacte du distributeur,
version Windows x64/architecture, licence, volume, SHA attendu du binaire/artefacts,
packs eng/fra et dépendances. Valeurs exactes encore inconnues; ne pas installer
« la dernière version » sans fixer ces preuves. Le prévol J ne télécharge rien.

Modèle de politique privée à compléter sous `data/local/ocr/trust.json`;
`dependencies_reviewed=false` reste bloquant tant que la revue n'a pas eu lieu :

```json
{
  "schema_version": 1,
  "executable": "C:/CHEMIN_CHOISI/tesseract.exe",
  "sha256": "SHA256_ATTENDU_A_FIXER",
  "version": "VERSION_A_FIXER",
  "architecture": "AMD64",
  "source_url": "https://DISTRIBUTEUR_A_VERIFIER/ARTEFACT_VERSIONNE",
  "license": "LICENCE_A_VERIFIER",
  "dependencies_reviewed": false,
  "tessdata_dir": "C:/CHEMIN_CHOISI/tessdata",
  "language_pack_hashes": {"eng": "SHA256_ATTENDU_A_FIXER", "fra": "SHA256_ATTENDU_A_FIXER"}
}
```

Prévisualisation sans exécution, après permission de lire ces fichiers précis :

```powershell
python -m pokemind match preflight --ocr-trust "data/local/ocr/trust.json" --json
```

Après ordre distinct d'exécution du moteur revu, ajouter
`--execute-reviewed-ocr`; même paire d'options pour `match benchmark-ocr`.
Preuve attendue : version/packs/SHA concordants, 22 cas/88 champs réellement
tentés, erreurs/abstentions/faux positifs et latence sans inventer CPU/RSS.
Ce corpus artificiel ne calibre aucune vraie capture.

Après consentement de captures d'entraînement où l'assistance est permise :
attacher volontairement un PNG à Codex (repli fichier si collage échoue), choisir
profil ROI et base validés, `owner-plan --step vision_trial --db BASE --json`,
puis prévisualiser `match observe --image PNG --calibration PROFIL --turn N
--ocr-trust POLITIQUE --execute-reviewed-ocr --db BASE --dry-run --json`.
Ouvrir/mémoriser la séance seulement avec ordres propres (`match start/observe`,
`--apply --confirm-owner`), puis `match review/advise/show`. Trois décisions avec
séquence exacte conditionnelle, repli et justification; prochaine image seulement
après effet déterminant. Cartes cachées inconnues; erreur→correction/révocation.

Rollback : cesser le moteur, révoquer la revue/correction choisie; fichiers sources
sous contrôle propriétaire, aucun effacement implicite. Risques : OCR mal lu,
versions/impressions confondues, chaîne d'approvisionnement non indépendamment
certifiée. Ni revue propriétaire ni benchmark ne donnent `visual_certain` ou
qualification indépendante; relever les résultats et faire auditer.

## Décision 5 — heures et validation du planificateur Windows

Entrées : heures quotidienne et mardi/vendredi choisies par le propriétaire,
fuseau Windows Toronto équivalent `Eastern Standard Time`, stockage/base publique
validés et absence de données privées dans la collecte. Les heures suivantes
sont des **exemples à remplacer**, pas un choix effectué :

```powershell
python -m pokemind knowledge scheduler --action install --daily-time 08:15 --deep-time 19:30 --windows-timezone "Eastern Standard Time" --dry-run --json
python -m pokemind knowledge scheduler --action status --dry-run --json
python -m pokemind knowledge scheduler --action uninstall --dry-run --json
python -m pokemind knowledge cadence --start-utc 2026-10-31T00:00:00Z --daily-time 01:30 --deep-time 05:00 --days 14 --json
```

Ces plans sont exportables par redirection vers un fichier local choisi; ils ne
contactent même pas `tzutil` ou le planificateur et déclarent le fuseau **asserté,
non vérifié**. Sans heure/fuseau, refus. Le verrou logiciel d'installation réelle
reste fermé dans J : après accord, ChatGPT doit autoriser/revoir son ouverture
ciblée et le choix de la base publique; ne pas contourner avec `schtasks` manuel.

Preuves terrain attendues après cette ouverture auditée : fuseau OS réellement
observé, deux tâches à privilège minimal, quotidienne + mardi/vendredi Toronto,
DeepTime transmis, cycles/retry idempotents sans Codex/LLM, alertes d'échec,
statut OS et désinstallation réelle démontrés. Rollback futur : désinstallation
des deux tâches nommées, garder les rapports; jamais supprimer les données.
Risque : fuseau/DST, poste arrêté, exécution différée, accès disque/réseau et
concurrence. La simulation ne prouve pas ces comportements OS réels.

## Ce qui reste indépendamment de ces décisions

L'historique complet FR/EN, les normes/errata/promos/reprints/Live et la couverture
compétitive restent partiels; Trainer Hill manque d'accès primaire autorisé.
Remplacement existant, purge multifichier, ACL/chiffrement et durabilité complète
ne sont pas qualifiés. Garder ces portes dans la V1. L'audit J doit distinguer ces
limites des essais propriétaire; aucune création automatique de LOT K, merge ou
release. Une réparation ciblée exige un défaut précis et un nouveau mandat.
