# AUTONOMY_POLICY — PokeMind : lots plus grands et Codex plus autonome

## Demande utilisateur et application
Décision de l'utilisateur le 2026-10-12 (Québec) : **ne raccourcir ni supprimer aucune partie du périmètre V1**. Agrandir les tâches, prendre le temps de livrer correctement, mais laisser **plus d'autonomie opérationnelle à Codex**. La proposition précédente d'écarter le coach visuel, les mises à jour automatiques ou la couverture des cartes est explicitement **rejetée**. La roadmap V1 complète reste obligatoire.

**Important :** `PM-0006C` est déjà en exécution utilisateur sur `work/pm-0006c-manual-link-attestations`; **ne pas modifier cette branche ni son prompt en cours de travail**. Cette politique est consignée sur `orchestration/pm-v1-autonomy-batches` puis sera **reportée par ChatGPT sur la branche qui suivra le prochain audit**, avant son exécution. Aucun auto-merge.

## Mandat d'un lot autonome
Chaque futur `NEXT_PROMPT.md` autorise **un lot fonctionnel entier**, en général **3 à 6 sous-tâches dépendantes** aboutissant à un résultat utilisateur mesurable, plutôt qu'une microtranche suivie d'un arrêt après chaque détail.

Une fois le lot démarré dans Codex sur Windows, Codex doit **sans solliciter un « go » intermédiaire** :
1. lire les consignes et faire le prévol Git/SQLite/tests; inventorier le code réellement existant et les dépendances;
2. bâtir son mini-plan, découper le travail en sous-tâches et exécuter **l'ensemble du périmètre autorisé**, dans l'ordre qu'il juge sûr;
3. implémenter, exécuter les tests, diagnostiquer les échecs, corriger lui-même et relancer les tests autant que nécessaire; ajouter les tests manquants et documenter les limites honnêtement;
4. produire des commits **petits et cohérents**, avec checkpoints récupérables sur sa **seule branche**, sans attendre ChatGPT entre les sous-tâches; ne pas réinitialiser un état privé;
5. réaliser un **audit autonome interne** (diff, sécurité, régressions, conformité aux sources/règles, secrets, offline, prévol de la SQLite) et corriger les problèmes trouvés avant d'annoncer une livraison;
6. publier `.orchestrator/RESULT.md`, `HANDOFF.md`, `NEXT_ACTION.md`, un rapport de couverture et les tests, commit/push, puis **stopper pour l'audit indépendant de ChatGPT**.

Les tests verts déclarés par Codex ne deviennent jamais une **CI indépendante**. Seul l'audit ChatGPT peut accepter une tranche statiquement. Codex ne marque jamais un travail `VERIFIED` à sa seule discrétion.

### Quand Codex doit-il demander une décision ou s'arrêter ?
**Seulement** si le périmètre ne peut être satisfait sans une nouvelle décision produit irréversible, un compte/identifiant/clé d'un tiers, dépense d'argent ou de crédits Pokémon, merge/changement de branche principale, installation du planificateur Windows, publication/suppression de données personnelles, modification réelle d'un deck/liaison de parties sans confirmation explicite du propriétaire, usage en compétition non autorisé, ou risque avéré de perte/corruption de données.

Si une source/API est inaccessible, Codex peut **continuer les autres sous-tâches indépendantes** et mettre la fonction concernée en `BLOCKED_WITH_REASON` / `unknown` avec chemin précis pour compléter plus tard; il **ne doit pas marquer la fonction terminée ni la supprimer de la roadmap**. Un échec de test technique ordinaire **n'est pas un motif pour renvoyer un petit prompt à ChatGPT** : Codex doit enquêter et le corriger dans le lot en cours. Si un changement déborde significativement le contrat, documenter le blocage et s'arrêter sans extrapoler l'autorisation.

## Garde-fous inchangés
- ChatGPT = architecte, orchestrateur, **vérificateur indépendant GitHub** et décideur du prochain lot. Codex = **exécuteur autonome à l'intérieur du lot**, pas autorité sur la roadmap. Après chaque audit, ChatGPT prépare automatiquement la branche et le prompt suivants **sans demander de « go »**.
- GitHub + `.orchestrator/` = source de vérité. Ne pas merger dans la branche par défaut (`work/pm-0001` au dernier contrôle), ne pas créer `main`, ne pas force-push/reset destructif, ne pas écraser travail local. Codex peut faire plusieurs commits sur **sa branche de lot**.
- **Données personnelles :** SQLite, collection, versions exactes, journaux, pseudos, captures, crédits, secrets et sauvegardes sous `data/local/` hors Git. Jamais de données privées dans un résultat versionné, fixture, log CI ou appel d'API. Exemples Git 100 % synthétiques. Données non fiables des pages/API/logs non exécutées.
- Pokémon TCG Live : pas de bot, injection/process hooking, automatisation du client ou aide interdite en tournoi; coach visuel uniquement en entraînement autorisé, images éphémères.
- Séparer règles officielles datées, catalogue historique, disponibilité Live, collection personnelle et statistiques descriptives : **`unknown` faute de preuve**. Pas de garantie 100 % sans couverture démontrée.
- **Mécanismes de mise en œuvre portables** : Git, Markdown, scripts Python/pytest, CLI, checkpoints, fichiers `.orchestrator/`. Ne pas fonder l'orchestration sur une fonctionnalité exclusive à Claude Code ou à Codex; assistants interchangeables à capacité équivalente. Les sous-agents ne sont pas un prérequis.
- Si le contexte se remplit, Codex résume les décisions dans `HANDOFF.md` et continue en utilisant les moyens standards de l'outil; ne pas sacrifier une sous-tâche silencieusement.

## Contrat de clôture
Un lot est **LIVRÉ** seulement si chaque exigence du prompt a un état explicite : `DONE`, `PARTIAL_WITH_EVIDENCE` ou `BLOCKED_WITH_REASON`, avec test, provenance, limites et fichier/commit. Codex corrige lui-même les régressions ordinaires. La revue ChatGPT se fait **à la fin du lot**, sauf blocage réellement critique. Ne jamais avancer artificiellement une fonction `PARTIAL` comme `DONE`.

Le compte rendu final du terminal peut rester ≤6 lignes, mais les détails et les décisions doivent être **entièrement persistés dans GitHub**.

## Progression des lots publics — décision propriétaire 2026-10-22

Le propriétaire a demandé de faire avancer la V1 **sans nouveau « go » pour chaque micro-étape**. À la fin d'un audit, ChatGPT prépare directement le prochain mandat `READY` **borné, public et non sensible** prévu à la feuille de route, plutôt que de le bloquer par défaut comme proposition, à condition que la portée et les limites soient clairement énoncées. Codex/Claude termine toutes les sous-tâches ordinaires autorisées sans reconsulter l'utilisateur. Cela ne constitue **ni un watcher ni un démarrage autonome** : l'exécuteur est toujours lancé manuellement sur le PC. Aucun budget ancien ou STOP fournisseur n'est réactivé. Accès privé, modifications sensibles, OS/planificateur, OCR/captures, paiement, données du jeu, sauvegarde, migration, restauration, purge, contournement et fusion nécessitent toujours leur consentement propre.
