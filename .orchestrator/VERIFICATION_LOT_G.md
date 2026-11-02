# VERIFICATION_LOT_G — audit indépendant GitHub ChatGPT (2026-10-14)

## Verdict
**LOT G G0–G5 LIVRÉ, ACCEPTÉ EN REVUE STATIQUE POUR PASSATION AU LOT H AVEC LIMITES BLOQUANTES PRODUIT.**
V1 **NOT_RELEASE_READY**. Acceptation des mécanismes et de la protection fail-closed **ne signifie pas** autorisation d'exécuter des restores/retentions sur une base réelle, de migrer la base personnelle, d'installer OCR ou scheduler, de capturer TCG Live ni de merger.

## Références et contrôles indépendants
- Repo privé `Sd-tech-Sol/PokeMind`, branche livraison `work/pm-v1-lotg-real-vision-readiness`, base `9ad99bbc0a893b1d4a8418828853c4598fa5c4a0`, **HEAD de livraison `9b19644ed3990befc569d25a29928e08400b1a42`**. GitHub compare : **6 commits**, **35 fichiers changés**, branche 6 en avance / 0 retard sur base G.
- Run GitHub Actions au **SHA exact** `38600129548`, `completed/success`. Jobs `115976928188` Linux et `115976928637` Windows, tous deux **success**. Logs indépendamment consultés : **389 passed, 1 skipped** sur chaque plateforme (OCR local absent). Compilation, hygiène Git et diff check en succès dans les deux jobs.
- Codex rapporte **388 passed, 2 skipped** sur son Windows local; deuxième skip local lié au privilège symlink. Ce chiffre demeure un **rapport Codex**, à distinguer des logs CI.
- Arbre Git récursif **221 entrées, truncated=false** : aucun fichier de base SQLite, capture réelle, image ou secret suivi détecté dans les chemins; `data/local/.gitkeep` seul sous `data/local/`. Un inventaire de chemins ne prouve pas l'absence universelle de secrets dans tous les octets ni les opérations exactes sur le PC.
- Lecture indépendante de `src/pokemind/recovery.py`, `local_ocr.py`, `readiness.py`, suites G0 et des matrices/rapports G. Aucun pytest local de ChatGPT ni essai terrain réel effectué.

## G0 — sûreté récupération : améliorée; restore réel existant encore BLOQUÉ
- `restore_backup` refuse explicitement `apply` quand `target` existe (`RESTORE_EXISTING_TARGET_BLOCKED`), même si un contrôle ponctuel ne voit pas de writer. Pour cible neuve, publication par `os.link` évite le remplacement destructif d'une cible apparue tardivement.
- `_publish_isolated_restore` intercepte les exceptions postpublication, contrôle l'empreinte de l'original dans les scénarios synthétiques, et remonte `RESTORE_ROLLBACK_INCOMPLETE` avec quarantaine conservée si retour arrière incertain. **Le remplacement d'une ancienne cible n'est pas ouvert publiquement; cette branche de code n'est exercée qu'avec `_allow_existing_fixture=True` en tests.**
- WAL/SHM/journal et header WAL des backups sont désormais refusés; snapshot par SQLite backup normalisé en DELETE et source/manifeste réattestés après contrôle. Tests d'injection opérationnels vus dans `test_lot_g_recovery.py`; la CI les exécute.
- **Réserves bloquantes** : aucune exclusion prouvée des programmes externes lors d'une restauration sur base existante; aucune garantie power-loss/atomicité multifichier; `retention apply` reste une suppression à étapes et peut laisser des artefacts intermédiaires. Ne pas autoriser restaurations/purges réelles à ce stade. H0 doit durcir et tester; fail-closed si invariant impossible.
- Point secondaire de maintenance à surveiller : `_safe_directory` exige l'accès en écriture même pour certaines opérations de consultation, et `_catalog_candidate` parcourt les impressions pour chaque ROI, donc mesurer coût et gestion des erreurs avant usage utilisateur.

## G1 — OCR
- `local_ocr.py` offre un contrat PNG/ROI/TSV Tesseract local avec bornes, timeout, seuils et correspondance de plusieurs champs du catalogue. Le chemin `ocr_uncertain` ne s'auto-promeut pas en lecture visuelle confirmée. Tests de reconnaissance = **faux OCR simulé**, pas Tesseract installé/benchmarké, aucune vraie capture utilisateur. **PARTIAL_WITH_EVIDENCE**, pas une reconnaissance réelle TCG Live. Préparer benchmark/calibration locale, puis essai réel uniquement sur consentement explicite séparé.

## G2 — corpus, règles et métagame
- Progrès techniques sur stale/détails, reprise deep et enregistrement de la file de validation normative, avec provenance datée. Observation réseau limitée **déclarée par Codex** : 4 GET TCGdex et 2 GET Limitless; non rejouée indépendamment; elle ne démontre aucune couverture exhaustive.
- FR/EN, reprints, promos, errata, restrictions/Expanded/Live, règles officielles et méta demeurent PARTIAL; Trainer Hill BLOCKED sans accès autorisé. Absence de dénominateur certain = `unknown`, HTTP/hash != validation de contenu.

## G3–G5 et V1
- Tests E2E de structure schéma 7→13 en **clone synthétique**, vérifications contenu FTS/FK, trois tours de mémoire OCR simulée, confidentialité et CI verte. Aucune comparaison réelle Windows de données privées faite par ChatGPT.
- `readiness.py` contient désormais des gates par dimensions; `vision_owner_trial`, `scheduler_cadence`, `existing_target_restore`, `trainer_hill`, `independent_release_audit` restent fail-closed faute de producteurs de preuves. Import collection/crédits demeure facultatif. Cette retenue est correcte, mais les critères de release réels sont **encore à construire/attester**.
- G0–G5 : acceptation des mécanismes au périmètre prouvé, **pas d'acceptation de la V1 produit**. Les objectifs antérieurs A–G ne sont pas supprimés. Rapport Codex, limites et suite dans `docs/LOT_G_ACCEPTANCE_MATRIX.md`, `LOT_G_QA_REPORT.md`, `LOT_H_COMPLETION_PLAN.md`.

## Décision et suite
Préparer **LOT H autonome H0–H5** sur branche distincte `work/pm-v1-loth-completion-readiness`; ChatGPT reste vérificateur indépendant de sa livraison. Priorités : restauration opérationnelle sûre (ou refus maintenu), vision locale vérifiable sans installation implicite, couverture et validation normative réelles, preuves/activation propriétaire seulement sur ordres séparés, cadence et portes V1, tests GitHub Windows/Linux au HEAD final. Toute fonction non attestée reste `PARTIAL_WITH_EVIDENCE` ou `BLOCKED_WITH_REASON`.

**Aucune nouvelle permission implicite** pour backup/restore/retention/migration/import réels, capture/compte Pokémon, modèle/OCR installé, scheduler, crédits/achat, merge ou modifications de branche par défaut (`work/pm-0001`). Aucun merge effectué pendant cet audit.
