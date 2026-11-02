# Skill portable — GitHub Executor Handoff (Codex et Claude Code)

## Intention
Exécuter **uniquement** une tâche autorisée et durablement publier son résultat assaini dans GitHub. Fonctionne à la demande dans Codex **ou** Claude Code; aucune API, hook, commande slash ou capacité exclusive n'est requise. **Ce document n'installe aucun watcher et n'exécute aucune tâche automatiquement.**

## Entrée
Repo privé `Sd-tech-Sol/PokeMind-dev` (renommé D-271; `Sd-tech-Sol/PokeMind` sera le dépôt public), branche désignée `work/pm-v1-lotj-final-readiness-windows`, `.orchestrator/STATE.json` (résumé structuré), `.orchestrator/NEXT_ACTION.md` (mandat détaillé), `AGENTS.md`, `.orchestrator/SESSION_CONTINUITY.md`, `.orchestrator/HANDOFF.md` et `.orchestrator/DECISIONS.md`. Les mandats archivés ne confèrent aucun droit.

## Procédure portable
1. `git status`; examiner les changements locaux; `git fetch`, `git pull --ff-only` **seulement si sûr**. Vérifier la branche, HEAD, état et autorisation **actuels**; ne jamais reset/force-push.
2. Lire les documents de gouvernance. Contrôler `STATE.json` et les références; en cas de désaccord avec les fichiers narratifs, **STOP** et demander arbitrage (ne jamais sélectionner une tâche au hasard).
3. Si statut `BLOCKED`, `AWAITING_AUDIT` ou mandat exécuté, **ne pas relancer**. Pour les actes privés : exiger consentement explicite du propriétaire, chemin, portée et nombre d'essais. Les commits GitHub ne constituent pas ce consentement.
4. Pour une tâche autorisée, travailler dans le périmètre exact. Toute panne, sortie ambiguë, résultat inattendu, modification concurrente ou limite de confidentialité impose STOP. Ne pas reconduire automatiquement les étapes, ni accéder à une base privée hors autorisation.
5. Terminer avec `RESULT.md` (faits, preuves et limites), `HANDOFF.md` (checkpoint), `NEXT_ACTION.md` (STOP ou prochain mandat), `STATE.json` (même statut, ID et référents), `DECISIONS.md` si **nouvelle décision**. Conserver les archives sans confondre mandat actif et historique.
6. **Rapport assaini uniquement** : jamais de DB, sauvegarde, manifeste, empreinte personnelle, identifiant, capture, chemin Windows absolu ou contenu personnel dans Git/GitHub. Inspection du `git diff --cached` et des seuls chemins explicitement préparés; commit/push non destructif sur branche autorisée.
7. Vérifier HEAD distant et la CI **au SHA exact**. Si pending, dire pending. Conclure `AWAITING_AUDIT` ou `BLOCKED` plutôt que `VERIFIED` : **seul ChatGPT peut auditer indépendamment**. STOP.

## Garantie
Cette procédure est un protocole manuel partagé, **pas** une promesse de surveillance ou d'exécution autonome. Aucun agent ne doit passer `BLOCKED` à `READY` parce qu'un fichier Git a changé; la permission humaine prévaut.

## Reprise
Après reboot ou `/clear`, recommencer par l'étape 1. L'historique de chat n'est jamais autorité.
