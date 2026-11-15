# Audit indépendant ChatGPT — PM-V1-DECKLAB-RANKING-STATISTICS-UX-016

Date : 2026-11-14. Dépôt privé `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`. Base `ab31142db74d0086ced09cc50301f316c5a7819d`; commit source `66a1ce0a2f974a480485110bbc10e8d7c086368b`; rapport privé Codex `3bee9c0fe647ee4dfe061f6c37de2ca77141f5a2`.

## Verdict

**SOURCE_016_INDEPENDENT_REVIEW_PASSED / SYNTHETIC_QT_SCREENSHOTS_VISUALLY_INSPECTED / INSTALLED_015_UNCHANGED / OWNER_GUI_RECEPTION_PENDING / NOT_RELEASE_READY.**

Les deux correctifs UI demandés sont présents, la réorganisation Qt est cohérente et les captures synthétiques confirment que l'information prioritaire n'est plus masquée à l'écran. Aucun blocage immédiat de V1 n'est identifié dans les modules touchés. Les résultats exécutables sur le PC Windows et le nombre de tests sont **rapportés par Codex**, non rejoués par ChatGPT; la navigation et l'expérience du futur EXE installé ne sont **pas vérifiées**.

## Périmètre GitHub vérifié directement

- Branche distante HEAD `3bee9c0fe647ee4dfe061f6c37de2ca77141f5a2`, compare depuis `ab31142` = **2 commits**, un code+QA `66a1ce0` et un rapport/orchestration `3bee9c0` ; seulement `src/pokemind/desktop/window.py`, `src/pokemind/desktop/charts.py`, `tests/test_desktop_workflow_qt.py`, `docs/QA_PM_DECKLAB_RANKING_016.md`, 7 captures QA et fichiers `.orchestrator/`. Aucune modification `services.py`, `deck_public_stats.py`, `insights.py`, `opponent_observer.py`, `data_archive.py`, scripts de build/installer, version ou dépendances.
- Fichiers `.orchestrator/RESULT.md`, `STATE.json`, `NEXT_ACTION.md`, `HANDOFF.md` lus directement au SHA final. `NEXT_PROMPT.md` 016 est CONSUMED, et l'original a été archivé. Aucun nouveau candidat ni autorisation de build/install/publication.
- `get_commit_combined_status`: `statuses=[]` sur le SHA rapport. `fetch_commit_workflow_runs`: `workflow_runs=[]` sur ce SHA; les mêmes endpoints consultés sur le SHA code n'ont pas montré de CI. Ces éléments ne remplacent pas une suite de tests indépendante.

## Vérification du code — classement visible

- `window.py:_DeckPicker` utilise un délégué natif et un rendu qui élide à droite. `loaded_decks` met dorénavant le préfixe **`#rang · taux % ·` avant le nom long**, aussi bien fermé qu'ouvert; cas inconnu `— · Données insuffisantes · nom`. Le deck principal suit le préfixe au lieu de le repousser; tooltip et description accessible gardent source, n, période, taux PUBLIC BO1 et précautions.
- Onglet `Classement` ajouté **à l'indice 3 après Galerie, Liste texte, Statistiques**, `QTableWidget` en lecture seule, 4 colonnes `Rang / Deck / Victoires PUBLIC BO1 / Matchs (n)`, tous les decks et inconnus affichés. Un clic/sélection clavier synchronise le sélecteur; `deck_selected` synchronise à son tour la table. Le classement est celui fourni par `Services.rank_decks`; aucun nouveau tri ou pourcentage à partir des données privées. `ranking_context` affiche population BO1, seuil et période ou « Données insuffisantes ». Les clés existantes préservent sélection/favori/deck principal/comparaison/galerie.
- La lecture des ajouts et tests vérifie les indices des anciens onglets inchangés, les jeux avec et sans taux, les égalités, l'absence de ligne et le rafraîchissement.

## Vérification du code — statistiques allégées

