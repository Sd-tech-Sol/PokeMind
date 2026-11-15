# Deck Lab — classement et statistiques, QA 016

Mandat source seulement, base privée `ab31142`. Aucune installation ni lecture des données,
decks ou sauvegardes du propriétaire. Toutes les entrées, statistiques et captures ci-dessous
sont **inventées**. Le candidat 015 installé n'est pas modifié.

## Présentation

- Le worker `Services.rank_decks` reste inchangé : PUBLIC PTCGL Standard BO1, n≥20,
  taux connus décroissants, égalités stables, inconnus après. Aucun nouveau calcul, collecteur
  ou appel par ligne. BO3 ne participe pas à ce classement.
- Le sélecteur fermé/ouvert commence par `#rang · taux · nom`. Pour un inconnu,
  `— · Données insuffisantes · nom` évite de cacher l'incertitude derrière le nom long.
  Le glyphe du deck principal vient après ce préfixe. Nom complet, n, population, période,
  source et snapshot restent dans les tooltips et descriptions accessibles.
- Onglet Classement ajouté en position 3, après Galerie/Liste texte/Statistiques : toutes
  les entrées, colonnes rang/deck/taux PUBLIC BO1/n, inconnus sans rang/taux/n fictif.
  Sélection souris/clavier reliée au même sélecteur, aucune écriture par cette vue.
  La sélection, les favoris, le deck principal, la comparaison et le scroll de galerie
  survivent au reclassement par clé existante.
- Statistiques : taux public en grand, mode et n explicites, période/Limitless/snapshot,
  identité ambiguë et erreur visibles. La valeur décimale formate le `win_fraction`
  existant; le résumé détaillé conserve son ancien arrondi entier, ses compteurs et IC.
  Aucune formule de winrate ni intervalle n'est recalculé dans l'interface.
- Les barres passent toujours par `project_public_stats`, mêmes données et limite de huit
  lignes. Matchups : légende courte V/D/N. Méta : placements; Évolution : parts par tournoi.
  Les populations et chiffres de placement ne deviennent pas des résultats personnels.
- Sources et détails : contrôle Qt natif, fermé par défaut/réinitialisé au changement
  de vue, utilisable au clavier. Résumés intégraux, miroirs/exclusions, seuils, IC, source,
  dates/URL/docs et avertissement public/personnel restent sélectionnables/copiables.
  Une erreur de rafraîchissement reste visible, y compris après changement de thème.

## Preuves synthétiques

Trois régressions avant correction : taux après nom long, classement absent, panneau
sans repli/KPI. Les suites du moteur existantes couvrent BO3 seul, n<20, ambiguïté,
vieux/futurs snapshots et oracle des pairings; leurs calculs n'ont pas été changés.

Fixture de présentation : cinq decks, noms >100 caractères, 57/117 → 48,7 %, second
42,0 %/100, trois inconnus. Tests du menu réel fermé/ouvert par comparaison des pixels
du préfixe long avec sa référence courte; largeur des quatre colonnes, n visible, taille
du KPI, non-chevauchement et absence de scroll horizontal. Tests de souris/flèches,
favori/principal/comparaison, nouveau classement, égalités, tout inconnu et liste vide.
BO1/BO3 séparés, faibles échantillons, source indisponible, repli, vraie copie Ctrl+A/C,
défilement des détails et sélection inconnue sans « 0 % » inventé.

Matrice native : sombre/clair × FR/EN × (1100/Coach ouvert, 1500/Coach ouvert,
1500/Coach fermé), facteurs Qt 1 puis 1.25, runtime Qt 6.12.0. Captures `QWidget.grab()`
du vrai MainWindow synthétique; animations laissées finir, aucun pixel retouché.
Ce ne sont pas des captures du bureau ni de l'EXE personnel. Les PNG offscreen de la
porte locale ne sont pas les preuves typographiques Windows.

Échantillon de livraison : [classement sombre 125 %](qa/decklab-016/ranking-dark-125.png),
[classement clair EN 100 %](qa/decklab-016/ranking-light-en-100.png),
[menu ouvert 125 %](qa/decklab-016/popup-dark-125.png),
[KPI 125 %](qa/decklab-016/statistics-dark-125.png),
[graphique/légende/repli](qa/decklab-016/chart-light-en-125.png),
[détails et copie](qa/decklab-016/details-light-en-125.png),
[inconnu et échec visible](qa/decklab-016/unknown-light-en-125.png).

Preuve complète et comptes finaux : [.orchestrator/RESULT.md](../.orchestrator/RESULT.md).
Exécuter uniquement `python scripts/local_gate.py --keep` depuis le dépôt pour la porte;
les parcours natifs se rejouent dans sa copie isolée avec `POKEMIND_TEST_OFFLINE=1`,
`QT_QPA_PLATFORM=windows`, `QT_SCALE_FACTOR=1` puis `1.25`, filtre `016 or deck_controls`.
Audit indépendant et nouveau GO requis avant tout candidat EXE/Setup ou installation.
