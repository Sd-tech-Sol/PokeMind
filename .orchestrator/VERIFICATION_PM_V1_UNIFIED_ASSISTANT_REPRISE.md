# Reprise et revue du cahier unifié — 2026-10-26 (Québec)

## Verdict et portée
**CONFIRMED_GITHUB_BASELINE_AND_DESIGN_SCOPE_ONLY.** Le cahier est cohérent avec la demande actuelle : une conversation persistante, Codex par défaut, outils réels et mémoire Web durable dans le cerveau existant. Implémentation complémentaire **non lancée**, état maintenu **DESIGN_READY_OWNER_REVIEW**, `execute_now=false`, V1 **NOT_RELEASE_READY**. Cette revue ne certifie ni le fonctionnement du PC, ni toutes les portes V1, ni la sécurité complète des anciens lots.

L'ancienne conception `PM-V1-DESKTOP-CODEX-DIRECT-TERMINAL-001` est annulée et non réactivable. Les anciens premiers paragraphes HANDOFF/RESULT/README/guide et l'architecture terminal contredisaient STATE/NEXT_ACTION : leur priorité est corrigée par cette livraison documentaire. Une divergence restante impose STOP, pas le choix arbitraire d'un ancien mandat.

## GitHub et CI vérifiés directement
- Dépôt/branche : `Sd-tech-Sol/PokeMind`, `work/pm-v1-lotj-final-readiness-windows`.
- HEAD examiné : [693750ce63cc81330c171537c0e75b8866b5c31e](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/693750ce63cc81330c171537c0e75b8866b5c31e).
- Comparaison avec `2e28b33fa0b58609a211840fd2046ffa953c1af7` : **3 commits, 11 fichiers documentaires/état, aucun changement src/tests/workflow/dépendances**.
- [Run 40441594259](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40441594259), au HEAD examiné : **completed/failure**. Jobs Windows `121982992546` et Ubuntu `121982992924` refusés avant démarrage. Annotation GitHub de chacun : **“The job was not started because an Actions budget is preventing further use.”** Aucun test de ce run n'a exécuté le code. Cause confirmée via annotations REST avec GitHub CLI, le connecteur ne donnant pas accès à cette sous-ressource. Les logs des jobs sont indisponibles (404); pas d'erreur applicative inférée. Aucun changement de budget/facturation ni relance effectuée.
- [Run 40408811095](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40408811095), SHA exact `2e28b33fa0b58609a211840fd2046ffa953c1af7` : **completed/success**. Logs des jobs `121873838978` et `121873839194` relus : **Windows 1406 passed/2 skipped; Ubuntu 1405 passed/3 skipped**, agrégation des processus Qt et cœur. Neuf marqueurs concordants SHA/run dans chacun; deux empreintes JSON canoniques rules égales entre OS, empreintes brutes différentes (ne pas les confondre).
- Le succès de cet ancien SHA ne rend pas verte la CI du HEAD documentaire. Le budget Actions doit être débloqué par le propriétaire avant une nouvelle preuve CI finale; aucun droit de dépense n'est déduit.

## Fonctions existantes : réutiliser avant de développer
Inspection de code suivi synchronisé au HEAD GitHub, tests associés relus et CI précédente contrôlée; **pas de suite locale relancée, pas d'application ni fournisseur lancé durant cette reprise**.

| Besoin | Implémentation constatée | Complément réel |
|---|---|---|
| Six écrans, chat commun, activité, Enter/Shift+Enter, galerie/images | `desktop/window.py`, `widgets.py`, `images.py`; tests Qt/workflow/images | Garder les composants; vérifier les boutons et amorces dans le flux unifié. |
| Collage, attachement/drop .txt/.log, validation, publication exclusive et doublons | `desktop/ingestion.py:83,111,154,172,240`; tests ingestion/concurrence/legacy | Extraire localement la question jointe au journal et la poursuivre automatiquement sur la bonne partie. Publication actuelle UUID : ne pas la réécrire juste pour changer les noms. |
| Analyses locales, statistiques et mémoire des combats | `battle_coach.py`, `battle_batch.py`, `learning_loop.py`, `legacy_bridge.py` | Exposer des projections ciblées par partie/version; conserver le pont schéma7 et l'historique. Les compteurs historiques du propriétaire n'ont pas été revalidés. |
| Session Codex stdio, streaming, reprise, annulation | `assistant/codex_app_server.py` | Actuellement shell/outils/Web désactivés, sandbox readOnly, approbations refusées, seul outil `pokemind_read`. Ajouter capacités/permissions/outils typés et événements d'exécution; pas simplement enlever DISABLED. |
| Claude et Ollama | `assistant/provider.py` | Claude actuellement `--tools ''` et prompt sans actions; évolution contrôlée des outils. Ollama n'implique pas la présence d'un service/modèle ni l'équivalence d'un agent de développement. |
| Historique conversationnel privé | `assistant/sessions.py`, `window.py:921` | Changer de fournisseur crée actuellement une nouvelle conversation : conserver le fil PokeMind et lier séparément les sessions fournisseurs sans envoyer automatiquement l'ancien privé. |
| Slash et état Codex | Le chemin `send_chat` ne traite pas /status localement; health ne lit que account/read | Registre local de commandes officielles, métriques réellement disponibles, valeurs inconnues explicites. |
| Observation adverse et listes publiques | `opponent_observer.py:47,78`, `deck_library.py`, `competitive.py`, `battle_batch.py:458` | Hypothèses de familles et références PUBLIC60 existent. Le proxy choisit une composition par identifiant, sans classement de variantes tenant compte de toutes les observations : ajouter top1–3, compatibilité, contradictions et export hypothétique60. |
| Matchups et deck versionné | `meta.meta_matchups` (pairings, n, Wilson, filtres), `matchup_analytics.py`, `version_evidence.py`, `counter_deck.py`, exports/légalité/collection | Les moteurs existent : relier les données publiques récentes, leur qualité et la version réellement jouée au même échange; pas de second calcul de statistiques. |
| Recherche et mémoire publiques | `cards.py`, `meta.py`, `rules.py`, `updates.py`, `batch_public_research.py`, `battle_batch.public_context` | Acquisition bornée, enregistrements source_fact et relecture hors ligne existent déjà. Il manque le service conversationnel général cache/fraîcheur → recherche → validation → version/persistance → reçu → réponse. La campagne bornée historique n'est pas un droit de la rejouer. |

