# Preuves Codex — PM-V1-CLONE7-SYNTHETIC-READINESS-001

2026-10-18 Québec. **RAPPORTÉ_PAR_CODEX_LOCAL / NOT_VERIFIED**.
Portée : code versionné et fixtures synthétiques jetables seulement.
Audit indépendant ChatGPT requis; V1 **NOT_RELEASE_READY**.

## Départ et contrôle GitHub

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre.
- Fetch puis pull `--ff-only` de `18204c221896f70ad70d53f4f7d5a9a860d4e951`
  vers `0688f08ae05a8cd1ad3138d6a7c3f072e983dc54`, sans écrasement.
- AGENTS, continuité, adoption V2, STATE, premier NEXT_ACTION, HANDOFF, RESULT,
  D-160, audit ACL, skill exécuteur, spécification et protocole Windows consultés.
  L'ancien NEXT_PROMPT LOT J est historique et non exécuté.
- [CI de départ 39099565670](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39099565670)
  `completed/success` au SHA exact `0688f08ae05a8cd1ad3138d6a7c3f072e983dc54`
  **avant prévol et tests**. Jobs Windows `117592913010` : **484 passed / 2 skipped**;
  Ubuntu hérité `117592912853` : **483 passed / 3 skipped**. Logs `ci_evidence`
  et concordance du HEAD distant contrôlés. Aucun développement Linux ajouté.
- Prévol `python -B -m pokemind preflight --json` : **RUNTIME_READY**,
  Python **3.13.15**, SQLite **3.50.4**, FTS5 présent, base propriétaire non ouverte,
  zéro écriture disque, aucun réseau ou contact avec le planificateur.

## Défaut reproduit avant correction

Sur un vrai schéma7 **artificiel**, backup/manifeste créés par les helpers existants,
cible absente et espace libre simulé à zéro : `restore_plan` rendait
`capacity.enough=false`, `would_write=false`, mais **`reason_code=null`**.
Le blocage d'écriture existait déjà; le diagnostic destiné à l'appelant manquait.

Reproduction par les cinq nouveaux cas, avant toute modification produit :
**1 failed / 4 passed / 3 deselected**. Seule assertion en échec :
`None != INSUFFICIENT_DISK_SPACE` dans
`test_restore_plan_explains_capacity_or_collision_without_writes[False-0-INSUFFICIENT_DISK_SPACE]`.
Les comparaisons d'octets et métadonnées passent avant cette assertion.

Correctif limité à `src/pokemind/recovery.py::restore_plan`, champ `reason_code` :
annoncer `INSUFFICIENT_DISK_SPACE` pour une cible neuve sans capacité suffisante;
garder la priorité de `RESTORE_EXISTING_TARGET_BLOCKED` si la cible existe.
Aucun changement de copie, migration, publication, nettoyage, permissions ou CLI.

## Exigences et preuves réutilisées

| Exigence | Preuve synthétique |
| --- | --- |
| Plan CLI schéma7, cible absente | Nouveau `test_schema7_cli_restore_plan_preserves_bytes_metadata_and_absent_target[False]` : `mode=dry_run`, `read_only=true`, réseau faux, schéma cible 7, capacité suffisante, cible toujours absente. |
| Projection de migration sans exécution | Même test `[True]` : schéma cible 13, backup toujours 7; toute copie ou initialisation de schéma provoque un échec explicite du test. |
| Santé du backup factice | Deux cas CLI : état/manifeste vérifiés, intégrité OK, FK0 et **deux FTS OK**. |
| Absence d'écriture par le plan | Comparaison exhaustive du seul répertoire de fixture : inventaire, octets, volume, identité, liens, taille, mtime, ctime et attributs. Atime exclu; aucune cible, sidecar ou répertoire créé. |
| Capacité insuffisante et collision | Nouveau test paramétré : cible absente/disque plein, cible occupée/disque plein, cible occupée/espace suffisant; `would_write=false`, raison précise, priorité collision et mêmes octets/métadonnées. |
| Redirections Windows | Tests existants `test_clone_owner_preview_rejects_windows_reparse_before_creation` et `test_cli_rejects_actual_windows_junction_before_resolving_paths` réussis localement. Ce dernier crée uniquement une jonction synthétique et vérifie le refus CLI avant résolution. |
| Lien symbolique | Test existant `test_restore_refuses_same_target_and_symlinks_when_supported` : **skipped localement**, création non permise. La couverture jonction réelle et reparse simulé ne certifie pas un lien symbolique réel sur ce PC. |
| Préservation des historiques 7→13 | Tests existants `test_schema7_history_clone_migration_ocr_memory_backup_readiness` et `test_h3_full_synthetic_historical_rehearsal_preserves_histories_and_owner_guards` : historiques comparés, original/backup artificiels inchangés, clone factice 13, intégrité/FK/FTS et V1 toujours non prête. |
| Préservation des résidus et garde-fous | Suites existantes recovery G/H/J, commissioning H, E2E G et `test_backup_residue_preservation.py`; aucun changement aux mécanismes correspondants. |

