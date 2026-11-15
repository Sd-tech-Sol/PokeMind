# Audit indépendant ChatGPT — PM-DECKLAB-PUBLIC-STATS-001 / D-291
Date : 2026-11-07. Branche privée : `work/pm-v1-lotj-final-readiness-windows`.
Code : `3a56023e1d17d73760497813f813c263c40a743e`. Rapport exécuteur : `06e3e5c3e6ea8a4fb829c4ff827e0a8f26734cdf`.

## Portée et verdict
**VERIFIED_SOURCE / IMPLEMENTED — AWAITING_REAL_SOURCE_AND_WINDOWS_VALIDATION.** Relecture indépendante via GitHub des changements et sources (`deck_public_stats.py`, `window.py`, tests synthétiques et `RESULT.md`). **Ni suite Python ni Windows ni API Limitless réelles rejouées par ChatGPT.** Le comportement annoncé par Claude est étayé par le code et les fixtures, mais n'est pas un feu vert d'installation/publication.

## Confirmations indépendantes
- UI : un troisième onglet `Statistiques` est intégré dans `Deck Lab`, alimenté par les mêmes sélections de decks. Une clé d'identité et un jeton empêchent un vieux résultat de remplacer les chiffres d'un autre deck.
- Source : `batch_public_research.research_matchups` et `meta.meta_archetypes/meta_matchups/meta_tournaments` existants; aucune nouvelle API ni dépendance. Le nouveau module agrège des instantanés PUBLIC validés. BO1 et BO3 sont distincts; seuils 20 placements, 20 matchs globalement, 10 par matchup; intervalle de Wilson.
- Définition du dénominateur : taux = victoires / (victoires + défaites + nuls) de **matchs admissibles**, non des parties. Miroirs exclus. Attribution de l'archétype fondée sur les Pokémon du deck et non son nom; ambiguïté → aucun taux pour le deck.
- Cache : garde `deck-public-stats.json`, une tentative automatique quotidienne, au plus deux actualisations manuelles avec délai d'au moins 600 secondes; refus réseau étiqueté et dernier instantané conservé.
- Vie privée : appel du collecteur indépendant des noms et listes privées; identification via catalogue public et deck local; tests de non-exfiltration sur serveur HTTP synthétique.
- Tests : `tests/test_deck_public_stats.py` utilise un oracle distinct sur fixtures pour comparer V/D/N et dénominateurs. Les parcours Qt ciblent ouverture, changement de sélection, cache, refus et langue.

## Réserves factuelles
1. **La porte complète VERTE a précédé une modification de fixture.** Après retrait d'un prénom d'une chaîne de test, uniquement les 12 tests ciblés ont été relancés. La porte complète sur l'arbre final exact de `3a56023` **n'est donc pas démontrée**. Cela ne prouve pas un bogue, mais empêche de déclarer la porte finale VERIFIED.
2. **Aucune requête Limitless réelle** au commit livré. Le contrat/format réel, les filtres actuels et la disponibilité d'archétypes restent à contrôler avec un test réseau public borné, sans donnée personnelle et sans contournement de quotas. Les résultats synthétiques prouvent la logique attendue, pas la disponibilité de chiffres aujourd'hui.
3. Le collecteur courant ne prend qu'un tournoi par campagne; il peut revisiter le même tournoi chaque jour : échantillon petit et stats souvent insuffisantes. **Ne jamais afficher « taux mondial », « stats des 60 cartes exactes » ou chiffre sans n/source.**
4. **Robustesse future à surveiller** : `_snapshots` ignore entièrement un ancien fichier si **un** ID de tournoi chevauche un fichier plus récent. Avec la collecte actuelle d'un tournoi/campagne, ce n'est pas un défaut observable, mais si plusieurs tournois sont ajoutés à une même campagne ce mécanisme peut perdre des tournois disjoints. Corriger uniquement si un cas réel ou un test le reproduit; sinon garder comme limite.
5. Le nom d'archétype non basé sur les Pokémon (« Box », « Control ») demeure non identifié. C'est volontaire et moins dangereux que d'attribuer des chiffres inexacts.
6. Deux exécutions de tests directement dans le dépôt ont contrevenu à `AGENTS.md`, signalées par l'exécuteur; aucune preuve d'atteinte aux données personnelles. Respect impératif de l'isolation pour la suite.
7. La 0.9.4 candidate demeure distincte; aucun build/install/publication 0.9.5, aucune validation visuelle sur PC du propriétaire.

## Une prochaine action recommandée
**PM-DECKLAB-STATS-REALITY-GATE-001** (Claude Code, une seule tâche) : synchroniser la branche privée; relancer la porte complète sur l'arbre final sous isolation; effectuer une consultation publique réelle, bornée et sans données privées, de l'API Limitless via le client existant, vérifier disponibilité/structure/date/filtres/quotas et examiner le rendu offline ensuite, sans inventer de stats si l'échantillon n'atteint pas les seuils. Documenter le résultat et éventuellement corriger un bogue prouvé, sans changer la version, construire, installer ni publier. STOP puis audit ChatGPT.
