# VERIFICATION_PM-0005A-R1 — audit indépendant ChatGPT (2026-10-11)

## Décision
**PM-0005A-R1 ACCEPTÉE EN REVUE STATIQUE INDÉPENDANTE pour sa portée ciblée.** Les deux risques identifiés dans `.orchestrator/VERIFICATION_PM-0005A.md` sont fermés dans le code. Ceci n'est **pas** une certification de légalité complète du deck, ni une réexécution indépendante de pytest ou de la SQLite privée Windows.

## Références GitHub vérifiées
- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0005a-r1-legality-guards`.
- SHA livré par Codex : `18dd95c7c302bd48d193808fd9f55bd2774cb8d5`; parent préparé `6d8ba0d384cf32d86648a75fbadf56d332d1ea8c`. Comparaison : **1 commit d'avance / 0 de retard**, 7 fichiers changés, seulement `src/pokemind/rules.py` et `tests/test_rules.py` comme code/tests du produit.
- Patch et code complet de `src/pokemind/rules.py` inspectés; tests complets `tests/test_rules.py`, `docs/PM-0005A-R1_AUDIT.md`, `.orchestrator/RESULT.md`, `HANDOFF.md`, `NEXT_ACTION.md` consultés.
- Arbre Git complet : **113 entrées**, `truncated=false`, aucun fichier SQLite, sauvegarde, journal personnel, deck réel, photo, secret ou chemin `data/local` privé détecté. Pas de merge. Dépôt par défaut `work/pm-0001`, `main` absente selon vérification antérieure.
- GitHub : **zéro statut CI et zéro workflow PR retourné** pour le HEAD; `99 passed` au prévol, `128 passed` au final, compileall, `git diff --check`, intégrité SQLite et invariants personnels sont **rapportés par Codex**, pas réexécutés par ChatGPT.

## Correctif 1 — garde-fou global de deck
- `check_deck` sélectionne la **version la plus récente** même si `exact_confirmed` est faux, expose `deck_version_id`, `deck_version`, `exact_confirmed`, total enregistré, somme des quantités et un diagnostic de structure.
- Le code initialise systématiquement `DECK_STRUCTURE_NOT_VERIFIED` tant que le validateur officiel complet des quotas, exceptions, Énergies de base et présence d'un Pokémon de base n'est pas implémenté.
- Le verdict **ne retourne plus `legal` sur aucun chemin**; si une carte individuelle est `not_legal`, le global vaut `not_legal`; sinon `unknown`. Une ancienne version confirmée n'est pas choisie à la place d'une nouvelle non confirmée. Aucun write dans `check_deck`.
- Tests synthétiques avec cartes individuellement `legal` mais version non confirmée, 59 cartes, total/quantités incohérents, 60 copies d'une seule carte, zéro Pokémon de base, entrée inconnue, carte interdite; lecture du deck sans changement.

## Correctif 2 — preuve des sources normatives
- `load_official_registry` bâtit `source_statuses` en mémoire et **rejette avant connexion SQLite** une assertion `verified` dont la source est `navigation_only`, `non_verified` ou `conflict`. Le registre normal 2026 (13 sources/6 assertions) reste admissible.
- `check_card` utilise les statuts nommés **de l'assertion et de la source**, contrôle leurs fenêtres d'effet séparément, et retourne `unknown` avec code adéquat pour source conflictuelle/non vérifiée ou assertion non vérifiée pertinente.
- Les restrictions, rotations, couvertures et réimpressions utilisées ensuite pour `legal/not_legal` exigent les deux statuts `verified` et les deux intervalles actifs. Une assertion visant une autre carte ne doit pas contaminer le verdict.
- Tests paramétrés **3 états de sources × 4 types d'assertions** à l'import et pour anciennes lignes DB incohérentes, contrôle atomique, source expirée avant l'assertion, cas non liés et assertions non vérifiées. Ce sont des données synthétiques.

## Limites conservées et suite
- **Aucun deck complet ne peut encore être déclaré `legal`**, car le validateur officiel de construction n'existe pas; `unknown` est un blocage de certitude volontaire. Les verdicts individuels restent utilisables.
- Les sources et données TCGdex sont partielles; les cartes et impressions non résolues, la compatibilité Live réelle, la possession/crédits et les mises à jour automatiques ne sont pas validés.
- Les deux journaux historiques sans original demeurent hors réanalyse exhaustive.
- CI recommandable à terme pour renforcer les preuves, mais **non lancée** par la tranche. Une source `verified` reste une **assertion de qualité documentaire**, non une vérification cryptographique de contenu.
- **PM-0005A-R1 clôturable après revue statique.** Prochaine tranche proposée **PM-0005B — métagame Limitless sourcé** ou travail prioritaire sur couverture TCGdex, uniquement après nouveau feu vert utilisateur et nouveau `NEXT_PROMPT.md`. Aucun merge, planificateur Windows, moteur de deck ou nouveau code autorisé par cet audit.
