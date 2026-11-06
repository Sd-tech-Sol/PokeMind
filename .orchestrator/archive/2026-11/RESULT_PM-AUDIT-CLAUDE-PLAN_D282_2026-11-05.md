# RESULT — PM-AUDIT-CLAUDE-PLAN : PokeMind 0.9.2 publié (D-282), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Ordre du propriétaire : « go » à la proposition d'une 0.9.2 publique (puis
« go » répété pendant la vérification). Session précédente (D-281) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D281_2026-11-05.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D281_2026-11-05.md).

## Publié
- Dépôt public `Sd-tech-Sol/PokeMind`, `main` : commit **`afdb0a3` « PokeMind 0.9.2 »**, parent `a6446e1` (0.9.1),
  arbre `ca38705` identique au commit privé **`b329028`**. Même identité d'auteur que 0.9.0 et 0.9.1. Push de
  `main` seulement, en avance rapide; l'historique privé n'est jamais poussé.
- Préversion **`v0.9.2`** « PokeMind v0.9.2 » : `PokeMind-Setup-0.9.2.exe` (non signé) + `.sha256`.
  SHA-256 `612E037E78C74DCD33F7DA6C7BD21BA645DDCC0F7A4F2A371413C5A3BBD94714`. Notes : `docs/RELEASE_NOTES_0.9.2.md`.
- Contenu depuis 0.9.1 : D-275 à D-281 (recherche web du coach, réinitialisation au choix et jamais bloquée,
  diagnostics, analyse plus rapide, decks et recherche visibles par le coach, saisons TCG Live, archive et
  restauration dans Réglages → Données).

## Checklist (`docs/release-checklist.md`)
- C.0 : dépôt public récupéré d'abord : aucun commit du propriétaire depuis `a6446e1`.
- Version 0.9.2 (`b329028`) : `pyproject.toml`, `pokemind.__version__`, CHANGELOG `[0.9.2] — 2026-11-05`, README
  FR/EN, ROADMAP, SECURITY, notes de version.
- C.1 : `export_public.py` accepté (625 fichiers, arbre identique à HEAD); recherche supplémentaire des détails
  privés de cette session dans l'export : aucun.
- C.2 : porte complète **VERTE dans l'export** : Qt 110, cœur 1589 réussis, 3 ignorés.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `b329028` : Qt 110, cœur 1589 réussis, 3 ignorés.
- EXE recompilé depuis `b329028` : 81 modules `pokemind` identiques aux sources, aucun module QA; recherche de
  chemins personnels dans les binaires (`--require-archive`) passée; fumées mode projet, mode autonome et copie
  installée : sortie 0; installation et désinstallation silencieuses propres.
- Contrôle externe : installateur téléchargé depuis GitHub, empreinte égale au `.sha256`; références publiques :
  `main` et `v0.9.2` = `afdb0a3`, `v0.9.1` = `a6446e1` et `v0.9.0` = `b451e2d` inchangés; `PokeMind` PUBLIC,
  `PokeMind-dev` PRIVATE.
- EXE 0.9.2 déployé dans `dist/PokeMind/` (ancien conservé sous `dist/PokeMind-before-0.9.2-<id>`); installateur
  et `.sha256` copiés dans `dist/installer/` (hors Git).

## Limites
- Installateur non signé (SmartScreen). V1 NOT_RELEASE_READY : 0.9.2 est une préversion.
- Catalogue de cartes : instantané TCGdex épinglé; les cartes de Delta Reign viendront avec une actualisation.
