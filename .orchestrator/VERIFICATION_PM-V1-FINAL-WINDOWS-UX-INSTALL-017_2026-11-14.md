# Audit indépendant ChatGPT — PM-V1-FINAL-WINDOWS-UX-INSTALL-017

Date : 2026-11-14. Dépôt privé `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`.

Source déjà auditée `66a1ce0a2f974a480485110bbc10e8d7c086368b` (016 inclut 013+014). Décision d'installation D-312, HEAD de l'activation `2ec7d3b8aaaad67dc03164f7d8833aafbe7dc25b`. Rapport Codex et HEAD distant vérifiés au SHA exact `bea56af09fb8b55231a9b4c29cc38825847f5ce3`.

## Verdict

**017_GITHUB_SCOPE_AUDITED_PASS / CODEX_WINDOWS_TECHNICAL_EVIDENCE_CONSISTENT / INSTALLED_PENDING_OWNER_GUI_RECEPTION / NOT_RELEASE_READY.**

La livraison technique est acceptable pour passer à la **réception manuelle**. ChatGPT a lu le rapport et les documents au SHA exact, vérifié les diff/commits et l'absence de CI. **Il n'a pas ouvert, exécuté, hashé ni inspecté le disque du PC Windows ou le Setup final**, qui restent des preuves locales rapportées par Codex. L'UI interactive du nouveau binaire est **NON ATTESTÉE** malgré ses tests synthétiques et fumées.

## Vérifications indépendantes GitHub

- `compare 2ec7d3b...bea56af` = **1 commit**, 8 chemins : `.orchestrator/RESULT.md`, `STATE.json`, `HANDOFF.md`, `NEXT_ACTION.md`, `NEXT_PROMPT.md`, deux archives de suivi (rapport 016, prompt 017 consommé), `AGENTS.md`. **Aucun fichier source, test, build, dépendance ou packaging modifié** pendant 017.
- `compare 66a1ce0...bea56af` = 13 commits, **exclusivement** `.orchestrator/` et `AGENTS.md`; aucun changement dans `src/`, `tests/`, `scripts/`, `packaging/`, ni `pyproject.toml`. Le code compilé selon le rapport correspond donc au code source audité par ChatGPT en 016; le binaire local ne peut toutefois être recalculé indépendamment via GitHub.
- HEAD de la branche distante = `bea56af09fb8b55231a9b4c29cc38825847f5ce3` au contrôle.
- `get_commit_combined_status` sur le rapport = `statuses=[]`; `fetch_commit_workflow_runs` = `workflow_runs=[]`. **Aucune CI GitHub associée**, pas de « CI verte » à déclarer.
- `STATE` et `NEXT_ACTION` au SHA du rapport cohérents : `installation_attempts_for_017=1`, `production_setup_attempts=1`, `NEXT_PROMPT=CONSUMED`, D-312 consommé, `owner_gui_reception=PENDING`, publication non autorisée. Les consignes `AGENTS.md` les plus récentes imposent STOP; l'exception D-312 située plus bas est **historique** et ne permet aucune réexécution.
- Prompt 017 original intégral archivé et marqué consommé; aucun mandat exécutable actif n'est autorisé après livraison 017.

## Opérations Windows **rapportées par Codex**, non reproduites par ChatGPT

### Suite source, QA et artefacts
- `python scripts/local_gate.py --keep` dans une copie isolée : **1 885 passed, 3 skipped, 0 failed**, Qt 191, cœur 1 694; contrôles compilation et hygiène verts.
- Qt Windows natif PySide 6.12.0 : **53 tests réussis à 100 % et 53 à 125 %**; includes classements fermé/ouvert, BO1 connu et inconnu, onglet Classement et repli Statistiques, couleurs/langues/tailles, non-régression Coach 013/014.
- Scanner binaire `CLEAN`, 797 fichiers, 328 modules PYZ, PE x64, version 0.9.5, 9 ressources icône/avis conformes, module UI `window` et `charts` gelés présents; EXE de staging et EXE installé (QA) fumées 7 vues sans réseau personnel. **`FROZEN_INTERACTIVE_QA_NOT_VERIFIED`**, erreur de pilote Windows `os error 2`; une fenêtre visible et sept vues dans un smoke ne sont pas une navigation interactive confirmée.
- Inno Setup QA sur AppId **distinct** `{323C6F04-9B68-49F8-9F02-C73ABDA71659}` : ancien → nouveau 0.9.5 → désinstallation; 104 fichiers fictifs conservés, application personnelle inchangée pendant cette QA.
- Nouveau EXE `build/exe-upgrade-fdddfebb1f454f12a0a10b3f86735ac5/dist/PokeMind/PokeMind.exe`, **SHA256 `c180d58daca4d9142506c3dfdfe036c56a7261b1635fb361eb7a1607d28f21a8`**.
- Nouveau Setup NON SIGNÉ `dist/installer-candidate-0.9.5-66a1ce0-fa8e4877/PokeMind-Setup-0.9.5.exe`, **SHA256 `e31bb4ce40886616cfc4f68a92a4da96fbda3e50a71fc75b2e2349c5b95390a7`**; même AppId de production `{9B4E3B52-6C1D-4E7A-9F3B-5A2C8D1E7F40}`. Version **0.9.5 inchangée**, ne pas prétendre que l'update 1-clic doit la distinguer.

