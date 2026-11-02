# Skill portable — GitHub Independent Audit (ChatGPT)

## Intention
Sur demande « Codex/Claude a fini, vérifie », vérifier **directement** GitHub au lieu de se fier au texte de la session de l'exécuteur. Ce document est une **procédure manuelle** : sans mécanisme complémentaire, il ne surveille pas GitHub en continu.

## Procédure
1. Confirmer dépôt privé `Sd-tech-Sol/PokeMind-dev` (renommé D-271; `Sd-tech-Sol/PokeMind` sera le dépôt public), branche active et HEAD distant; lire `AGENTS.md`, `.orchestrator/SESSION_CONTINUITY.md`, `.orchestrator/STATE.json`, `.orchestrator/RESULT.md`, `.orchestrator/HANDOFF.md`, `.orchestrator/NEXT_ACTION.md`, `.orchestrator/DECISIONS.md`. Identifier les mandats archivés et les permissions courantes.
2. Comparer base de référence / HEAD à la livraison. Inspecter liste des fichiers, le diff, le code, les tests et les éventuelles preuves non sensibles. La déclaration « terminé » n'est **pas** une preuve suffisante.
3. Lire le run CI associé au **même SHA**, ainsi que les logs/jobs utiles. Ne pas substituer un run d'un ancien commit; si run en cours, écrire `PENDING_CI`.
4. Distinguer `CONFIRMÉ_GITHUB` (commit/diff/CI) et `RAPPORTÉ_EXÉCUTEUR_LOCAL` (état des fichiers privés/Windows/SQLite). Des tests CI sur fixtures ne vérifient pas la machine personnelle.
5. Verdict documenté avec portée : `VERIFIED`, `REJECTED`, `BLOCKED` ou `AWAITING_EVIDENCE`. Un diagnostic peut être vérifié sans que le produit ou la sauvegarde soit validé.
6. Publier l'audit non sensible sous `.orchestrator/` et l'état/mandat suivant dans `STATE.json`, `NEXT_ACTION.md`, `HANDOFF.md`, `DECISIONS.md` si décision effective. Ne jamais autoriser une nouvelle opération sensible sans consentement explicite du propriétaire. Vérifier nouveau HEAD et CI, sans prétendre qu'une CI pending est verte.
7. STOP et communiquer uniquement l'état vérifié, les limites et la prochaine décision/proposition.

## Restrictions
Ne pas lire/écrire les données privées par GitHub, pas de merge `main` ni force-push. Ne pas inventer de logs locaux. Des contrôles périodiques ou webhooks exigent une installation distincte; **aucun watcher, scheduler ou agent réveillé automatiquement n'est fourni par ce skill**.
