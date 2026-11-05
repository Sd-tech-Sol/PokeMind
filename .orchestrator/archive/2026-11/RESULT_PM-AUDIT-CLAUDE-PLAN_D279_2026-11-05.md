# RESULT — PM-AUDIT-CLAUDE-PLAN : 2e diagnostic du propriétaire, decks et recherche visibles par le coach, analyse réutilisée (D-279), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Le propriétaire a recollé « Copier le diagnostic » après D-278 (masqué;
non versionné). Session précédente (D-278) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D278_2026-11-03.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D278_2026-11-03.md).

## Constats tirés du diagnostic
1. D-278 confirmé sur le PC : analyse d'un import environ 85 s → environ 31 s; les 5 plans contre-deck
   environ 70 s → environ 18 s. Aucune nouvelle erreur (seule l'erreur d'avant le correctif reste listée).
2. `pokemind_tool/decks · CONTEXT_SIZE_CAP` répété : toutes les listes de 60 cartes à la fois dépassaient
   le plafond d'un outil (24 000 octets); le coach ne recevait **aucun** deck.
3. `pokemind_tool/research · CONTEXT_SIZE_CAP` : le reçu complet de la recherche (tous les faits) dépassait
   le même plafond; le coach ne recevait qu'une erreur.
4. Chaque import refait encore le contexte public (environ 5 s) et les 5 plans (environ 18 s), alors
   qu'ils ne dépendent que des fichiers publics et de la date.

## Fait (commit `4cf50ea`)
- `decks` : tous les noms avec leur numéro (`reference`), les listes complètes tant qu'elles tiennent;
  `decks` + `reference` = la liste d'un deck; `query` filtre par nom. Decks personnels toujours exclus d'un
  contexte public. Les numéros restent ceux de `compare`/`save_candidate`.
- `research` : le coach reçoit une vue bornée du reçu (comptes, 12 sources, faits entiers tant qu'ils
  tiennent); l'hôte garde le reçu complet pour son propre compte rendu.
- Filet général dans `run_tool` : une réponse trop longue garde le début de sa plus longue liste
  (`truncated`, journalisé `TRUNCATED`) au lieu d'être perdue; erreur seulement si rien ne tient.
- `counter_deck.public_memo` : les plans (et leur travail partagé) sont gardés d'une analyse à la suivante
  tant que la base compétitive, son registre, les pages qu'il nomme et le catalogue gardent taille et date;
  copie privée à chaque appel; aucun dossier listé; deux états au plus.
- `battle_batch.public_context` mémorisé de la même façon (bases publiques, index de recherche et
  manifestes qu'il nomme, date); chemins revérifiés à chaque réutilisation.

## Preuves
- Porte locale **VERTE sur la suite complète** au contenu de `4cf50ea` : Qt 105, cœur 1573 (3 ignorés).
- Fixture inventée : 5 plans 0,49 s à la première analyse, 0,02 s à la suivante. Gain réel à lire dans le
  prochain diagnostic (lignes « Analyse · contexte public » et « plan contre-deck » d'un 2e import).
- Tests : liste de 40 decks sous le plafond, liste d'un deck par numéro, deck personnel refusé en public,
  filtre par nom; reçu de 40 faits raccourci, reçu complet gardé par l'hôte; filet `truncated`; plans
  réutilisés puis recalculés quand le catalogue change; contexte public réutilisé puis recalculé (nouvel
  index de recherche, catalogue touché, autre date).
- EXE recompilé depuis `4cf50ea` (79 modules `pokemind` identiques aux sources, aucun module QA; fumées
  projet, autonome et copie installée : sortie 0) et déployé dans `dist/PokeMind/` (ancien conservé sous
  `dist/PokeMind-before-reuse-analysis-<id>`); installateur non publié
  `dist/installer/PokeMind-Setup-0.9.1-decks-coach.exe`.

## Limites
- La première analyse d'une session ou d'une nouvelle journée reste complète (environ 30 s, en arrière-plan) :
  l'empreinte inclut la date, par conception.
- La lecture des journaux (environ 5 s) est refaite à chaque import.
- Dépôt public inchangé : une 0.9.2 publique exige un GO.
