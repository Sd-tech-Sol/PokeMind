# VERIFICATION_CORRECTIF_BACKUP_1B — audit indépendant ChatGPT (2026-10-15)

## Verdict indépendant
**CORRECTIF TECHNIQUE DU CHEMIN DE SAUVEGARDE : ACCEPTÉ / VERIFIED POUR SON PÉRIMÈTRE**, **avec réserves explicites**. **PAS** de sauvegarde réelle effectuée, **PAS** de V1 RELEASE_READY. L'anomalie horaire de la démo Windows demeure **OUVERTE** et interdit d'affirmer « tous les tests locaux en heure Toronto réussis ». Elle est distincte du chemin de sauvegarde.

## Identité du code et des preuves
- Repo `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`, HEAD code+documentation **`ea43103a14705462a9a5d09a82e463919aa0f47f`**.
- Base `f2cae122fdc818c30695efdb85cb8bd2f03922f9`, **2 commits, 12 fichiers** modifiés/ajoutés. Code/tests checkpoint `544a183d17e340433173ba030768d6e65bd97496`; un second commit publie QA/rapports.
- CI [run **38840912144**](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/38840912144) au **SHA final exact**, `completed/success`. Journaux **lus directement** :
  - Windows job `116780529006` : **480 passed / 2 skipped**, `ci_evidence=TECHNICAL_TESTS_GREEN os=Windows passed=480 skipped=2 sha=ea43103a14705462a9a5d09a82e463919aa0f47f`.
  - Ubuntu historique job `116780528762` : **479 passed / 3 skipped**, preuve `ci_evidence` au même SHA. Ceci ne constitue **pas** une extension du support Linux.
- Arbre Git au SHA final **275 entrées, non tronqué**; seul `data/local/.gitkeep` suivi sous `data/local/`; aucune base, capture ou fichier de journal réel découvert comme fichier suivi. Cela ne certifie pas l'état du PC propriétaire.

## Inspection du code
1. Suppression fautive d'origine (`temporary.unlink` après échec de renommage diagnostique) **supprimée** du chemin de sauvegarde : `create_backup` laisse `.inprogress` en place, même si une deuxième opération aurait échoué. Aucun renommage `.failed` écrasant un fichier existant. `_atomic_bytes(... keep_temporary=True)` conserve le `.tmp` du manifeste sur erreur; autres appelants non élargis.
2. `_ProcessLock(... preserve_on_error=True)` conserve le verrou sur exception; un échec ultérieur demandera **revue manuelle** plutôt que relance automatique. En fonctionnement normal, nettoyage du verrou et des alias créés contrôlé, après attestation interne complète. Le **chemin normal** contient encore `unlink()` pour les alias de travail attestés, ce qui est compatible avec la distinction « pas de suppression de résidus sur erreur »; ne jamais dire « aucun unlink dans le projet ».
3. Noms temporaires réservés par `xb`, identité contrôlée après `sqlite3.backup`; publication via `os.link` sans remplacement; `_verify_backup` refuse preuve publique en présence d'alias/hardlinks et résidus associés ou paire non concordante. L'attestation interne ne dispense pas de `backup verify` externe **sur le nouveau fichier unique**.
4. **21 nouveaux tests synthétiques** : double panne `os.replace`, échecs de copie/lien/fsync/manifest/namespace, nettoyage verrou/alias, collisions de noms, alias externe, vérification interne contre publication incomplète et attestation finale du schéma7 + FK + FTS. Les changements de tests antérieurs conservent l'état `in_progress` au lieu de `failed`. Les résultats CI prouvent leur exécution sur les runners; **ChatGPT n'a pas exécuté pytest sur le PC Windows propriétaire**.
5. Risques résiduels : verrou coopératif (races externes possibles), fichiers backup+manifeste pas transactionnels ensemble, namespace fsync Windows non certifié, ACL/chiffrement non évalués complètement, coupure de courant non garantie. Ne jamais effacer/renommer/« réparer » automatiquement des résidus, surtout après panne.

## Anomalie distincte, non résolue : fuseau Toronto
Codex documente **478 passed / 3 skipped / 1 failed** sur Windows en heure locale Toronto et **479 passed / 3 skipped** avec `TZ=UTC` fixé uniquement dans le processus de tests. Inspection indépendante du code :
- `src/pokemind/demo.py` prend `datetime.now(timezone.utc).date().isoformat()` pour plusieurs arguments `--as-of`.
- `src/pokemind/collection.py:_strict_date` compare avec `date.today()`, donc près de minuit UTC la date UTC peut être « demain » pour Toronto. Rejet de la date à l'étape `recommend` de la démo synthétique.
- **CI verte en UTC ne prouve pas que la démo Windows fonctionne dans cette fenêtre locale.** Corriger séparément avec date cohérente et tests de frontière TZ/DST, sans affaiblir la validation des dates futures en vraies données ni ajuster le fuseau système Windows. Aucun code de ce type n'a été autorisé/exécuté dans le mandat correction backup.

## Décision et action suivante
**ACCEPTER UNIQUEMENT le correctif de préservation de résidus** et conserver le blocage V1 global. La Stage 1B personnelle n'a **toujours PAS eu lieu** d'après rapport Codex (non vérifié directement sur PC). Son exécution requiert **nouvelle instruction explicite du propriétaire**, malgré l'ancien accord, car le mandat de correction imposait STOP. Si l'utilisateur l'autorise, prévol strict relancé sur les chemins explicitement choisis, **UNE création neuve** et **UNE vérification publique indépendante** avec préservation en cas d'erreur, STOP; ne pas tenter de contourner un verrou résiduel. Pas de clone ni migration7→13 avant la preuve de sauvegarde et nouvel accord.
Anomalie Toronto à réparer ensuite dans un **correctif indépendant** sur branche J, pas de LOT K automatique ni expansion Linux. Aucune modification de la branche par défaut.
