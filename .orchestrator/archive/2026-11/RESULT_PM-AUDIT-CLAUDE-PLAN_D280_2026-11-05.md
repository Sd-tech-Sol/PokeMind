# RESULT — PM-AUDIT-CLAUDE-PLAN : réinitialisation réparée, scripts d'archive, saisons TCG Live (D-280), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Demandes du propriétaire : le bouton « Réinitialiser » ne marchait pas; un
Python pour réinitialiser et un pour archiver tout le dossier du compte en zip; remise à zéro pour revivre une
première ouverture; statistiques par saison (la saison venait de recommencer le 5 novembre), avec le cumul.
Session précédente (D-279) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D279_2026-11-05.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D279_2026-11-05.md).

## Réinitialisation : cause trouvée et corrigée (commit `1cdb9cd`)
- Reproduite avec de vrais processus sur des données inventées (fenêtre qui se ferme, lancement suivant) : au
  repos elle marche; pendant une analyse (environ 30 s à chaque import et au premier lancement du jour) ou une
  réponse du coach, le bouton n'affichait qu'une ligne dans la barre d'état et **ne faisait rien**.
- Maintenant : l'opération en cours est arrêtée à son étape sûre, rien de nouveau ne démarre (analyse,
  surveillance des journaux), la fenêtre se ferme puis la réinitialisation s'applique au lancement suivant.
  Reproduction refaite : `RESET`. Attente de la fenêtre qui se ferme 90 s (au lieu de 30), essais 20 s; un
  échec nomme l'élément encore utilisé (`blocked`).

## Scripts d'archive (même commit)
- `pokemind.data_archive` + `scripts/archive_data.py`, `reset_data.py`, `restore_data.py`, PokeMind fermé
  (refus sinon) : zip de tout `%LOCALAPPDATA%\PokeMind` dans `%LOCALAPPDATA%\PokeMind-archives`, écrit sous
  un nom partiel puis relu entier (CRC, mêmes noms et tailles) avant son nom final; remise à zéro qui archive
  d'abord, met tout de côté d'un bloc (retour complet si un fichier est utilisé) et ne garde que le pointeur
  et des dossiers vides (`data/local`, `workspace`, et le `data/local` de chaque dossier nommé par le
  pointeur); restauration qui archive d'abord le contenu actuel, refuse les chemins hors du dossier et les
  liens, et remet la date de chaque fichier. Les fichiers en lecture seule sont effacés aussi.
- **Exécuté sur demande explicite du propriétaire** (« veux-tu me le remettre à zéro ») : archive vérifiée
  puis remise à zéro de son dossier, PokeMind fermé; aucun contenu lu. L'archive reste sur son PC, hors Git.

## Saisons (même commit)
- `pokemind.seasons` : une saison va d'un Ladder classé au suivant. Départ officiel connu : **2026-11-05**,
  Ladder de novembre 2026 avec Méga-Évolution — Delta Reign (lettre officielle du 2026-10-30 :
  https://community.pokemon.com/en-us/discussion/26744/letter-to-the-community-october-30-2026).
  « Nouvelle saison… » en ajoute une aujourd'hui (`battle-intelligence/seasons.json`, effacé avec les parties).
- Un journal n'a pas de date : une partie compte dans la saison du jour où son journal a été ajouté (date du
  fichier, gardée par la copie hors du projet et par la restauration).
- Vue d'une saison = le même rapport limité à ses parties, regroupé par `battle_batch.group_matches` (mêmes
  calculs que l'analyse); « Cumul » = tout. Recommandations et Learning Loop restent calculés sur toutes les
  parties, et c'est écrit. Choix gardé (`season_view`), sur Vue d'ensemble et Combats; le coach reçoit la saison
  affichée et les totaux de chaque saison. Aucune nouvelle analyse, rien de déplacé.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `1cdb9cd` : Qt 108, cœur 1585 passed, 3 skipped.
- Tests : archive vérifiée et jamais écrasée, zip partiel retiré si échec, remise à zéro et retour complet si
  fichier utilisé, refus si PokeMind ouvert, restauration avec dates, chemin hors dossier refusé, lecture seule
  effacée; réinitialisation pendant une analyse; saisons (bornes, saison du propriétaire, vues, cumul intact,
  résumé du coach), choix de saison dans la fenêtre et « Nouvelle saison… ».
- EXE recompilé depuis `1cdb9cd` et déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-seasons-<id>`); installateur non publié `dist/installer/PokeMind-Setup-0.9.1-seasons.exe`.

## Limites
- Une partie ajoutée le 5 novembre avant midi (heure du Québec) compte déjà dans la nouvelle saison : la saison
  se compte au jour.
- Les prochains départs de Ladder officiels s'ajoutent dans `seasons.OFFICIAL` (ou par « Nouvelle saison… »).
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