Réutilisation de `local_tmp`, `_historical_v7` et des helpers backup existants.
La fixture historique retire réellement les tables postérieures à 7;
elle ne change pas seulement `PRAGMA user_version` sur un schéma courant.
Ajout limité à **deux tests paramétrés, cinq cas et un helper de comparaison**.

## Exécutions locales

Environnement de test : `PYTHONDONTWRITEBYTECODE=1`, `POKEMIND_TEST_OFFLINE=1`.
Tous les chemins de données passés aux appels proviennent des fixtures factices.

- Baseline ciblée, avant ajout/correction : **71 passed / 1 skipped**.
- Reproduction avant correctif : **1 failed / 4 passed** comme décrit ci-dessus.
- Ciblés après correctif : **97 passed / 1 skipped**, **35,94 s** :
  `python -B -m pytest -q tests/test_recovery.py tests/test_lot_g_recovery.py tests/test_lot_h_recovery.py tests/test_lot_j_recovery.py tests/test_lot_h_commissioning.py tests/test_lot_g_e2e.py tests/test_backup_residue_preservation.py`.
- Suite complète : **488 passed / 3 skipped**, **189,15 s**; commande `python -B -m pytest -q`
  avec `--basetemp` unique sous le répertoire des tests jetables, afin que
  `tmp_path` reste lui aussi dans le projet. Aucun nom aléatoire publié.
  Deux skips OCR absent/non attesté, un skip symlink Windows non permis;
  aucun de ces cas n'a été contourné ou installé.
- `python -B -m compileall -q src tests scripts` : succès.
- `python -B scripts/check_repo_hygiene.py` : succès, **259 fichiers suivis** avant
  ajout de cette fiche, **260** après staging explicite des sept fichiers autorisés.
- `git diff --check` : succès; aucun journal brut ni artefact synthétique publié.

## Frontières de preuve et protocole ultérieur

Aucune consultation, liste, lecture SQL, empreinte ou observation ACL personnelle.
Aucune base originale, archive historique ou paire moderne personnelle touchée.
Zéro commande privée `restore plan`, backup, clone ou migration; aucun import réel,
installation, OCR réel, planificateur, réseau fournisseur, merge ou force-push.
`restore verify` et les migrations ne sont exécutés que par les **tests synthétiques
existants**, jamais comme démonstration distincte sur un fichier du propriétaire.

Relecture statique confirmée : `commissioning_preflight` appelle `database_status`
et `_sqlite_checks` sur son argument DB; **lecture seule signifie quand même lecture
du contenu**. `restore plan` lit la paire backup/manifeste. `restore verify` crée un
clone temporaire. Aucun de ces constats ne donne une permission privée.
`initialize_schema` peut aussi créer une sauvegarde de migration avant de modifier
le schéma; les essais correspondants sont confinés aux fixtures existantes.

Après audit de cette livraison seulement, toute éventuelle opération personnelle
requiert un mandat distinct nommant la paire à lire, la cible neuve, les contrôles
de chemins/collision/capacité et le nombre d'essais. Les observations ACL antérieures
restent `OBSERVATION_ONLY`; protection effective, chiffrement, fraîcheur et durabilité
non certifiés. Le mandat privé précédent reste **BLOCKED, zéro plan**;
cause historique `ACL_OBSERVATION_FAILED` inconnue et ancien incident backup
`POST_VERIFY_RESIDUE_OR_UNSAFE_FILE` toujours `CAUSE_NON_RECONSTRUITE`.

Livraison : STATE et premiers RESULT/HANDOFF/NEXT_ACTION **AWAITING_AUDIT**,
`execute_now=false`, arrêt exécuteur. **CI du commit contenant cette fiche :
PENDING_CI à la publication**, à consulter sur GitHub Actions au HEAD distant exact.
La CI prouve des tests sur fixtures et ne certifie aucune opération privée Windows.
**STOP pour vérification indépendante ChatGPT; V1 NOT_RELEASE_READY.**
