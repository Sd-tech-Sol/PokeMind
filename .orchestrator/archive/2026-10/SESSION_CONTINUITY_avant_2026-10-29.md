# PM-V1-LIVE-FR-EN-UI-001 — clôture de session, reprise sur audit indépendant

2026-10-28 Québec. Fermeture propre demandée par le propriétaire; **point de reprise enregistré, aucun mandat produit relancé**. État conservé : **AWAITING_AUDIT**, `execute_now=false`, autorisation consommée, réception propriétaire non effectuée. V1 **NOT_RELEASE_READY**, CI **AWAITING_EVIDENCE**.

Livraison FR/EN : source testée/compilée `51aa92e8cdd04e7e2c7bca4d4a478b29dcb55517`, rapport publié `3035d9a712787237c4e4afc50940f30a085b07a8`; 160 tests distincts réussis selon Codex, même `dist/PokeMind/PokeMind.exe` mis à jour et ancienne distribution conservée. Ces contrôles ne sont pas rejoués à la clôture. [Preuves de livraison](EVIDENCE_PM-V1-LIVE-FR-EN-UI-001.md).

CI du commit de livraison `3035d9a712787237c4e4afc50940f30a085b07a8` : [Actions 40643154561](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40643154561), conclusion `failure`; jobs Windows et Ubuntu **non démarrés, zéro étape**, annotation indiquant un blocage par le budget Actions. Aucun échec de test exécuté ni succès CI déduit. Le commit documentaire de clôture aura son propre HEAD/sa propre CI à contrôler; aucun rerun ni changement de budget/workflow autorisé.

**Reprise :** lire `AGENTS.md`, puis l’ordre V2 (`SESSION_CONTINUITY`, `WORKFLOW_ADOPTION_V2`, `STATE`, premier mandat `NEXT_ACTION`, `HANDOFF`, `RESULT`, `DECISIONS` et preuves), synchroniser la branche autorisée sans reset/force-push. Prochaine action unique : **audit indépendant ChatGPT du HEAD distant exact**, de la source indiquée et de la CI; ensuite réception visuelle propriétaire du choix FR/EN dans son EXE habituel. Codex ne relance ni tests, compilation, installation, ancienne QA ou opération personnelle sans nouvelle demande ciblée. Les archives ne sont pas des permissions.

Cette clôture modifie uniquement les pièces de passation assainies. Aucun accès aux données personnelles, lancement d’application, import, backup, migration, nettoyage ou suppression; aucune tâche de fond ajoutée.

---

# PM-V1-LIVE-FR-EN-UI-001 — FR/EN à chaud livré / STOP audit

2026-10-28 Québec. Français/anglais interchangeables à chaud dans **Réglages → Langue de l’application**, choix conservé au prochain lancement. Pages, navigation, préférences, graphiques, filtres, infobulles, accessibilité, dialogues Qt et messages applicatifs suivent la langue; pas de reconstruction de fenêtre ni de rechargement des données. Catalogue local de 512 équivalents. Source **`51aa92e8cdd04e7e2c7bca4d4a478b29dcb55517`**. **160 tests distincts verts : 93 Qt et 67 services/reçus**, dont neuf nouveaux tests de bilinguisme; répétitions non additionnées. [Preuves](EVIDENCE_PM-V1-LIVE-FR-EN-UI-001.md).

Compilation Windows et smoke du vrai portable production sur fixture indépendante **exit0**, 12 modules PYZ et l’entrée app conformes aux sources (13), traduction Qt française embarquée, démarrage anglais inspecté. Même **`dist/PokeMind/PokeMind.exe`** mis à jour : **788 nouveaux fichiers**, précédent dossier de 788 binaires intégralement conservé, installé conforme au candidat. Aucun lancement de l’application propriétaire ni accès/inventaire personnel, aucun nouveau comptage de matchs, backup DB, migration, import personnel ou suppression. Les textes sourcés, exports et messages historiques restent dans leur langue d’origine; les nouvelles demandes au coach indiquent la langue choisie, aucun appel réel de fournisseur testé.

**CODEX_LOCAL_REPORTED / REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT; execute_now=false, consumed=true. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.** Prochaine action unique : audit indépendant ChatGPT du HEAD distant et de sa CI exacte, puis réception propriétaire du même EXE. Aucun acte automatique, rebuild, rollback, import, backup ou migration. Aucun succès CI ni réception propriétaire revendiqué.

---

