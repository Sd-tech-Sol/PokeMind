# Matrice d’acceptation — LOT D

Date : 2026-10-13. Cette matrice décrit l’exécution Codex; elle ne constitue pas une
vérification indépendante et n’emploie pas le statut `VERIFIED`.

## Résumé

| Chantier | État | Preuve principale |
|---|---|---|
| D0 — garde-fous coach | `DONE` | `visual_coach.py`, `test_visual_coach.py` |
| D1 — orchestrateur public | `DONE` pour le mécanisme; données réelles `PARTIAL_WITH_EVIDENCE` | `updates.py`, `test_updates.py` |
| D2 — quotidien léger | `DONE` | CLI dry-run/apply/status, budgets et historique |
| D3 — mardi/vendredi Toronto | `DONE` pour la logique; exécution planifiée `BLOCKED_WITH_REASON` | `toronto_tz.py`, tests DST/rattrapage |
| D4 — résilience/alertes/offline | `DONE` pour le mécanisme | schéma 12, verrou, logs, rollback synthétique |
| D5 — CLI/skills/scheduler | `DONE` pour la préparation; installation `BLOCKED_WITH_REASON` | `scheduler.py`, skills, guide, tests |

## D0 — dette du LOT C

| Exigence | État | Preuve / limite |
|---|---|---|
| Provenance manuelle non falsifiable | `DONE` | `visual_certain` devient `owner_annotated`, `ocr_uncertain` devient `unknown`; un futur backend devra attester par une voie interne. |
| Informations cachées | `DONE` | Main ou défausse `hidden/unknown` ne conserve aucune carte; contenu des Récompenses et ordre de pioche restent `UNKNOWN`. |
| Coût typé | `DONE` | Allocation par type puis Colorless; Feu + seule Énergie Eau donne `ENERGY_TYPE_NOT_VERIFIED`; Énergie spéciale/type inconnu reste non supporté. |
| Tour/phase/source/contexte | `DONE` | Tour adverse, mauvaise phase, source absente/future et format/plateforme/date incohérents s’abstiennent sans citation trompeuse. |
| A→B→A, révocation et concurrence | `DONE` | Schéma 12 retire seulement l’unicité historique du hash; l’index d’une seule active demeure. Révisions identiques, doublon actif, révocation et `BEGIN IMMEDIATE` testés. |

## D1–D4 — actualisation publique

| Exigence | État | Preuve / limite |
|---|---|---|
| Composition TCGdex/Pokémon/Limitless | `DONE` | Réutilise `sync_cards` et `sync_meta`; client officiel GET allowlisté; aucun LLM/compte. |
| Budget réel redirects/retries | `DONE` | Trois clients débitent avant GET; tests de retry/allowlist/oversize et suites historiques TCGdex/Limitless. |
| Validation normative prudente | `DONE` | HTTP 200/304 ou hash différent reste `non_verified/conflict`; aucune écriture dans les assertions officielles. |
| Delta/provenance/santé | `DONE` | Tables de cycles, sources, observations et alertes; compteurs `new/changed/missing/unknown`, URL/date/statut. |
| Catalogue/règles/méta réels complets | `PARTIAL_WITH_EVIDENCE` | Mécanisme démontré sur transports synthétiques; aucune grosse sync réelle ni prétention d’exhaustivité dans LOT D. Les caches A restent partiels. |
| Quotidien dry-run zéro effet | `DONE` | Test base absente : zéro DB, verrou, log, réseau et migration. Probe réseau séparé et sans écriture. |
| Application publique confirmée | `DONE` | `--apply --confirm-owner`; seules données publiques sont routées aux collecteurs. |
| Historique et `last_successful` | `DONE` | Échec synthétique n’avance pas la dernière réussite; cycles partiels explicites. |
| DST/cadence/rattrapage | `DONE` | EST `-05:00`, EDT `-04:00`, mardi/vendredi, heure obligatoire, jour déjà fait, rattrapage récent unique, jours fériés documentés. |
| Processus concurrents | `DONE` | Création exclusive du verrou, refus d’un deuxième processus, reprise contrôlée d’un verrou stale. |
| Atomicité/checkpoints/rollback | `DONE` | Pas de transaction updater pendant GET; commits source courts, checkpoints fournisseurs, sauvegarde 11→12 restaurable. |
| Offline/alertes/logs | `DONE` | Status lecture seule, source en panne non verte, alerte après trois échecs, JSONL sans chemin absolu ni identifiant de source. |
| Trainer Hill | `BLOCKED_WITH_REASON` | Toujours aucune API publique/condition automatisable vérifiée; aucun scraping. |

## D5 — planification simulée

| Exigence | État | Preuve / limite |
|---|---|---|
| Lanceur sans Codex/LLM | `DONE` | `scripts/pokemind_update.ps1` appelle seulement `python -m pokemind knowledge update`. |
| Manifests standard user | `DONE` | `LeastPrivilege`, working directory, `StartWhenAvailable`, `IgnoreNew`, sortie locale et verrou updater. |
| Heure configurable | `DONE` | Daily/deep exigent `HH:MM`; aucune valeur arbitraire par défaut. |
| Install/status/uninstall simulés | `DONE` | Sorties dry-run et commandes futures rendues sans lancer PowerShell/schtasks. |
| Installation/activation réelle | `BLOCKED_WITH_REASON` | Verrou dur `SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D`; consentement distinct futur requis. |
| Skills portables | `DONE` | `.agents` et `.claude` byte-identiques, commandes update/status/scheduler prudentes. |

## Preuves d’exécution

- Baseline : **272 tests**. Suite finale : **288 tests réussis en 62,99 s**.
- `python -m compileall -q src tests` et `git diff --check` réussis.
- E2E synthétique : TCGdex + source Pokémon + Limitless, deux cycles, changement
  officiel en `conflict`, aucun changement du registre normatif, logs anonymisés.
- Migration synthétique 11→12 : sauvegarde au schéma 11 restaurable, contraintes
  d’historique corrigées et tables publiques présentes.
- Base privée : diagnostics/dry-runs seulement; schéma 7 et empreinte comparés au
  prévol dans l’audit final. Aucune migration ou collecte réelle sur cette base.
- Scheduler : aucun appel OS dans le code de prévisualisation/test; aucune tâche,
  aucun service et aucun autorun créé ou modifié.

## Reste explicite

LOT E demeure obligatoire pour sauvegarde/restauration complète, rétention et QA
finale. Les couvertures publiques A/B, vision locale réelle C2/C4/C5, vrai smoke test
d’entraînement et Trainer Hill restent partiels/bloqués avec leurs raisons.
