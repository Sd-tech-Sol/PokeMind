# Passation — 025 publication 0.9.6 : STOP à l'étape 4, rien de public (2026-11-20, D-320)

Réception **OWNER_GUI_ACCEPTED_096** (déclaration du propriétaire), puis GO de publier 0.9.6 en préversion (D-320),
exécuté par Claude Code, sans audit indépendant.
- Vert : prévol (source = `8d2bd62`, public `main` = `295db53`, pas de v0.9.6); commit privé `81580b0` (CHANGELOG,
  notes 0.9.6, ligne Status des README); porte 1946 / 0 / 3; Setup `688d8651…d137` revérifié, scan CLEAN.
- **Rouge à l'étape 4** : deux captures `docs/design/pokemind-brainball/captures/style-global/06-reglages-4-data-*`
  affichent un chemin absolu contenant le nom du compte Windows. **Aucun push public, aucun tag, aucune release.**
- **Prochaine action : décision du propriétaire** (refaire ces captures, puis nouveau GO). Détails : [RESULT](RESULT.md).

# Historique — 024 version 0.9.6 : installée localement, réception du propriétaire en attente (2026-11-19, D-319)

Mandat **PM-RELEASE-096-LOCAL-INSTALL-024** (GO explicite du propriétaire, **D-319**, extensions « option a » et
correction du plantage de la QA native), exécuté par Claude Code, sans audit indépendant.
- Commits : fusion `1e3d483`; 0.9.6 `215e1f4`; mise en page `5eee9c9`; Jobs libérés par `job_finished` au lieu
  du pool (`c34f32e`, `8d2bd62`). **SHA source de l'EXE : `8d2bd62e4599b98aab96feea5e82b86ba5685f8f`.**
- Preuves : porte verte 1946 / 0 / 3; QA native 5 × verte (542 / 0 à 100 % et 125 %); scan CLEAN; fumée et QA Inno
  vertes; `FROZEN_INTERACTIVE_QA_NOT_VERIFIED`.
- Binaires : EXE SHA256 `07cb3d8b…02d6`, Setup SHA256 `688d8651…d137` (valeurs complètes dans RESULT).
- Protection et installation : sauvegarde et copie 0.9.5 vérifiées (hors dépôt, hors Git); Setup lancé 1 fois,
  code 0; 0.9.6 installée, données conservées. Détails : [RESULT](RESULT.md).

**Prochaine action : réception par le propriétaire**, jamais inférée. Aucune deuxième installation. Publication non
autorisée.

## Historique — audit indépendant 019 (D-315 de la branche de publication, 2026-11-15)

Source : `.orchestrator/VERIFICATION_PM-V1-PUBLIC-RELEASE-019_2026-11-15.md` (audit ChatGPT). Public
`Sd-tech-Sol/PokeMind`, `main` et tag `v0.9.5` = `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac`; arbre public
`e908741ce5024daa4af36c16332fa7498d4cf940` = arbre privé `f223aaa44f058afd32163a5d57d59b9a74ae70b4`. Release
préversion, Setup non signé, SHA256 `e31bb4ce40886616cfc4f68a92a4da96fbda3e50a71fc75b2e2349c5b95390a7`. Deux portes
1885/0/3 rapportées par Codex, non rejouées par ChatGPT; aucune CI GitHub. V1 acceptée par le propriétaire après
017; 0.9.5 est une préversion, pas 1.0. GO 017/018/019 consommés.