# PM-V1-POKEDEX-EXPERIENCE-STATS-001 — expérience et statistiques livrées / STOP audit

2026-10-28 Québec (GO 2026-10-27). Cinq améliorations et statistiques graphiques livrées : cartes avec reflet/zoom, chat unique en bulles et sources repliables, favoris/parties/point de travail sur l'accueil, six icônes/menu repliable, fiches/frise des faits connus; quatre vues statistiques avec filtres, effectifs et couverture explicites. Sources finales **`e8f9849c5fad71d1de70e30dadccf78d54d91ef7`**, implémentation principale `ad064dcd62dfaf6ec852e90862353993d12bbd1c`. **84 tests distincts verts dont 18 nouveaux**, 18 aussi confirmés après ajustement des sources; passes non additionnées. Banc Qt corrigé pour une seule QApplication par session après deux passes 83/1. [Preuves](EVIDENCE_PM-V1-POKEDEX-EXPERIENCE-STATS-001.md).

Vrai build et smoke production frozen **exit0** sur fixture indépendante; sept modules modifiés embarqués conformes. Distribution complète finale installée au même `dist/PokeMind/PokeMind.exe`, **788 nouveaux fichiers**, précédent dossier 788 fichiers conservé, versions antérieures retenues, aucun nettoyage. Ancien premier candidat également qualifié, puis libellé de pièce jointe raccourci avant la livraison finale. Aucun accès/inventaire personnel ni nouveau comptage des matchs, aucun lancement propriétaire; réception personnelle non effectuée.

**CODEX_LOCAL_REPORTED / REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT; execute_now=false, consumed=true. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.** Prochaine action unique : audit indépendant ChatGPT du HEAD distant et de sa CI exacte, puis réception visuelle propriétaire du même EXE. Aucun rebuild, rollback, backup DB, import, migration ou acte automatique. Pas de taux global, dates, causalité ou données de jeu fabriqués.

---

# PM-V1-POKEDEX-MOTION-001 — animations livrées / STOP audit

2026-10-27 Québec. Demande manuelle d'animations exécutée : transitions natives fondu/glissement, survols lumineux, onde au clic, Poké Ball réactive et dessin progressif des graphiques. Réduction des animations persistante dans Réglages; réglages lisibles et défilables sur petite fenêtre. Source **`7dbb66858e83e2afc482a8843fd0f2326395b617`**. **66 tests Qt distincts verts dont 4 nouveaux**, navigation rapide/resize/clavier/fermeture couverts, inspection native sombre/clair et 1100×700; effets arrêtés au repos. [Preuves](EVIDENCE_PM-V1-POKEDEX-MOTION-001.md).

Vrai build production et smoke frozen Windows **exit0** sur fixture indépendante, 5 modules embarqués conformes aux sources. Distribution entière installée au même `dist/PokeMind/PokeMind.exe`, 788 anciens fichiers conservés et 788 nouveaux conformes. Aucun accès ou inventaire personnel, compteur de matchs réel non recalculé, aucune réception propriétaire. **66 désigne les tests**, pas une nouvelle vérification des matchs.

**CODEX_LOCAL_REPORTED / REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT; execute_now=false, consumed=true. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.** STOP audit ChatGPT du HEAD distant et de la CI SHA exact. Aucun rebuild, rollback, import, backup, migration ou autre acte automatique. Le nouveau choix graphique du propriétaire supplante l'attente précédente sans réexécuter l'ancien mandat.

---

# PM-V1-POKEDEX-VISUAL-REFRESH-001 — nouvel habillage livré / STOP audit

2026-10-27 Québec. Nouvelle demande graphique exécutée : style Pokédex rouge/anthracite/blanc/jaune, Poké Ball locale, navigation, bannière, graphiques et thèmes clair/sombre; tableau de bord défilant sur petite fenêtre. Source **`44f966b0bed3bc93dd917d08d952e317379684c3`**. **62 tests Qt distincts verts**, inspection native des deux thèmes et de 1100×700, vrai portable production frozen exit0 sur fixture indépendante. Distribution entière installée au même `dist/PokeMind/PokeMind.exe`; **788 anciens fichiers conservés**, 788 nouveaux conformes au candidat. Aucune donnée personnelle ouverte ou modifiée; aucun compteur de matchs personnel recalculé, aucun lancement propriétaire. [Preuves](EVIDENCE_PM-V1-POKEDEX-VISUAL-REFRESH-001.md).

