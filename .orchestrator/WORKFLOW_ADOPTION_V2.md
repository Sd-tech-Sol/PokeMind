# Adoption progressive de la méthode IA V2 — PokeMind

## Décision
**À compter du 2026-10-17, propriétaire : appliquer sur PokeMind le noyau commun portable de la méthode IA V2**, en conservant les preuves GitHub et la séparation ChatGPT (architecture/audit) / Codex ou Claude Code (exécution).

Le dépôt central `Sd-tech-Sol/AI-Project-Workflow` était **encore en étape 0, audit préalable**, lors de l'adoption : **aucune V2 complète n'est installée ni certifiée**. Le propriétaire a explicitement levé **pour PokeMind** l'ancienne exclusion « projets existants non concernés pour le moment ». Cela ne modifie PAS le dépôt central ni les autres projets.

## Ce qui est désormais ACTIF
1. **GitHub comme mémoire canonique** : `AGENTS.md`, `SESSION_CONTINUITY.md`, `NEXT_ACTION.md`, `RESULT.md`, `HANDOFF.md`, `DECISIONS.md`; `STATE.json` pour le résumé machine, sans recopier les détails de chaque mandat. `PROJECT_SPEC.md` reste la description projet actuelle : **ne pas créer un PROJECT.md redondant**.
2. **Deux skills compatibles et manuels** :
   - `.orchestrator/skills/github-executor/SKILL.md` pour Codex **ou** Claude Code.
   - `.orchestrator/skills/github-auditor/SKILL.md` pour ChatGPT.
   Tous deux sont des procédures Markdown, lisibles sans dépendance ou fonctionnalité exclusive à un fournisseur; ils ne sont **pas** des démons/schedulers/hooks.
3. **Protocole d'états** : `READY` (tâche et permission d'exécution confirmées), `IN_PROGRESS`, `AWAITING_AUDIT`, `VERIFIED` (**portée du constat seulement**), `BLOCKED`. `PENDING_CI` et `AWAITING_OWNER_APPROVAL` sont des **motifs explicatifs** ou sous-états plutôt qu'une seconde hiérarchie incohérente. Si `STATE.json` diverge de `NEXT_ACTION` ou des décisions, **STOP**.
4. **Identification/idempotence** : chaque tâche a un ID et une portée; ne jamais relancer un mandat historique après redémarrage ou une opération locale sous prétexte que son rapport n'est pas poussé. Pas de double `backup create`, de migration automatique, ni d'élévation de permissions en déduisant un statut.
5. **Preuves et audits** : Codex publie des résultats assainis; ChatGPT inspecte HEAD, diff, CI SHA exact, publie son audit et mandat suivant; `IMPLEMENTED` ou `RAPPORTÉ_LOCAL` n'équivaut pas à `VERIFIED`. Les données privées restent hors GitHub.
6. **Reprise après `/clear` / panne / nouveau clavardage** : resynchroniser les fichiers et reprendre l'état, sans dépendre de la mémoire de conversation; aucun nouveau travail tant que STOP ou approbation propriétaire ne sont pas levés.

## Ce qui n'est PAS installé
- **Aucune surveillance permanente de GitHub**, webhook, tâche planifiée, logiciel de fond, réveil de ChatGPT ou d'un terminal Codex/Claude, et aucun auto-démarrage d'un mandat.
- Aucun remplacement de l'interface ChatGPT Web par Desktop/Work; aucune dépendance MCP/plug-in nouvelle.
- Aucune modification du moteur PokeMind ou de sa base, ni automatisation de sauvegarde.
- L'installation générique de la méthode centrale reste à concevoir/approuver dans `AI-Project-Workflow`.

## Statut projet au moment de l'adoption
- Un unique backup moderne aurait été créé, puis `backup verify` aurait réussi **selon Codex local**; GitHub ne peut pas prouver cette opération sur Windows.
- Dernier diagnostic métadonnées Codex accepté par ChatGPT; CI Win 480/2, Ubuntu 479/3 sur `702ccddd`.
- Anomalie historique `POST_VERIFY_RESIDUE_OR_UNSAFE_FILE` = `CAUSE_NON_RECONSTRUITE`, et aucun résidu courant observé (selon rapport local).
- **Aucune nouvelle création de sauvegarde**. Préparer seulement un mandat pour une **unique nouvelle vérification publique lecture seule du backup moderne existant**, soumise à l'instruction explicite du propriétaire à Codex. V1 `NOT_RELEASE_READY`.

## Contrat des agents
- Après nouvelle livraison Codex ou Claude : publier `.orchestrator/RESULT.md`, `HANDOFF.md`, `NEXT_ACTION.md`, `STATE.json`, `DECISIONS.md` si nouvelle décision, commit/push des seuls docs assainis, STOP audit.
- Après audit ChatGPT : verdict de portée, preuve de CI au SHA exécuté, nouveau statut et mandat dans GitHub. Si CI nouvel audit encore pending, ne pas la présenter comme réussie.
- **L'autorisation d'écrire des rapports publics ne permet pas une opération privée**. Si publication assainie est impossible, STOP et signaler le blocage.
- La présence d'un nouveau commit n'est pas une permission d'exécuter une tâche; la future détection automatique devra respecter ce contrat.
