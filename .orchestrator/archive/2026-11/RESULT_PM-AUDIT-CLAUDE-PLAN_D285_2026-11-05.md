# RESULT — PokeMind 0.9.3 publié (D-285), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Ordre du propriétaire : « go », en réponse à « publier 0.9.3 demande
toujours ton GO ». Publication **avant** l'audit ChatGPT du mandat BrainBall : l'audit se fait a posteriori
(D-258), il reste à faire. Rapport précédent (D-284, couleurs BrainBall) :
[archive/2026-11/RESULT_PM-UI-BRAINBALL-THEMES-001_D284_2026-11-05.md](archive/2026-11/RESULT_PM-UI-BRAINBALL-THEMES-001_D284_2026-11-05.md).

## Publié
- Dépôt public `Sd-tech-Sol/PokeMind`, `main` : commit **`5629ae2` « PokeMind 0.9.3 »**, parent `afdb0a3` (0.9.2),
  arbre `bb5beca` identique au commit privé **`84426b8`**. Même identité d'auteur que les versions précédentes.
  Push de `main` seulement, en avance rapide; l'historique privé n'est jamais poussé.
- Préversion **`v0.9.3`** « PokeMind v0.9.3 » : `PokeMind-Setup-0.9.3.exe` (non signé) + `.sha256`.
  SHA-256 `AD8D4EFD678B9DAEB41C5F97BA870A496F373B3FBAD954EBC903B3E8DD5DC85A`. Notes : `docs/RELEASE_NOTES_0.9.3.md`.
- Contenu depuis 0.9.2 : mises à jour en un clic des cartes et du programme (D-283) et couleurs BrainBall
  (D-284).

## Checklist (`docs/release-checklist.md`)
- C.0 : dépôt public récupéré d'abord : aucun commit du propriétaire depuis `afdb0a3`.
- Version 0.9.3 (`84426b8`) : README FR/EN (état et limites : le catalogue suit maintenant TCGdex et se met à
  jour depuis l'application), SECURITY, ROADMAP, CHANGELOG `[0.9.3] — 2026-11-05`. `pyproject.toml`,
  `__version__` et notes de version étaient déjà à 0.9.3 (D-283, D-284).
- C.1 : `export_public.py` accepté (643 fichiers, arbre identique à HEAD); recherche supplémentaire des détails
  privés de cette session dans l'export : aucun.
- C.2 : porte complète **VERTE dans l'export** : Qt 114, cœur 1610 réussis, 3 ignorés.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `84426b8` : Qt 114, cœur 1610 réussis, 3 ignorés.
- EXE recompilé depuis `84426b8` : 83 modules `pokemind` identiques aux sources, aucun module QA; recherche de
  chemins personnels dans les binaires (`--require-archive`, plus une recherche du nom de compte dans les 799
  fichiers) passée; fumées en mode projet, en mode autonome et en copie installée : sortie 0; installation et
  désinstallation silencieuses propres; base synthétique inchangée.
- Contrôle externe : installateur téléchargé depuis GitHub, empreinte égale au `.sha256`; préversion
  (non brouillon) avec ses deux fichiers; références publiques : `main` et `v0.9.3` = `5629ae2`, `v0.9.2` = `afdb0a3`,
  `v0.9.1` = `a6446e1` et `v0.9.0` = `b451e2d` inchangés; `PokeMind` PUBLIC, `PokeMind-dev` PRIVATE.
- Module de mise à jour de l'application, interrogé contre GitHub (lecture seule) : depuis 0.9.2, il annonce
  0.9.3 avec l'installateur de 38 687 285 octets (la taille publiée); depuis 0.9.3, il répond « à jour ».
- EXE 0.9.3 déployé dans `dist/PokeMind/` (ancien conservé sous `dist/PokeMind-before-0.9.3-public-<id>`);
  installateur et `.sha256` copiés dans `dist/installer/` (le précédent gardé sous `-brainball`), hors Git.

## Ce que ça change pour les utilisateurs
- 0.9.0 à 0.9.2 n'ont pas le bouton : on installe 0.9.3 une fois à la main (elle met à jour en place et garde
  les données). Ensuite, les versions suivantes s'installent depuis l'application.
- Une copie 0.9.3 installée verra la prochaine version publiée dans son bandeau « Mise à jour disponible ».

## Limites
- Installateur non signé (SmartScreen). V1 NOT_RELEASE_READY : 0.9.3 est une préversion.
- Le mandat BrainBall (D-284) est IMPLEMENTED/REPORTED, **pas VERIFIED** : l'audit ChatGPT reste à faire,
  après publication. Une correction éventuelle passerait par une 0.9.4, sur GO.
- Delta Reign arrivera par « Mettre à jour » dès que TCGdex publiera ses cartes.
