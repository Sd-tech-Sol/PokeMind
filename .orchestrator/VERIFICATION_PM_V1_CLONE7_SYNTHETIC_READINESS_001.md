# Audit indépendant ChatGPT — PM-V1-CLONE7-SYNTHETIC-READINESS-001

**Date : 2026-10-18 (Québec). Verdict : `VERIFIED` pour le correctif et les tests du produit sur fixtures synthétiques. V1 : `NOT_RELEASE_READY`.**

## Références GitHub réellement contrôlées
- Repo `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`; base du mandat `0688f08ae05a8cd1ad3138d6a7c3f072e983dc54`. Livraison Codex **`9cd0585a437fc427150b817885761d8516573539`**, un seul commit, sept fichiers : `src/pokemind/recovery.py`, `tests/test_lot_j_recovery.py`, nouvelle preuve `.orchestrator/EVIDENCE_PM_V1_CLONE7_SYNTHETIC_READINESS_001.md`, plus `RESULT.md`, `HANDOFF.md`, `NEXT_ACTION.md`, `STATE.json`.
- Inspection du patch `restore_plan` : quand `target.exists()`, le `reason_code` demeure `RESTORE_EXISTING_TARGET_BLOCKED`, indépendamment du disque; pour cible absente et `capacity.enough==false`, il devient `INSUFFICIENT_DISK_SPACE`. Sinon `None`. Les protections `would_write` et `target.exists()` **ne changent pas**; aucun chemin d'écriture ou migration modifié.
- Nouveau test de commande réelle `restore plan` sur fixture `_historical_v7`, deux cas `migrate_clone=false/true`. Vérifie `dry_run/read_only/network_used=false`, schéma source 7, projection 7/13, FK 0, deux FTS sains, cible absente; `_copy_database` et `initialize_schema` explicitement remplacés pour échouer si appelés. Le helper de comparaison lit **uniquement les fixtures** et vérifie octets/métadonnées en excluant atime.
- Nouveau test paramétré (trois cas) : absent + disque plein -> `INSUFFICIENT_DISK_SPACE`, existant + disque plein/avec espace -> `RESTORE_EXISTING_TARGET_BLOCKED`, et conservation des octets/meta. Total **5 nouveaux cas**, deux fonctions paramétrées.
- D'après la preuve locale Codex, la régression a été reproduite avant correctif (**1 échec attendu/4 réussites**) et les tests ciblés **97 passed / 1 skipped**, suite locale **488 passed / 3 skipped**. **Ces observations sur la machine Windows sont attestées par Codex, non directement rejouées par ChatGPT.**

## CI GitHub au SHA de livraison
- [Run 39100177241](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39100177241) : `completed/success`, `head_sha=9cd0585a437fc427150b817885761d8516573539`.
- Windows job `117594673874` : **489 passed / 2 skipped** (104,82 s), log `ci_evidence=TECHNICAL_TESTS_GREEN os=Windows passed=489 skipped=2 sha=9cd0585...`.
- Ubuntu historique job `117594673951` : **488 passed / 3 skipped** (87,27 s), `ci_evidence=TECHNICAL_TESTS_GREEN os=Linux passed=488 skipped=3 sha=9cd0585...`.
- `git diff --check`, hygiène dépôt et compilation passent dans la CI. Le test symbolique Windows n'est pas supposé couvert par la session locale faute de privilèges; une vraie jonction synthétique est couverte.
- Le compte CI Windows peut différer du compte Windows local à cause des permissions et skips; ce n'est pas une régression constatée.

## Limites du verdict
- **`VERIFIED` pour le code, tests synthétiques, diff et CI**, non pour une base privée, la restauration réelle ou une migration 7→13 personnelle.
- Aucune donnée personnelle ajoutée au commit. Codex affirme ne pas avoir consulté ni inventorié les fichiers privés durant ce mandat; GitHub ne permet pas de corroborer physiquement cela.
- Le précédent mandat de `restore plan` privé `PM-V1-CLONE7-PLAN-001` reste **`BLOCKED`** et compte **0 plan exécuté**, consentement précédent consommé.
- Trois observations `icacls` réussies rapportées lors d'un ancien diagnostic **ne certifient pas l'adéquation ACL**. Le `ACL_OBSERVATION_FAILED` antérieur conserve cause `UNKNOWN`, le postcheck `POST_VERIFY_RESIDUE_OR_UNSAFE_FILE` conserve `CAUSE_NON_RECONSTRUITE`.
- Les normes officielles, le catalogue FR/EN, les jeux de combats/données propriétaires, OCR réel, planificateur Windows et tests de sécurité/durabilité restent des portes `PARTIAL`/`BLOCKED` dans `docs/LOT_J_ACCEPTANCE_MATRIX.md`.

**Décision : ACCEPTED / VERIFIED pour le mandat synthétique ciblé.** Ne pas lancer d'anciens mandats; aucun clone/migration, installation, lecture du contenu privé ou merge ne devient autorisé. Pour progresser vers la V1 sans répétition de diagnostics synthétiques autour du backup, priorité désormais aux **gates métier réelles sur connaissances publiques** et aux tests de livraison correspondants, sous quotas/fournisseurs autorisés, sans données personnelles. Auditer ensuite GitHub, conserver `NOT_RELEASE_READY` tant que les gates ne sont pas résolues.