- `charts.py:PublicStatsPanel` crée un taux PUBLIC en grande police, **n, mode BO1/BO3, période, source Limitless et statut** en présentation prioritaire. Le taux vient **directement de `view.archetype.modes[mode].win_fraction`**; aucune fusion de modes ni nouveau calcul d'échantillon. `—` et « Données insuffisantes » restent explicites quand la fraction manque.
- `CountChart` et `project_public_stats` gardent la même structure de données : graphes matchups V/D/N (jusqu'à 8 lignes) distincts de la méta des placements et de l'évolution. La légende courte est visible; seuils, exclusions, intervalles de confiance, sources/dates/URLs et avertissement personnel/public sont déplacés dans `Sources et détails` natif `QToolButton` replié initialement, sélectionnables et copiables, ouvert au clavier.
- Le statut d'erreur de rafraîchissement reste visible hors du repli et après changement de thème; absence de snapshot et identité ambiguë n'affichent pas de faux `0 %`.

## Captures réellement inspectées par ChatGPT

J'ai **ouvert les PNG synthétiques directement depuis le SHA source GitHub** (contenu binaire base64 du connecteur) pour :
- `docs/qa/decklab-016/ranking-dark-125.png` : le sélecteur supérieur montre `#1 · 48,7 %` avant le nom élidé; onglet `Classement` a `#1 48,7 % n=117`, `#2 42,0 % n=100`, puis 3 entrées « Données insuffisantes » ; colonnes visibles et source/période sous le tableau.
- `docs/qa/decklab-016/popup-dark-125.png` : dans le menu ouvert, les taux et rangs sont encore visibles à gauche sur noms longs.
- `docs/qa/decklab-016/statistics-dark-125.png` : un KPI `48,7 %` avec `n=117`, BO1, période/Limitless et graphiques remplace le bloc méthodologique dense en haut.
- `docs/qa/decklab-016/details-light-en-125.png` : section dépliée lisible, source complète sélectionnée en bleu et informations d'incertitude disponibles après défilement.
- `docs/qa/decklab-016/unknown-light-en-125.png` : situation inconnue `—`, mention de données insuffisantes, échec de rafraîchissement visible et aucune fausse attribution de taux.

**Ce sont des captures du vrai widget Qt sur des fixtures entièrement inventées selon Codex, pas du PokeMind personnel ni du binaire gelé.** Aucune capture propriétaire n'a été enregistrée/versée dans GitHub par ChatGPT.

## Rapport d'exécution Codex — non reproduit par ChatGPT

- `python scripts/local_gate.py --keep` en copie isolée : **1 885 réussis, 3 ignorés, 0 échec** (Qt 191 ; cœur 1 694) selon RESULT.
- Qt natif Windows 6.12.0 : **35 tests passés à facteur 100 % et 35 à 125 %**, selon Codex; matrice sombre/clair, FR/EN, 1100/1500 px avec dock ouvert/fermé. Les tests comparent les vrais pixels du préfixe sélecteur, mesurent les colonnes sans scroll horizontal, KPI, repli clavier/copier/défilement; nouvelles fixtures inventées.
- Périmètre local : aucune lecture des vrais decks/journaux, aucun accès aux archives utilisateur, aucune construction de Setup/EXE, aucune installation, migration, changement de consentement, publication ou tag selon Codex. ChatGPT ne peut attester l'intégrité des données Windows via une lecture GitHub.

## Limites et décision

1. L'installation Windows réelle **reste candidat 015, version 0.9.5, source `7cede884`**; le source 016 `66a1ce0` ne s'y trouve PAS encore. Même 0.9.5 après reconstruction ne déclenchera pas forcément un bouton de mise à jour 1-clic.
2. L'audit source + captures synthétiques est **favorable**, mais le propriétaire doit voir le nouveau classement/statistiques dans **son propre PokeMind installé** avant acceptation finale. Une dernière réception de la reconstruction adverse doit rester fondée sur un journal réellement admissible; l'absence de création avec preuves/sources publiques insuffisantes reste un comportement normal.
3. **Ne pas lancer d'autre tâche de développement; ne pas inventer de nouveau défaut ni modifier les statistiques/algorithmes.** Une SEULE prochaine décision propriétaire : **GO explicite pour reconstruire le candidat Windows 0.9.5 avec la source 016, QA isolée complète, sauvegarde intégrale vérifiée et copie ancien programme, puis une seule installation conditionnelle au même AppId**, suivie de sa réception GUI manuelle. Le mandat sera écrit dans `NEXT_PROMPT.md` seulement si GO; l'autorisation de 015 est consommée et ne se renouvelle pas.
4. **Aucun GO public** : tag/release/export vers dépôt public interdits jusqu'à réception réelle, puis nouvelle autorisation distincte. Conserver archives, ancien programme et `synthetic_v2.*` intacts; aucune réinstallation, sauvegarde ou mutation maintenant.

**État : `016_SOURCE_AUDIT_PASSED / 015_INSTALLED_UNCHANGED / OWNER_GUI_NOT_ACCEPTED / PUBLICATION_FORBIDDEN`.**
