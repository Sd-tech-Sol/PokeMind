# ADDENDUM — inventaire local des résidus analysé (2026-10-16)

**Source : compte rendu Codex transmis par le propriétaire.** ChatGPT ne peut pas vérifier directement les métadonnées Windows. GitHub distant au moment de la lecture : `e027eee9315de85cd37c0584f22253c2d8f3408a`, CI verte.

**Résultat précis :** une seule entrée dans `data/local/backups/`, inventaire non récursif annoncé complet :
- `pokemind-pm0003f-before-reparse-20261011T050146Z.sqlite3`, fichier régulier, **540 672 octets**, modifié UTC `2026-10-11 05:01:46.880540` ;
- Windows `st_file_attributes=0x20` (Archive), `reparse_tag=0x0`, `st_nlink=1` par `os.lstat` ; aucun symlink, junction/reparse ;
- aucun `*.manifest.json` correspondant au nom `pokemind-pm0003f-before-reparse-20261011T050146Z.sqlite3.manifest.json` ; aucune autre entrée `.lock`, `.inprogress`, `.failed`, `.tmp`, WAL/SHM/journal ou manifeste orphelin ;
- catégorie **`unattested_database`**, et **SEULE cause identifiée** du prévol arrêté `DESTINATION_RESIDUES_OWNER_REVIEW_REQUIRED`. Cette catégorie **n'établit pas** une corruption, une sauvegarde valide, ni l'origine historique du fichier. Le code générique du prévol ne figure pas tel quel dans `recovery.py`, donc sa règle exacte n'a pas été prouvée hors rapport Codex.

**Code vérifié dans GitHub :** `recovery.py:648–649` classe `*.sqlite3` dépourvu du manifeste homonyme en `unattested_database`. `backup_plan` accepte une destination distincte et n'exige pas son existence; `create_backup` peut créer la destination sûre si autorisée. La CLI accepte les destinations sous `data/local/`. Ces capacités ne prouvent pas le succès d'une sauvegarde réelle.

**Choix recommandé, soumis à accord explicite du propriétaire :** préserver `data/local/backups/pokemind-pm0003f-before-reparse-20261011T050146Z.sqlite3` sans aucune opération, et **proposer** `data/local/backups/managed-v1/` comme destination neuve isolée pour la **première sauvegarde moderne** avec manifeste. Ce dossier n'est **pas encore autorisé** et ne doit pas être créé automatiquement. Si propriétaire accepte, Codex devra : prévol non destructif chemin/enfants/ancêtres, destination neuve/non redirigée, base source santé schéma7 FK/FTS/espace, plan de backup, une seule création et vérification publique sur le nom réellement retourné, preuve source inchangée, STOP. Aucun contournement des contrôles à l'intérieur de la NOUVELLE destination. Si le dossier existe déjà ou si blocage/résidu détecté, STOP sans écrire.

**Interdits toujours** : vérifier/ouvrir/hacher l'ancienne base non attestée, la déplacer, la renommer ou la supprimer; créer un faux manifeste ancien; changer de code ou contourner le prévol; faire un backup réel avant nouvel accord de destination, migrer 7→13, purger, restaurer, scheduler/OCR. **Stage 1B suspendu. V1 NOT_RELEASE_READY.**

---

## Archive : audit initial avant inventaire
# Audit ChatGPT — STOP Stage 1B sur résidus de destination (2026-10-15)

## Faits rapportés par Codex (non directement vérifiés sur Windows par ChatGPT)
- HEAD local propre et synchronisé à `5908b14a488aaf49e300f253df6ec85c62678822` ; ACL sans groupe large apparent.
- **Prévol STOP**, raison **`DESTINATION_RESIDUES_OWNER_REVIEW_REQUIRED`** sur **`data/local/backups`**. Au moins une entrée échoue aux contrôles de résidu, de lien ou de paire SQLite/manifeste.
- Les contrôles source SQLite/FTS/FK, le `backup plan`, `backup create` et `backup verify` **n'ont PAS été exécutés dans cette tentative**. Aucun changement déclaré à la base, aux sauvegardes existantes, ni à Git.
- **Il est impossible d'identifier le fichier incriminé à partir de ce code générique**; le résultat ne démontre pas une corruption ou une fuite.

## Vérification indépendante du code distant
Branche J HEAD `5908b14a488aaf49e300f253df6ec85c62678822` (au moment de cet audit), GitHub CI `38842941609` `completed/success`, documentation seule après le correctif `ea43103a`.

`src/pokemind/recovery.py` :
- `recovery_residues(directory)` classe sans lecture de contenu les noms `*.inprogress`, `*.failed`, `*.tmp`, `*.lock`, sidecars SQLite, manifeste orphelin, lien symbolique, dossier de rétention/quarantaine, ou `*.sqlite3` sans `*.manifest.json`; `scan_complete` est borné à 10 000 entrées.
- Une entrée `unattested_database` peut être un **ancien backup légitime sans manifeste moderne**; une entrée `lock_requires_owner_review` peut être un verrou historique. La catégorie n'autorise ni suppression, ni renommage, ni inférence de corruption.
- `backup_status(directory)` appelle `verify_backup` sur les sauvegardes associées et **lit leur contenu**. Ne PAS l'exécuter pour le simple inventaire sans nouvelle décision claire de lecture des anciennes sauvegardes.
- La chaîne d'erreur `DESTINATION_RESIDUES_OWNER_REVIEW_REQUIRED` n'est pas une constante de ce fichier : elle provient probablement du prévol orchestré par Codex. Évaluer la règle de ce prévol avant de changer du code; ne pas relâcher les garde-fous juste pour franchir le blocage.

## Mandat diagnostic suivant (LECTURE DES MÉTADONNÉES SEULEMENT)
Sur Windows, depuis le repo J, inventorier **une seule profondeur** `data/local/backups/` sans suivre de lien, sans ouvrir SQLite ou les manifestes. Relever pour CHAQUE entrée : nom de fichier relatif au dossier backups, type de fichier (`lstat`), lien/jonction/reparse oui/non, taille si fichier régulier, date de modification, `st_nlink` si disponible, présence nominale du pair `.sqlite3 ↔ .manifest.json`, et catégorie `recovery_residues`. Vérifier le nombre total et `scan_complete`, puis préciser quel critère exact du prévol a généré le STOP, en distinguant `orphan_manifest`/`unattested_database`/`interrupted_work`/`lock`/`unsafe_link` et erreurs de pair/permission. Signaler anomalies sans conclusion de corruption.

**Interdictions** : aucune ouverture/lecture des octets SQLite, manifeste ou source; aucun `backup status`/ `backup verify` sur d'anciens backups; aucun hash, `backup create`/`plan`, suppression, renommage, déplacement, nettoyage de résidus, chmod/ACL, commit/push, migration, installation. Aucune inspection d'autres dossiers, ni données personnelles sur GitHub. Rapport uniquement dans Codex à l'utilisateur; **STOP** pour décision ChatGPT et propriétaire. Le propriétaire devra autoriser séparément tout contrôle de contenu d'anciens fichiers ou toute action corrective.

**V1 NOT_RELEASE_READY.** Sauvegarde réelle Stage 1B toujours suspendue; ne pas réutiliser automatiquement le consentement précédent après cette nouvelle alerte.
