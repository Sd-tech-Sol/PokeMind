# RESULT — PM-AUDIT-CLAUDE-PLAN : PokeMind 0.9.1 publié (D-274), 2026-11-03

Exécuteur : Claude Code (Opus 5.5). Ordre du propriétaire : « go » à la proposition d'une 0.9.1 publique qui corrige
la règle ACE SPEC absente de 0.9.0. Session précédente (D-273) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D273_2026-11-02.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D273_2026-11-02.md).

## Publié
- Dépôt public `Sd-tech-Sol/PokeMind`, `main` : commit **`a6446e1` « PokeMind 0.9.1 »**, arbre identique au commit
  privé **`bc90012`** (arbre `2b4da8e`), parent `8415c14`. Même identité d'auteur que 0.9.0.
- Préversion **`v0.9.1`** « PokeMind v0.9.1 » : `PokeMind-Setup-0.9.1.exe` (non signé) + `.sha256`.
  SHA-256 `C3FD796CD19D1BC61F5AA2158C3C50C5A577125EA3B54F3941042DC74471DE4C`. Notes : `docs/RELEASE_NOTES_0.9.1.md`.
- Contenu : correctifs D-273 (règle 1 ACE SPEC / 1 Radieux, enregistrement de deck par le coach, bandeau de
  chargement, « Tout supprimer », rendu du chat).

## Modifications du propriétaire sur GitHub
- Le dépôt public avait deux commits faits par le propriétaire dans l'interface GitHub après 0.9.0 (`ccf2909`,
  `8415c14`) : intro des README réduite à « coach IA ». Reportés dans le dépôt privé (`bc90012`, article corrigé
  en anglais : « an AI coach ») avant l'export, pour ne pas les écraser; le commit 0.9.1 vient après eux.

## Commits privés
- `4e6a595` : version 0.9.1 (`pyproject.toml`, `pokemind.__version__`), CHANGELOG, README, ROADMAP, SECURITY, notes.
- `bc90012` : intro des README reprise du dépôt public.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `4e6a595` puis **dans l'export** (arbre de `bc90012`) :
  Qt 99, cœur 1546 réussis, 3 ignorés.
- EXE recompilé depuis `4e6a595` (`bc90012` ne change que les README) : 75 modules `pokemind` identiques aux sources,
  aucun module QA; fumées mode projet, mode autonome et copie installée : sortie 0; installation et désinstallation
  silencieuses propres.
- Contrôle externe : installateur téléchargé depuis GitHub, empreinte égale au `.sha256`; références publiques :
  `main` et `v0.9.1` = `a6446e1`, `v0.9.0` inchangé; `PokeMind` PUBLIC, `PokeMind-dev` PRIVATE.
- EXE déployé dans `dist/PokeMind/` (ancien conservé sous `dist/PokeMind-before-0.9.1-<id>`); installateur copié
  dans `dist/installer/` (hors Git).

## Limites
- Installateur non signé (SmartScreen). V1 NOT_RELEASE_READY : 0.9.1 est une préversion.
- Vitesse au démarrage (M-4) toujours en attente du diagnostic masqué du propriétaire.
