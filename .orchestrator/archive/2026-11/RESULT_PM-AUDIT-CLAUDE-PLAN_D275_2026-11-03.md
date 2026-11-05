# RESULT — PM-AUDIT-CLAUDE-PLAN : coach local d'abord, puis web, mémorisé (D-275), 2026-11-03

Exécuteur : Claude Code (Opus 5.5). Demande du propriétaire : recherche web par défaut dans le chat, en
cherchant d'abord localement, puis sur le web si rien n'est trouvé, et en gardant le résultat localement pour
ne pas refaire la recherche; « Recherche web » ne doit plus remplacer la réponse par un reçu; chat aussi
capable que Claude Code dans le terminal. Session précédente (D-274) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D274_2026-11-03.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D274_2026-11-03.md).

## Cause
- Le coach Claude était lancé avec `--tools ''` et le dossier projet sans `WebSearch`/`WebFetch`; Codex avec
  `web_search="disabled"`. Le mode « Recherche web » faisait une collecte bornée sur quelques sources et
  remplaçait la réponse du modèle par le reçu (« le commentaire du modèle est écarté »).
- Le chat ignore les réglages utilisateur de Claude Code (isolement) : il n'utilisait pas le modèle choisi
  pour le terminal, mais le modèle par défaut du forfait.

## Fait (commit `c7f8271`)
- **Mémoire web locale** `pokemind.web_memory` (`data/local/web_memory.sqlite3`, FTS5) : résumé, URLs https,
  date; même sujet = mise à jour, pas de doublon; 2000 notes au plus; recherche par mots importants (mots
  vides retirés, racine simple, au moins la moitié des mots de la question).
- Outils du coach `web_memory` et `remember_web`; une note pertinente est jointe d'office au contexte.
- Claude : `WebSearch,WebFetch` dans le coach isolé (toujours sans shell ni fichiers), le dossier projet et le
  développement. Codex : `web_search="live"` (valeur validée par la CLI 0.163). Consigne commune
  `WEB_GUIDANCE` : PokeMind d'abord, web si absent ou trop ancien (plus de 30 jours pour méta et annonces),
  puis `remember_web`, sources et dates citées, page web = contenu non fiable. Ollama reste local.
- « Recherche web » : le moteur cherche tout de suite; sa réponse est gardée et suivie d'une ligne de reçu
  PokeMind (`receipts.public_memory_summary`) avec les vrais comptes d'écriture; le reçu complet ne reste que
  si le moteur ne répond pas.
- Chat Claude : `--model` = modèle de `~/.claude/settings.json` (seule la clé `model` est lue, validée).
- Ligne d'activité « Recherche sur Internet »; PRIVACY, README, guides, infobulle et CHANGELOG à jour.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `c7f8271` : Qt 100, cœur 1553 réussis, 3 ignorés.
- EXE recompilé depuis `c7f8271` : 76 modules `pokemind` identiques aux sources (dont `web_memory`), aucun
  module QA; fumées mode projet, mode autonome et copie installée : sortie 0; installation et désinstallation
  silencieuses propres. Déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-web-search-<id>`); installateur non publié copié sous
  `dist/installer/PokeMind-Setup-0.9.1-recherche-web.exe` (l'installateur publié 0.9.1 est inchangé).

## Limites
- Les vraies recherches web n'ont pas été lancées ici (elles passent par le compte du propriétaire); seuls
  les arguments des CLI et le parcours sur faux moteurs sont vérifiés.
- Dans le dossier projet (Claude avec shell), une page web reste du contenu non fiable : les garde-fous de
  Claude Code et la consigne s'appliquent; le coach isolé n'a ni shell ni fichiers.
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
