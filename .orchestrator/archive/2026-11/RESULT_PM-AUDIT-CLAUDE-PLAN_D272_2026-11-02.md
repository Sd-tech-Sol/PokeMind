# RESULT — PM-AUDIT-CLAUDE-PLAN : PokeMind 0.9.0 publié (D-272), 2026-11-02

Exécuteur : Claude Code (Opus 5.5). Ordre du propriétaire : « GO publie ». Session précédente (D-270, D-271) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D270-D271_2026-11-02.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D270-D271_2026-11-02.md).

## Publié
- Dépôt public **`Sd-tech-Sol/PokeMind`** (branche `main`, 1 commit « PokeMind 0.9.0 », 600 fichiers), arbre identique
  au commit privé **`3d4af78`** (arbre `a83fb3e`). Auteur : l'identité des autres dépôts publics du propriétaire.
- Préversion **`v0.9.0`** « PokeMind v0.9.0 » : `PokeMind-Setup-0.9.0.exe` (non signé) + `PokeMind-Setup-0.9.0.exe.sha256`
  (même format que ClipPull). SHA-256 `922F2D9607E9D127F8667CAEA21103A49FD0F60B4060F7B590BF68904DBB65DC`.
- Réglages comme FileTopo : issues ouvertes, wiki fermé, signalement privé des vulnérabilités activé, licence MIT
  reconnue, 8 sujets, description. Pas de GitHub Actions, profil inchangé (D-271).

## Commits privés de la publication
- `0b6f6b1` : README / README.fr / CHANGELOG au présent (0.9.0, première préversion publique).
- `3d4af78` : l'adresse webmail inventée de `tests/test_export_public.py` est découpée (l'export la refusait).

## Preuves
- Porte locale **VERTE dans l'export** (même arbre que `3d4af78`) : Qt 95, cœur 1545 réussis, 3 ignorés.
- EXE recompilé depuis `0b6f6b1` (`src/` identique à `3d4af78`) : 75 modules `pokemind` identiques aux sources, aucun
  module QA, point d'entrée exact; fumées mode projet, mode autonome et copie installée : sortie 0; 5 bases inventées
  inchangées; dossier de données du propriétaire non modifié (horodatage seulement). Installation silencieuse
  (clé et raccourci créés), désinstallation propre (clé, raccourci et programme retirés).
- Installateur : vérification des chemins de la machine de construction passée (archive Python incluse).
- Contrôle externe : préversion téléchargée depuis GitHub, empreinte égale au `.sha256`; dépôt `PUBLIC`, auteur du
  commit conforme; `Sd-tech-Sol/PokeMind-dev` toujours `PRIVATE`.
- EXE déployé dans `dist/PokeMind/` (ancien conservé sous `dist/PokeMind-before-public-0.9.0-<id>`); installateur
  copié dans `dist/installer/` (le précédent renommé `-avant-public.exe`, hors Git).

## Limites
- Installateur non signé (avertissement SmartScreen documenté). V1 NOT_RELEASE_READY : 0.9.0 est une préversion.
- Le fichier `.sha256` finit par CRLF, comme celui de ClipPull : `sha256sum -c` de Git Bash ne le lit pas tel quel.
