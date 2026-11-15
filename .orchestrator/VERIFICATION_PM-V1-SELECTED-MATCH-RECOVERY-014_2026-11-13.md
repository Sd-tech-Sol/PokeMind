# Audit indépendant ChatGPT — PM-V1-SELECTED-MATCH-RECOVERY-014

Date : 2026-11-13. Repo privé `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`.

**Code contrôlé** : `7cede8848fcfeb4606608fed44625df6d612740a`; **rapport contrôlé** : `b6489b5972fe2435d47390d1419f4166b31d7baa`. Base de l'action `4ec8b46bbe00caf816a59207dc0051f82d6d5682`. GitHub affiche exactement **2 commits** depuis la base (un code, un rapport), et la branche distante pointait sur `b6489b5` au moment du contrôle.

## Verdict
**SOURCE_AUDIT_014_PASSED / HISTORICAL_MATCH_LINK_FIXED / OWNED_STAGING_CLEANUP_FIXED / FROZEN_WINDOWS_QA_PENDING / OWNER_GO_FOR_NEXT_CANDIDATE_PENDING / NOT_RELEASE_READY.**

Deux corrections bornées constatées directement dans le diff de code source et confrontées aux tests. Aucun nouveau blocage manifeste identifié par la lecture des portions touchées. **Ce verdict n'est PAS une preuve que l'EXE gelé fonctionne sous le profil réel du propriétaire**. Ne pas confondre avec une CI ou la publication de 0.9.5.

## Résultats vérifiés directement dans GitHub
- Commit source `7cede884` : seulement **2 modules produit** `src/pokemind/desktop/window.py` et `src/pokemind/desktop/services.py`, plus **3 fichiers de tests** : `tests/test_desktop_qt.py`, `tests/test_desktop_workflow_qt.py`, `tests/test_opponent_auto_deck.py`. Aucune modification aux seuils publics du moteur 013, aux statistiques BO1, aux couleurs/bulles, au packaging, aux numéros de version ou aux consentements.
- Commit final `b6489b5` : seulement rapports et fichiers `.orchestrator/`, sans nouveau code. Branche HEAD exact contrôlé via GitHub.
- Sur **les deux SHA**, `statuses=[]` et `workflow_runs=[]` : aucun statut/CI GitHub associé. `1867 passed / 3 skipped` et **9 parcours Windows natifs par facteur 1 et 1,25** sont des résultats rapportés par Codex : ChatGPT n'a pas exécuté localement `scripts/local_gate.py` ni testé l'EXE installé.

## A — Sélection réelle d'un ancien match
- `MainWindow.games.activated` relie maintenant une activation volontaire, y compris du premier élément, à `game_selected(..., explicit=True)`. Le changement automatique de ligne reste distinct et ne réécrit pas le contexte.
- `game_selected(explicit=True)` vérifie la référence par `match_record` contre le rapport déjà chargé et synchronise `self._combat_match`, `self.services.selected_match`, `conversation['selected_match']`. `matchup_selected` invalide la sélection UI active lors d'un changement de famille, sans inventer un choix du premier match.
- `reconstruction_match()` résout une référence explicite et retourne un **instantané** de la partie sélectionnée; dans Combats, une sélection de la discussion en cours prime seulement si elle est réellement activée et encore visible. Sans référence valide, `None` → refus `NO_SELECTED_MATCH`, aucun « dernier match » implicite. `reconstruct_selected_deck` utilise cette résolution avant le worker.
- `resume_conversation`, `new_conversation`, `view_import` et `ingest_done` synchronisent/revalident la référence sans autoriser d'appel fournisseur pour cette commande locale. Import sans consentement cloud associé à la partie courante et aucune création rétroactive générale au démarrage.
- Les **nouveaux tests Qt** utilisent les vrais widgets `matchups`, `games`, `history_picker` avec souris et clavier; test réel `test_013_explicit_selected_old_match...` ne pose plus directement `Services.selected_match`. Cas couverts : OLD-A2 vs dernier match, non-doublon, changement de famille/automatique, ancienne discussion et redémarrage, référence obsolète, import local sans cloud, annulation/résultat tardif. Évidence source : ces tests existent et ciblent le trou 013; **leur réussite est rapportée** par Codex.

## B — Fichier temporaire de sauvegarde
- `Services._save_deck` mémorise `os.fstat` du fichier temporaire ouvert avec `'xb'`; un `finally` vérifie le chemin `safe_path` et compare `samestat` avec `lstat` avant de supprimer **uniquement** l'alias qu'il a créé. Les anciennes cibles et autres fichiers `.pending` ne sont pas nettoyés; `os.link` reste une publication exclusive sans écrasement.
- Tests d'injection `PermissionError`, collision avec destination existante, annulation, succès et collision sur nom temporaire préexistant préservent les autres fichiers; aucune opération sur données personnelles pendant les essais selon Codex.
- Cas théorique limite : erreur système pendant le `finally` peut encore laisser un alias, plutôt que d'essayer un nettoyage dangereux; ce n'est pas un blocage identifié de la V1, et aucun nettoyage global n'est autorisé.

## Risques et limites qui restent
- Les tests source/natifs sur fixtures ne remplacent **pas** une nouvelle compilation de l'EXE/Setup à partir de ce SHA, validation du binaire gelé Windows et réception de la GUI par le propriétaire.
- Les seuils d'admission 013 restent heuristiques et prudents; une vraie défaite peut ne rien enregistrer si aucune référence publique compatible suffisamment étayée n'est en cache. Ne pas promettre une reconstruction de tous les anciens journaux.
- Le PokeMind 0.9.5 installé sur la machine de l'utilisateur demeure le **candidat 009 ancien**, sans les modifications 013/014; sauvegardes personnelles 012 conservées. Aucun contrôle de leurs contenus n'est effectué par ChatGPT.

## Décision proposée
**Clore le développement source V1; ne pas lancer de tâche 015 de code.** Prochaine décision utilisateur unique : autoriser **un dernier candidat Windows intégrant 013+014**, compilation et QA isolée sur données synthétiques, validation SHA et sauvegardes conservées, puis installation contrôlée sur le même AppId **conditionnellement à tous les prévols** et réception manuelle par le propriétaire. Ce mandat Windows doit être préparé **seulement après GO explicite couvrant l'étendue proposée**; ne jamais installer/publier maintenant et ne pas utiliser le Setup 009 pour les fonctionnalités 013/014. Le GO final de publication publique doit rester distinct après réception utilisateur.

Aucun nouveau prompt agent actif pendant l'attente du GO. `NOT_RELEASE_READY` jusqu'à réception de la vraie version installée.
