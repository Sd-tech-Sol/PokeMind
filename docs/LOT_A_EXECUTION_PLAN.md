# LOT A — plan d'exécution autonome

Date du plan : 2026-10-12 (America/Toronto)  
Branche exclusive : `work/pm-v1-lota-knowledge-completeness`

## Prévol mesuré

- Arbre Git propre après `fetch`, `switch` et `pull --ff-only`.
- Base privée consultée en lecture seule : intégrité `ok`, schéma 7, 223 sets,
  602 impressions, 973 traductions, 13 sources de règles, 6 assertions, un
  tournoi et 16 appariements. Ces nombres peuvent évoluer et ne seront pas
  copiés comme données personnelles dans les fixtures.
- Baseline : `216 passed` en 36,66 s.
- `cards coverage` refuse le schéma 7 tant que la migration sauvegardée vers le
  schéma courant n'est pas explicitement déclenchée. Le LOT A doit rendre ce
  besoin visible sans migrer silencieusement une consultation hors ligne.

## A1 — découverte TCGdex mesurable et reprenable

1. Conserver les phases/index/refresh/404 et budgets existants, puis exposer les
   dénominateurs réellement connus, l'état par scope, les erreurs/quota et les
   estimations de requêtes restantes sur les objets déjà découverts.
2. Prioriser localement : impressions du deck explicitement nommé, impressions
   au contexte Standard démontré dans le cache, puis arrière-catalogue; ne
   transmettre que des identifiants TCGdex publics.
3. Renforcer pagination, reprise, données partielles, diagnostics et tests sans
   réseau. Un total fournisseur inconnu reste `unknown`.

Acceptation : progression déterministe avec petit budget, 404 conservé, ordre de
priorité testé, ratios dotés d'un numérateur et d'un dénominateur vérifiables,
aucune image ou donnée privée persistée/versionnée.

## A2 — impressions, alias, variantes et réimpressions

1. Enrichir `cards show/search` avec les deux traductions d'une même impression,
   champs manquants explicites, édition/date, variantes et provenance par langue.
2. Produire un diagnostic de réimpressions uniquement à partir d'assertions
   officielles vérifiées et actives; un nom identique ne crée aucune identité.
3. Normaliser Unicode sans perdre les accents et rendre la résolution de deck
   déterministe face aux collisions, promos et informations partielles.

Acceptation : tests FR/EN, accents, collisions, variantes, 404, identité commune
par ID stable et réimpression non prouvée retournée `unknown`.

## A3 — règles officielles et structure datée

1. Vérifier les sources officielles accessibles et versionner seulement de courts
   faits/provenances. Les documents non consultés restent `non_verified`.
2. Ajouter un registre daté de règles de construction lié à une source officielle,
   avec conflits et anciennes fenêtres conservés.
3. Évaluer 60 cartes, limite par nom, Énergies de base, Pokémon de base et
   exceptions. `legal` exige toutes les preuves; `not_legal` exige une violation
   démontrée; autrement `unknown`.
4. Garder format, plateforme Live/présentiel, disponibilité numérique, possession
   et légalité comme dimensions séparées et ne modifier aucun deck/combat.

Acceptation : tests 59/61, quota, énergie de base, absence de Pokémon de base,
exception incomplète, conflit, dates et source non vérifiée; migration avec backup
et rollback sur bases synthétiques.

## A4 — couverture Limitless contextualisée

1. Préserver l'allowlist, les scopes, checkpoints, HMAC et le refus de
   `/games/{id}/decks`.
2. Ajouter `meta coverage` : contexte, période, fraîcheur, tournois/snapshots,
   placements classifiés, matchs exploitables, phases BO1/BO3/BO5 et exclusions.
3. Ne publier aucun taux avec `n=0` ou sous le seuil et documenter le biais de la
   seule Tournament Platform. Trainer Hill reste bloqué sans accès public autorisé
   vérifié.

Acceptation : tests de filtres date/format/plateforme/online, snapshot partiel,
archétype absent, faible échantillon, provenance et fraîcheur.

## A5 — audit intégré et navigation Codex

1. Ajouter `knowledge status --json` et `knowledge audit --json`, strictement hors
   ligne/lecture seule, qui agrègent cartes, règles et méta sans masquer une table
   absente ou un ancien schéma.
2. Donner des actions prioritaires avec coûts seulement calculables depuis les
   compteurs locaux; tout coût global inconnu reste `unknown`.
3. Tester les parcours carte/effet/réimpression/légalité/méta/source et mettre à
   jour les guides portables.
4. Publier la matrice `DONE`, `PARTIAL_WITH_EVIDENCE`, `BLOCKED_WITH_REASON`, puis
   RESULT, HANDOFF et NEXT_ACTION avec les commandes réellement exécutées.

Acceptation finale : suite complète, `compileall`, `diff --check`, intégrité et
FTS5, consultations CLI offline, audit de confidentialité Git, tests de migration
et aucune régression V1. Le LOT A s'arrête ensuite pour l'audit indépendant.

## Découpage de commits prévu

1. `docs/lot-a-plan` — présent plan et critères.
2. `feat/cards` — A1/A2 et tests.
3. `feat/rules` — A3, registre/migration et tests.
4. `feat/meta` — A4 et tests.
5. `feat/knowledge` — A5, CLI, guides et tests.
6. `test/docs` — audit final, matrice et orchestration.

Les commits peuvent être subdivisés si un changement récupérable le justifie. Ils
restent tous sur la branche du LOT A; aucun merge ni changement de branche par
défaut n'est autorisé.