### Protection des données et installation
- Avant installation : programme 015 fermé, SHA de l'ancien EXE et AppId confirmés selon agent, aucune fermeture forcée. Racine desktop JSON-first réelle validée, sans exiger de base canonique SQLite.
- **Nouvelle archive intégrale vérifiée** : **480 fichiers**, ZIP CRC/noms/tailles/SHA comparés à la source; **8 fichiers SQLite** vérifiés en lecture seule sans sidecars; protections locales restreintes hors projet/cloud. **Copie vérifiée du programme antérieur** : **800 fichiers**; toutes les anciennes archives et les deux `synthetic_v2.*` conservées. Ne jamais pousser les manifests, chemins ou hashes personnels sur Git.
- **UNE tentative Setup** selon journal local, code retour **0**, sans `/RELAUNCH`. Nouvelle application : **797/797 fichiers** identiques à la distribution gelée, EXE installé au même SHA, version/AppId et raccourcis conformes. **480/480 fichiers personnels et dossiers inchangés** selon inventaires locaux avant/après, taille/date/SHA stables; aucune restauration, migration, import, cleanup ou publication.
- Les 480 fichiers actuels ne doivent **pas** être présentés comme égaux à la précédente sauvegarde 015 de 472 fichiers : les inventaires sont des clichés à des dates différentes. On a uniquement la preuve locale rapportée d'absence de changement **durant l'installation 017**.

## Ce qui reste à valider par le propriétaire

Ouvrir **manuellement** PokeMind depuis le raccourci habituel et vérifier sans nouveau Setup :
1. **Deck Lab** : les rangs et taux PUBLIC BO1 sont visibles en premier dans le menu fermé et ouvert; **Classement** affiche les decks connus et ceux « Données insuffisantes », sans rang ni taux fictif.
2. **Statistiques** : gros taux PUBLIC, n, période/source, graphes distincts et panneau `Sources et détails` replié qui peut être ouvert et copié. Pas de confusion avec les stats personnelles.
3. **Données existantes** : decks, galerie/images, journaux, préférences et consentements inchangés; Coach/messages arrondis. Ne pas lancer de test automatisé/LLM sur des données réelles.
4. **Auto-deck adversaire** : il n'est pas nécessaire de créer un nouveau deck pour valider l'UX; s'il est testé volontairement, rappeler que le moteur refuse sans preuve suffisante d'un deck PUBLIC 60 compatible. La capture UX seule ne prouve pas cette fonction.

**Si réception OK** : enregistrer `OWNER_GUI_ACCEPTED_017` (sans inférer l'acceptation de tous les chemins non testés). **Publication publique exige un nouveau GO distinct**; ne jamais appeler cette installation une publication. Si un vrai défaut est montré, traiter le défaut concret avant toute publication, sans nouvelle tâche d'agent/deploy automatique.

## Décision après audit

**UNE seule prochaine action : réception manuelle de l'interface par le propriétaire.** Aucun nouveau prompt Codex/Claude, aucun test/setup/rebuild, aucune sauvegarde supplémentaire, aucun nettoyage, aucun rollback ni publication. Les backups vérifiés et l'ancien programme demeurent préservés. État : `INSTALLED_TECHNICAL_GITHUB_AUDIT_PASSED / OWNER_GUI_RECEPTION_PENDING / NOT_RELEASE_READY`.