**CODEX_LOCAL_REPORTED / REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT; execute_now=false, consumed=true. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.** STOP audit indépendant ChatGPT du HEAD distant et de la CI exacte; aucun rebuild, rollback, import, backup, migration ou autre acte automatique. La demande courante supplante l'attente précédente par ce seul chantier graphique, sans qualifier une réception personnelle.

---

# PM-V1-WINDOWS-EXE-IN-PLACE-UPDATE-001 — livré localement / STOP audit

2026-10-27 Québec. Véritable `dist/PokeMind/PokeMind.exe` confirmé par le propriétaire et mis à jour au même endroit, source `a232f17fc56e43722a50a12c5b527a3099db00db`. Ancien dossier binaire intégral conservé, rollback disponible; rapport 66→66, DB historique 5→5 et schéma 7→7, métadonnées personnelles inchangées. 123 tests verts, 4 refus build, vrai portable frozen exit0 sur fixture indépendante. **AWAITING_AUDIT / REPORTED_COMPLETE_LOCAL / execute_now=false / consumed=true**. [RESULT](RESULT.md), [preuves](EVIDENCE_PM-V1-WINDOWS-EXE-IN-PLACE-UPDATE-001.md), [STATE](STATE.json), [seule action active](NEXT_ACTION.md). **STOP audit indépendant ChatGPT**; aucun mandat historique réactivé, aucune réception personnelle accomplie. V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE.

---

# Livraison QA du 2026-10-27 — STOP audit indépendant

`PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001` consommé, `execute_now=false`, `AWAITING_AUDIT`. 302 tests distincts verts et lanceur manuel fictif qualifié localement, reprise native vérifiée par Codex. [RESULT](RESULT.md), [preuves](EVIDENCE_PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001.md), [STATE](STATE.json). La réception propriétaire attend sa décision après audit. Aucun ancien mandat réactivé; V1 NOT_RELEASE_READY, CI AWAITING_EVIDENCE et Option B sans sandbox OS.

---

# ADDENDUM 2026-10-17 — noyau V2 portable adopté sur PokeMind

Lire maintenant en plus `.orchestrator/WORKFLOW_ADOPTION_V2.md` et `.orchestrator/STATE.json`. Les deux procédures manuelles portables `.orchestrator/skills/github-executor/SKILL.md` (Codex/Claude) et `.orchestrator/skills/github-auditor/SKILL.md` (ChatGPT) sont disponibles. Ces documents ne créent aucun watcher, processus persistant ni nouvelle permission d'agir.

Pour chaque tâche, maintenir `STATE.json` cohérent avec NEXT_ACTION/HANDOFF/RESULT. Si divergent, STOP. `BLOCKED` signifie qu'aucun agent ne peut reprendre une opération privée sans ordre du propriétaire. L'ordre de démarrage après /clear, reboot ou nouveau chat reste GitHub → AGENTS → SESSION_CONTINUITY → STATE → NEXT_ACTION → HANDOFF/RESULT → skill selon rôle.

---

# PokeMind — protocole permanent de continuité GitHub (ChatGPT / Codex)

## Règle principale
**Le dépôt GitHub et les fichiers versionnés `.orchestrator/` sont la source de vérité durable.** Le contexte du clavardage ChatGPT et la mémoire de session Codex **ne sont pas des preuves de progression**. Après fermeture du PC, perte de session, `/clear`, nouveau clavardage ou arrivée d'un autre modèle, **tout agent doit repartir des fichiers GitHub**.

## Rôles
- **Propriétaire** : autorise les actes sur ses données. Un consentement est ciblé par l'action, le fichier/répertoire et le nombre de tentatives; il n'autorise ni migrations ni suppressions implicites.
- **ChatGPT** : architecte/orchestrateur, prépare et publie les mandats dans GitHub, lit les résultats, inspecte indépendamment GitHub, les diffs et la CI au SHA exact. Pour une opération sur le PC qu'il ne peut pas exécuter, il **ne prétend jamais** avoir vérifié physiquement la base : il distingue `RAPPORTÉ_PAR_CODEX_LOCAL` de `VERIFIED_PAR_CHATGPT_GITHUB`.
- **Codex / Claude Code** : exécutants dans la branche autorisée, suivent le mandat actif, produisent preuves techniques, commit + push des **rapports non sensibles**. Aucun exécuteur ne s'auto-attribue le statut `VERIFIED`.

