# AUDIT INDÉPENDANT CHATGPT — PM-V1-POKEDEX-EXPERIENCE-STATS-001

**2026-10-28 Québec · AUDITED_STATIC_UX_STATS_IMPLEMENTED_OWNER_REAL_EXE_RECEPTION_PENDING_CI_AWAITING_EVIDENCE.**
**V1 NOT_RELEASE_READY · CI AWAITING_EVIDENCE · réception du propriétaire NON EFFECTUÉE.**

## Périmètre du dépôt vérifié

- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`.
- Baseline du mandat `9e0435bff4abda5597ec2233f7458ce30838c175`, implémentation principale `ad064dcd62dfaf6ec852e90862353993d12bbd1c`, source finale du build `e8f9849c5fad71d1de70e30dadccf78d54d91ef7`, HEAD des preuves et états `0cc7033b30fe4f465a261e6834187582c3298a0b`.
- Comparaison GitHub **ahead=3, behind=0**, **20 chemins changés**. Modules nouveaux `desktop/charts.py`, `desktop/insights.py`, `desktop/card_art.py`; intégration `desktop/window.py`, `desktop/widgets.py`, `desktop/theme.py`, préférences `assistant/sessions.py`; banc `tests/test_desktop_insights.py`, `tests/test_desktop_qt.py`, `tests/conftest.py`, `scripts/run_synthetic_qa.py`, guide et `.orchestrator`. Aucun moteur de calcul de combats, collecte réelle ou migration DB modifié dans le diff examiné.
- Fichiers inspectés directement via connecteur GitHub : `insights.py` complet, `charts.py` complet, `card_art.py`, `sessions.py`, `tests/test_desktop_insights.py`, `tests/conftest.py`, `EVIDENCE_PM-V1-POKEDEX-EXPERIENCE-STATS-001.md`, RESULT/STATE/NEXT_ACTION, diff de la correction finale de `window.py` et points d'intégration retrouvés dans `window.py`.
- Ce cycle de ChatGPT n'a ouvert **aucune donnée personnelle, aucun EXE Windows et aucun fichier local**.

## Lecture indépendante du code / réserves

1. **Quatre vues implémentées** : `StatisticsPanel` offre les onglets *Bilan*, *Adversaires*, *Tours*, *Actions*, un filtre `all/wins/losses/unknown` pour les vues détaillées; `CountChart` dessine des barres natives, infobulles, focus et sélection au clic ou clavier d'une famille pour naviguer vers les Combats. Ce sont des **effectifs** et non des probabilités inventées.
2. **Honnêteté statistique** : `project_statistics()` lit le rapport déjà fourni, préserve `coverage.valid` et les totaux d'`outcomes`, et affiche séparément `details_n` issu des seules traces disponibles. Le « dernier tour observé » n'est pas la durée de partie, les prises de Récompenses sont des *occurrences*, et les statuts/dates inconnus restent inconnus. `recent_matches()` ne qualifie de récents les matchs que si **toutes les dates requises sont valides**; sinon « ordre du rapport · chronologie non attestée ». `timeline_html()` échappe le texte issu des traces. Pas d'apprentissage de cartes non observées ni de taux global imputé par ces projections.
3. **Cinq évolutions UX** : `card_art.py` compose sur des images déjà disponibles avec reflet/zoom; `window.py` dispose des contrôles pour favoris, accueil, historique, un seul chat en bulles, volet de sources repliable, navigation à six icônes avec barre latérale repliable. Les sources et le moteur IA existants ne sont pas remplacés dans ce diff. Les effets restent soumis à la réduction de mouvement.
4. **Préférences/UI** : `sessions.py` fusionne `favorite_decks=[]` et `sidebar_collapsed=false` aux anciennes préférences via `DEFAULTS | value`, valide les identifiants de favoris comme hex SHA-256 uniques, limite leur nombre et conserve les anciens réglages. Les favoris sont l'empreinte d'un export de référence, **pas une attestation d'une version de deck réellement jouée**. Le choix de favoris/repli en utilisation réelle pourra écrire une préférence UI dans le dossier local, ce qui ne contredit pas l'absence de lecture ou écriture personnelle **par Codex pendant le mandat**.
5. **Banc de tests présent** : `test_desktop_insights.py` couvre totaux vs détails, inconnues, chronologie, texte HTML échappé, favoris, navigation, bulles/sources, zoom et réduction des mouvements; `conftest.py` réutilise une session Qt commune. Cela confirme la **présence** des cas, mais **pas leur exécution** par l'auditeur.
6. **Réserve** : le résumé ne qualifie ni l'exactitude des 66 matchs privés, ni tous les événements du jeu, ni les performances/ergonomie sur le PC du propriétaire. Les 4 vues reflètent les seules données que le rapport contient. Les graphes peuvent être partiels; aucune donnée manquante n'a été inventée pour combler la couverture.
7. **Aucun défaut bloquant confirmé par cet audit statique ciblé**. Cette conclusion n'est pas une certification de produit, un audit de sécurité Windows ou une acceptation utilisateur.

## Vérifications locales — CODEX_LOCAL_REPORTED uniquement

Rapport Codex du [fichier de preuves](EVIDENCE_PM-V1-POKEDEX-EXPERIENCE-STATS-001.md) :
- **84 tests distincts passés**, 0 échec final/erreur/skip, dont **18 nouveaux** (les 66 de la suite antérieure sont inclus et ne s'additionnent pas). Deux passes intermédiaires 83/1 ont été attribuées à plusieurs `QApplication` durant un même processus; fixture de session corrigée, résultat final 84/84 rapporté.
- Inspection visuelle native, sombre/claire et petite fenêtre; échantillon *inventé* n=6 avec 2 victoires, 3 défaites, 1 inconnue, et 18 occurrences d'événements. Aucune statistique personnelle calculée dans ce mandat.
- Build PyInstaller **de production** en staging neuf, smoke du vrai frozen Windows **exit0 sur fixture indépendante**. Sept modules finaux déclarés identiques au code embarqué. Le smoke du binaire ne démontre **pas** tous les clics des parcours UX dans ce binaire.
- Codex rapporte la distribution complète installée au même **`dist/PokeMind/PokeMind.exe`**, 788 nouveaux fichiers concordants, ancien dossier 788 fichiers conservé et versions antérieures retenues sans suppression. ChatGPT ne peut pas vérifier ces fichiers locaux dans GitHub.
- Aucun accès/inventaire personnel, aucune migration, suppression, backup DB ni import, aucun GET de source réel ni fournisseur réel sollicité dans cette tâche, selon l'exécuteur. Les gardes Python ne sont **pas** une sandbox OS; ni l'absence absolue de trafic réseau, ni l'immutabilité complète des données privées ne sont certifiées.
- **Le compte de matchs personnels n'a pas été recalculé.** La valeur précédente « 66 » provenait d'un mandat antérieur; ni 84 tests ni les n=6 fictifs ne doivent être présentés comme son nouvel historique vérifié.

## GitHub Actions vérifié au SHA exact

- [Run 40630273076](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40630273076) associé au HEAD `0cc7033b30fe4f465a261e6834187582c3298a0b` : `completed/failure`.
- Windows job `122624781688` : **0 étape**; Ubuntu job `122624781880` : **0 étape**. Contrôle indépendant via `fetch_workflow_job_steps`; **aucun test CI n'a tourné**.
- Cause budget Actions rapportée par Codex, non réauditée via annotations financières. Reste **CI AWAITING_EVIDENCE**. Le prochain commit documentaire d'audit crée sa propre CI; elle doit être lue séparément.

## Verdict et prochaine action

**AUDITED_STATIC_UX_STATS_IMPLEMENTED_OWNER_REAL_EXE_RECEPTION_PENDING_CI_AWAITING_EVIDENCE.**

Le code versionné et le rapport correspondent au mandat, avec des limites statistiques explicites et aucune dérive manifeste du périmètre dans les fichiers examinés. Les 84 tests et la mise à jour du binaire sont **locaux, rapportés par Codex, non reproduits par ChatGPT**.

**Ne créer aucun nouveau mandat Codex de QA fictive ou de mise à jour EXE.** Le propriétaire peut ouvrir le **même programme réel** `dist/PokeMind/PokeMind.exe` : vérifier les quatre vues, filtres et clics, quelques favoris, menu repliable, chat en bulles et historique réel. Vérifier le compteur attendu de **66 matchs** sans effectuer d'import ni migration. Si l'historique manque ou des graphiques affichent une conclusion trompeuse, décrire l'écart et ne pas le corriger par un réimport automatique. Une approbation visuelle n'entraîne pas V1 RELEASE_READY. `execute_now=false`.