## Mémoire Web durable confirmée
Le [cahier §6 bis](../docs/UNIFIED_POKEMIND_ASSISTANT_DESIGN.md#6-bis-mémoire-web-durable--toute-recherche-utile-enrichit-le-cerveau-local), la décision D-233 et les huit `design_requirements` du STATE prescrivent déjà : cache-first, provenance/date/licence/version, faits validés distincts des hypothèses, déduplication, historique, fonctionnement après redémarrage/hors ligne, séparation public/personnel et bilan affiché **après écriture réussie**. Ce n'est pas seulement la mémoire du fournisseur. Il n'est pas permis de présenter ce contrat comme entièrement implémenté.

Les upserts actuels des modules métiers ne démontrent pas à eux seuls l'historisation complète requise. Il faut réutiliser les snapshots/journaux existants et combler les manques démontrés, sans créer un cerveau parallèle.

## Choix techniques vérifiés à la documentation officielle
Consultation du 2026-10-26 Québec :
- [Codex App Server](https://learn.chatgpt.com/docs/app-server) : intégration UI, threads/turns/approbations, `account/rateLimits/read`, `account/usage/read`; outils dynamiques expérimentaux. Le schéma de la version Windows installée reste à qualifier lors de l'exécution autorisée. Une métrique absente reste indisponible; utilisation passée et quota restant sont distincts.
- [Claude Code programmatique](https://code.claude.com/docs/en/headless) : CLI/Agent SDK avec outils et sorties structurées; préférer l'adaptateur existant, qualifier la version et les restrictions réellement applicables.
- [Limitless Tournaments](https://docs.limitlesstcg.com/developer/tournaments) : endpoints tournois, details, standings et pairings. Données accessibles et classification suffisante à vérifier; placements seuls ne prouvent aucun matchup.
- [TCGdex Assets](https://tcgdex.dev/assets) : images low/high et formats documentés; réutiliser le cache d'images existant, sans déduire des droits de redistribution.

**Inférence d'architecture** : App Server peut porter le chat unique et des actions réelles sans développer une deuxième TUI. Ce constat documentaire n'atteste pas l'installation ni les droits effectifs du PC.

## Réalisation proposée et portes restantes
Un seul [mandat majeur en brouillon](MANDATES/PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md) avec étapes internes A–G : capacités/contrats, orchestrateur et outils, import+question, reconstruction/comparaisons, recherche-mémoire, finition UI, réception Windows/build/CI. Audit indépendant à la livraison, sans micro-go par fichier.

Le lancement proposé couvre le code et les validations publiques/synthétiques, ainsi qu'une consultation locale précisément bornée décrite dans le mandat; **aucune de ces opérations n'est autorisée maintenant**. Aucune nouvelle sauvegarde, migration/clone/purge, dépense, tâche planifiée ou commande sur le client du jeu. Les validations OCR, récupération et autres portes V1 historiques restent suivies, sans prétendre que le mandat unifié les prouve toutes. Trainer Hill inaccessible et données publiques insuffisantes doivent être signalés plutôt que fabriqués.

Les sessions/services cloud ordinaires Codex/Claude sont autorisés par préférence propriétaire durable, sans redemande répétitive. Cette préférence n'autorise pas l'envoi automatique de journaux bruts ni de secrets. Le futur accès complet doit refléter les permissions réelles; un shell libre ne garantit pas le cloisonnement privé par une simple consigne de prompt.

## Suite autorisée
Publication de ce rapport assaini et correction des documents d'orchestration seulement. Maintenir `execute_now=false`. Demander **une seule validation de lancement** du mandat majeur concret. L'ancien mandat reste annulé. Contrôler le HEAD publié et sa CI exacte; ne pas marquer une CI bloquée par budget comme réussie.
