# Plan d’exécution — LOT D

Date d’exécution : 2026-10-13. Branche exclusive :
`work/pm-v1-lotd-public-knowledge-updates`.

Le lot actualise uniquement des connaissances publiques. Les tests utilisent des
bases, horloges et transports synthétiques sous `data/local/test-runs`. Aucune base
personnelle n’est migrée par une consultation, aucun deck/journal/crédit/capture ne
quitte la machine et aucune tâche Windows n’est installée ou activée.

## Prévol mesuré

- Branche synchronisée par `fetch` puis `pull --ff-only`, arbre initial propre.
- Baseline : `272 passed`; `compileall` et `git diff --check` réussis.
- Base privée lue seulement : schéma 7, intégrité `ok`; empreinte SHA-256 prise
  avant les diagnostics. `status`, `knowledge status` et `knowledge audit` n’ont
  demandé ni réseau ni migration.
- Couverture réelle : catalogue/réimpressions/règles/méta toujours partiels;
  Trainer Hill demeure `BLOCKED_WITH_REASON`. Le lot ne transforme pas ces limites
  en connaissance vérifiée.

## D0 — garde-fous du coach

1. Sanitariser toute provenance issue d’une annotation propriétaire : sans preuve
   produite par un adaptateur local attesté, `visual_certain` et `ocr_uncertain`
   deviennent `owner_annotated` ou `unknown`. Masquer également les cartes d’une
   défausse déclarée cachée/inconnue.
2. Comparer les coûts d’attaque aux types d’Énergie visibles. Colorless accepte une
   ressource connue; un symbole coloré exige le type correspondant. Toute Énergie
   spéciale, type inconnu ou modificateur non prouvé garde l’option inconnue.
3. Refuser/conserver comme conflit un conseil dont format, plateforme ou date ne
   correspondent pas à la séance; attaque seulement au tour du joueur et dans la
   phase permise.
4. Rendre A→B→A révisable sans effacer l’historique : une seule observation active
   par tour, transition atomique, doublon actif idempotent, ancien état restaurable,
   révocation et fermeture concurrentes sûres.

## D1 — orchestrateur public incrémental

1. Ajouter un module Python déterministe qui compose les collecteurs TCGdex et
   Limitless existants et un contrôle prudent du registre Pokémon officiel.
2. Enregistrer cycles, unités, budgets, compteurs, provenance, deltas et santé dans
   un schéma SQLite additif. Les règles officielles détectées restent candidates
   `non_verified/conflict` jusqu’à validation humaine du contenu daté; HTTP 200 ne
   certifie jamais une règle.
3. Garder les transactions réseau séparées des commits d’état du cycle, les
   checkpoints publics reprenables et les anciennes données valides intactes.

## D2 — contrôle quotidien léger

1. Exposer `knowledge update --mode daily --dry-run --json`, l’application publique
   confirmée et `knowledge update status --json`.
2. Le dry-run planifie seulement : zéro réseau, fichier, SQLite ou migration. Un
   éventuel probe réseau est une option distincte, bornée et sans écriture.
3. Budgets stricts par source et global; états `planned/attempted/completed/partial/
   blocked`; `last_successful` ne bouge pas lors d’un échec.

## D3 — réconciliation mardi/vendredi

1. Calculer l’échéance avec `zoneinfo.ZoneInfo("America/Toronto")`, horaire local
   configurable, DST été/hiver, absence machine et rattrapage sans doublon.
2. Le mode approfondi progresse par budgets : index TCGdex, détails FR/EN, règles
   officielles candidates et découverte/refresh Limitless. Une partie incomplète ne
   remplace jamais un état complet.
3. Tester mardi/vendredi, même jour traité, rattrapage, quota, panne, horloge future
   et contamination temporelle.

## D4 — résilience, rapports et confidentialité

1. Verrou interprocessus local borné, cycles idempotents et reprise après abandon;
   rollback SQLite synthétique et conservation des tables/FTS5 existantes.
2. Produire rapports `new/changed/missing/unknown`, alertes locales seulement et
   logs JSONL anonymisés sous `data/local/`, sans chemin absolu ni valeur privée.
3. Le mode offline et le statut restent lisibles; les erreurs ne créent aucun vert
   artificiel. Contrôler intégrité/FK/FTS5, empreinte de la base privée et secrets Git.

## D5 — préparation Windows sans installation

1. Générer un manifeste et des commandes PowerShell sûres pour tâche standard,
   répertoire de travail explicite, fuseau/DST, verrou, rattrapage et sortie locale.
2. Toute installation réelle refuse sans `--confirm-owner` et reste en plus
   désactivée dans le LOT D; les tests ne font que rendre/valider des commandes avec
   mocks. Ne jamais appeler `schtasks /Create` ni `Register-ScheduledTask`.
3. Documenter statut, activation future distincte et désinstallation; fournir skill
   portable Codex/Claude et E2E D1–D5 synthétique.

## Checkpoints prévus

1. Plan et D0 avec tests de régression.
2. Schéma 12, orchestrateur D1/D2 et tests transports/quotas.
3. Cadence D3, résilience D4, rapports et tests.
4. CLI/skills/scheduler dry-run D5 et E2E.
5. Audit interne, guide, matrice, `RESULT`, `HANDOFF`, `NEXT_ACTION`, tests finaux,
   plusieurs commits puis push exclusif de la branche.

Chaque exigence finale portera `DONE`, `PARTIAL_WITH_EVIDENCE` ou
`BLOCKED_WITH_REASON`. Le lot s’arrête ensuite pour l’audit indépendant ChatGPT et
ne revendique jamais `VERIFIED`.
