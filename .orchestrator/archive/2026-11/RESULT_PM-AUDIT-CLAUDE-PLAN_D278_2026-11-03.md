# RESULT — PM-AUDIT-CLAUDE-PLAN : diagnostic du propriétaire, plantage d'import et analyse plus rapide (D-278), 2026-11-03

Exécuteur : Claude Code (Opus 5.5). Le propriétaire a collé le texte de « Copier le diagnostic » (masqué;
non versionné). Session précédente (D-277, réinitialisation au choix) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D277_2026-11-03.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D277_2026-11-03.md).

## Constats tirés du diagnostic
1. `IndexError` dans `MainWindow.ingest_done` (`self.conversation['messages'][-1]`) : pendant un import
   (environ 80 s), « Supprimer » et « Tout supprimer » restaient actifs; supprimer la discussion la remplaçait
   par une discussion vide et la fin de l'import plantait.
2. Chaque analyse de combats prenait environ 83 s, dont environ 65 s pour les 5 « plans contre-deck », et
   repartait à chaque journal importé. Profil sur fixture inventée : `competitive._advisor_snapshot` (relecture
   et analyse de toutes les pages de listes publiques) appelé 14 fois par plan; fiches `knowledge_show`,
   présélection et comparaisons recalculées pour chaque plan alors qu'elles ne dépendent pas de la cible.
3. Le diagnostic copié s'arrêtait deux jours avant : `diagnostics.redact` tronque à 8 000 caractères et
   coupait la **fin** du rapport (les lignes les plus récentes).

## Fait (commit `c4338f5`)
- Boutons de suppression bloqués pendant un import ou un tour (`chat_controls`, gardes); `ingest_note` ajoute
  le texte au message d'import, ou crée un message si la discussion ne finit plus par lui.
- `competitive._advisor_snapshot` mémorisé (copie privée à chaque appel) tant que la base, le registre
  `requests.json` et chaque page nommée par le registre gardent taille et date; 15 min au plus; aucun dossier
  listé. Une page modifiée est toujours détectée.
- `counter_deck.counter_plan(shared=…)` : inventaire, présélection, fiches et comparaisons partagés entre les
  plans d'une même analyse (mêmes entrées seulement), résultat identique; `battle_batch` passe ce partage.
- Diagnostic : « Erreurs récentes » d'abord (avec la ligne d'exception), puis la fin du journal en gardant les
  lignes les plus récentes, 12 000 caractères au plus.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `c4338f5` : Qt 105, cœur 1568 réussis, 3 ignorés.
- Profil sur fixture inventée : 3 plans contre-deck 2,99 s → 0,67 s; lectures complètes de l'échantillon
  public 42 → 1. Le gain réel sur le PC du propriétaire n'est pas mesuré ici (à lire dans le prochain
  diagnostic : lignes « Analyse · plan contre-deck »).
- Tests : résultat identique avec et sans partage, fiches construites une seule fois, parties non partagées;
  mémoire de l'échantillon (copie privée, page touchée = relecture, page modifiée = détectée); import qui finit
  après une discussion vidée; résumé d'erreurs et dernières lignes gardées.
- EXE recompilé depuis `c4338f5` (79 modules `pokemind` identiques aux sources, aucun module QA; fumées projet, autonome et copie installée : sortie 0) et déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-faster-analysis-<id>`); installateur non publié
  `dist/installer/PokeMind-Setup-0.9.1-analyse-rapide.exe`.

## Limites
- Les autres étapes de l'analyse (contexte public environ 5 s, lecture des journaux environ 4,5 s, familles
  environ 4,4 s) ne sont pas optimisées; l'analyse complète repart encore à chaque import.
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