## Reprise de session (obligatoire)
1. Vérifier branche, `HEAD`, `git status` et synchroniser avec le distant **sans écraser le travail local** (fetch / pull --ff-only si possible; pas de reset/force-push).
2. Lire `AGENTS.md` et, dans cet ordre, `.orchestrator/SESSION_CONTINUITY.md`, `.orchestrator/NEXT_ACTION.md`, `.orchestrator/HANDOFF.md`, `.orchestrator/DECISIONS.md`, `.orchestrator/RESULT.md`, puis références de l'action en cours. **Le PREMIER en-tête de NEXT_ACTION est le mandat actif**; les sections d'archive sont historiques. `NEXT_PROMPT.md` ne s'applique que si NEXT_ACTION y renvoie explicitement.
3. Ne jamais reprendre une action privée sur la seule foi de notes historiques ou d'un `/clear`. Relever permissions et STOP actuels; si le mandat est terminé ou bloqué, ne pas relancer la même opération.
4. Pour les tâches purement techniques : ne pas ouvrir la base personnelle, même via une commande implicite `status/search`.

## Livraison durable avant STOP (règle systématique)
Aucun simple « terminé » en terminal n'est une livraison suffisante.
- Codex doit publier sur la **branche GitHub autorisée** les modifications de **documentation non sensibles** : `.orchestrator/RESULT.md` (ce qui a été fait/observé, preuves et limites), `.orchestrator/HANDOFF.md` (état courant), `.orchestrator/NEXT_ACTION.md` (seul prochain geste autorisé et ses blocages), et `.orchestrator/DECISIONS.md` lorsqu'une décision a été effectivement prise. Une fiche d'audit supplémentaire peut compléter ces documents.
- **Y compris après un prévol arrêté ou un acte local privé** : publier un **résumé assaini** de l'état, sans les données privées ni chemins absolus; marquer clairement `RAPPORTÉ_PAR_CODEX_LOCAL`, `STOP`, `PARTIAL`, `NOT_VERIFIED` ou `AWAITING_CHATGPT_AUDIT`. La preuve brute reste **sur le PC**.
- Si un run produit une exception ou laisse des résidus : publier seulement la catégorie neutre de l'erreur et la prochaine vérification non destructive. **Ne jamais publier le fichier SQLite, le manifeste personnel, la sauvegarde, leur contenu, leurs hachages, noms de fichiers privés identifiants, chemins absolus, captures, journaux de combat, clés ou une liste de fichiers personnels.**
- Commit et push uniquement ces documents assainis, sans `git add .`; inspecter `git diff --cached`, chemins suivis et `.gitignore`, vérifier qu'aucun artefact privé ne part. Pas de merge `main`, reset ou force-push.
- Après publication : vérifier `HEAD` distant, SHA, CI Windows et Ubuntu héritée si déclenchée, état exact de ses jobs; si CI non terminée, noter `PENDING`. **STOP pour audit indépendant ChatGPT.**
- **Exception** : si GitHub indisponible, si sécurité/confidentialité non garantie ou si un mandat contient un STOP interdisant toute écriture, ne pas contourner l'interdiction. Garder les données sur le PC; rapporter clairement « publication non réalisée » et demander un nouveau mandat. L'autorisation **de mettre à jour les seuls documents non sensibles** est indépendante de l'autorisation d'effectuer une opération personnelle.
- ChatGPT doit lui aussi publier son audit et la suite (ou STOP) dans GitHub; vérifier le dernier SHA du dépôt après publication. Aucun contrôle privé local n'est présenté comme vérifié par GitHub.

## Critères de fermeture
Une opération peut être `REPORTED_COMPLETE_LOCAL` avec preuve locale mais encore `STOP/OWNER_REVIEW_REQUIRED`. Une CI verte **prouve les tests exécutés sur GitHub**, pas la santé du PC. Une sauvegarde avec `backup verify=verified` rapporté mais un contrôle postérieur inconclus reste **validation opérationnelle en attente**; ne pas relancer backup/create et ne pas autoriser de migration.

## Raccourcis de reprise
- Codex : `/clear` seulement à l'arrêt entre tâches; reprendre en lisant les fichiers précédents depuis GitHub.
- Nouvelle conversation ChatGPT : « Reprends Sd-tech-Sol/PokeMind sur la branche indiquée par GitHub. Lis AGENTS.md et .orchestrator/SESSION_CONTINUITY.md, NEXT_ACTION, HANDOFF, RESULT et DECISIONS. Vérifie HEAD, commits et CI indépendamment, puis donne uniquement le prochain mandat. »
