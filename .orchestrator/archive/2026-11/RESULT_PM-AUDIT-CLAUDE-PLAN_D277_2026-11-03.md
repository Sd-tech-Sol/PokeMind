# RESULT — PM-AUDIT-CLAUDE-PLAN : réinitialisation au choix, par type de données (D-277), 2026-11-03

Exécuteur : Claude Code (Opus 5.5). Demande du propriétaire : dans la réinitialisation, cocher les types de
données à effacer, ou tout. Session précédente (D-276, réinitialisation complète) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D276_2026-11-03.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D276_2026-11-03.md).

## Fait (commit `b53eee3`)
- Nouvelle fenêtre `desktop.reset_dialog.ResetDialog` : « Tout : comme à la toute première ouverture » et une
  case par type, avec une ligne d'explication; rien n'est coché au départ (« Réinitialiser » grisé), la copie
  l'est; « Annuler » est le bouton par défaut. Sans copie, seconde confirmation qui nomme les types choisis.
- `data_reset.CATEGORIES` et `selection()` (chemins sous `data/local`, déplacés à leur place dans la copie) :
  - parties et statistiques : `battle_logs/`, `battle-intelligence/` sauf `my-decks/`;
  - mes decks : `battle-intelligence/my-decks/`, `decks/`, `deck-export.txt`;
  - discussions : `chat/conversation-*.json`, `chat/sandbox/`; si les préférences restent, la liste des
    discussions y est vidée (original copié);
  - connaissances : `web_memory.sqlite3`, `pokemind.sqlite3` (+ fichiers compagnons SQLite), recherches
    publiques gardées dans `public-campaigns/`;
  - catalogue et méta publics : le reste de `public-campaigns/`, `card-images/`;
  - préférences : `chat/preferences.json` (l'assistant de bienvenue revient);
  - fichiers techniques : `logs/`, `update-logs/`, `desktop-dev/`, `demo-runs/`, `test-runs/`,
    `knowledge-update.lock`.
  Tous les types cochés = réinitialisation complète (y compris ce que PokeMind ne connaît pas). Une demande
  sans liste reste lue comme complète; un type inconnu rend la demande invalide.
- Message après redémarrage : « Données retirées : … » ou « PokeMind a été réinitialisé. », puis la copie.
- Guides, PRIVACY et CHANGELOG à jour.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `b53eee3` : Qt 104, cœur 1564 réussis, 3 ignorés.
- Tests : un seul type déplacé, le reste intact; discussions sans préférences (liste vidée); partage du
  dossier public entre connaissances et catalogue; tous les types = complet; types inconnus refusés; fenêtre
  (rien coché, « Tout » coche et décoche tout, bouton grisé sans choix); message nommant les types.
- Captures hors écran : fenêtre entière lisible après correction de la hauteur des textes sur deux lignes.
- EXE recompilé depuis `b53eee3` (79 modules `pokemind` identiques aux sources, aucun module QA; fumées projet, autonome et copie installée : sortie 0) et déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-reset-choices-<id>`); installateur non publié
  `dist/installer/PokeMind-Setup-0.9.1-reinitialisation-au-choix.exe`.

## Limites
- Non exécuté sur les vraies données du propriétaire. Le classement suit les chemins écrits par le code;
  `pokemind.sqlite3` (ancienne base du cerveau) est rangé dans « Connaissances », pas dans « Parties » : le
  compte des parties et les statistiques viennent de `battle_logs/` et des rapports.
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
