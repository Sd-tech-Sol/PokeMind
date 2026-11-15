# Deck Lab — étude interactive privée

Une fenêtre **PySide6 native**, six illustrations fictives originales dessinées avec QPainter,
sélection, survol, onglets et détails animés. Aucune intégration à PokeMind, base, compte,
requête réseau ou écriture à l'ouverture. Aucune dépendance à installer pour cette session.
Les cartes et la composition sont imaginaires, sans légalité Pokémon TCG ni résultat de partie.

Depuis la racine du dépôt sur Windows :

```powershell
python demos/premium_decklab/demo.py
```

Survole une carte, clique pour la sélectionner; Tab/Espace fonctionnent aussi. Essaie les trois
onglets, **Voir les effets** et **Réduire les animations**. Les autres rubriques de la barre
latérale servent uniquement de contexte visuel. Fermer la fenêtre arrête les animations/timers.

Pour recréer les preuves depuis la vraie fenêtre Qt :

```powershell
python demos/premium_decklab/record_preview.py
Start-Process .\build\qa-premium-decklab-demo\preview.mp4
# Ou ouvrir preview.gif dans un navigateur/lecteur d'images qui anime les GIF.
```

Le script échantillonne 120 images de l'UI Qt en 6 secondes à 20 i/s : véritable
`enterEvent`, sélection, animation des détails et changement d'onglet. L'horloge Qt est pilotée
pour rendre l'enregistrement reproductible; aucun diaporama de maquettes. Le petit curseur
circulaire est ajouté à l'enregistrement pour montrer la cible. Rien ne capture le bureau.
FFmpeg déjà disponible crée MP4 + GIF; sans FFmpeg, Pillow déjà disponible peut créer le GIF.
Si les deux manquent, le script échoue explicitement et n'installe rien.

Sorties locales ignorées par Git : `build/qa-premium-decklab-demo/preview.gif`, `preview.mp4`,
`decklab-complete.png`, `decklab-1100.png`, six `art-*.png`, les frames et `recording.json`.
Les fichiers sources ici sont reproductibles hors ligne; aucune image propriétaire n'est incluse.

Art et code originaux : contributeurs PokeMind, 2026, licence MIT du dépôt.
Palette et emblème BrainBall existants autorisés réutilisés; aucune illustration de carte TCG téléchargée.
Une validation esthétique appartient au propriétaire. Cette démo n'est ni installée ni publiée.
# Prototype visuel actuel — finition 005 de la direction approuvée

Depuis la racine du dépôt, dans PowerShell :

```powershell
python demos/premium_decklab/reference.py
python demos/premium_decklab/reference_preview.py
Start-Process .\build\qa-decklab-finish\preview.mp4
Start-Process .\build\qa-decklab-finish\decklab-full.png
```

Le deuxième script capture uniquement ses propres QWidget synthétiques dans `build/qa-decklab-finish/` : PNG 1500×970,
contrôle étroit 1100×900, film MP4 et GIF de six secondes. Les fichiers restent ignorés par Git.
Survol 220 ms, clic ou Tab/Espace, panneau de sélection et trois onglets réels; mouvement réduit.
Les paramètres DPI de Windows ne sont pas changés; les dimensions de capture suivent le DPR Qt courant.

`reference.py` est une adaptation de présentation, **pas MainWindow en production**. Son constructeur
initialise Store/Services, historique et tâches; l'isolation minimale évite ces chemins entièrement.
Navigation et ordre exacts des sept pages, trois onglets Deck Lab, sélecteur de deck et dock Qt à droite
de 355 px viennent de `window.py` (`__init__`, `_decks`, `_chat`). Les commandes hors aperçu sont
visiblement désactivées. ChatInput, CardArt via DemoCard, AnimatedStack, palette, logo et icônes sont réutilisés.
Le dock reste fixe pour cette étude. Aucun compte, modèle, DB, cache de cartes, Services ou Store créé.

La [référence originale](../../docs/design/pokemind-brainball/references/decklab-premium-target.png)
guide l'ambiance et les proportions; ses cartes, simulateur, optimisation, taux et recommandations inventés
ne deviennent pas des fonctions. La galerie montre six illustrations originales distinctes dans une grille
équilibrée de trois colonnes à 1500 px et deux à 1100 px, avec défilement vertical. Aucun téléchargement.
Les cartes sont peintes à environ 213 px de largeur (contre 144 px en 003), avec titres 17 px et sous-textes
13 px. Les pochettes suivent le principe de hauteur réservée du vrai CardTile pour les textes repliés.
Le bandeau peint une composition panoramique originale en mémoire une seule fois (QPixmap), à partir de
la créature existante, avec lumière cyan/or et bordure fine. Le panneau de sélection se replie sous un bouton nommé selon la carte choisie (clic ou Tab/Espace); le Coach
est consacré à la discussion, sans fausse réponse IA. Accent or de sélection distinct du survol bleu.

Le Coach garde son vrai vocabulaire de commandes désactivées, avec titre, état hors ligne, accueil typographique
et trois panneaux explicatifs. Ce sont des indications d'utilisation, aucune réponse ni recommandation IA.
Le survol et la sélection ne déplacent pas les voisins. Aucun timer permanent ni effet graphique lourd.
Les captures précédentes restent dans `build/qa-decklab-reference/` (003) et `build/qa-decklab-polish/` (004). Aucune image QA versionnée.

Écarts visuels assumés : art géométrique original plutôt que cartes Pokémon détaillées; seulement six images;
défilement vertical pour voir le bas des rangées; identité réellement fournie par PokeMind plutôt que logo
redessiné de la maquette; pas de barre de navigation horizontale dupliquée, graphiques d'impact, filtre de carte
ou nouveaux onglets. Lueurs modérées et texte conforme aux tokens de contraste. Mode sombre FR-CA seulement.
La sélection est un panneau synthétique, pas une modification de galerie intégrée. L'acceptation esthétique
appartient au propriétaire après visionnement; aucune installation/publication n'est autorisée.

---

Finition 005 : silhouette du dragon entière dans une zone sûre à droite, sans étirement ni contrôles
superposés; sélecteur sous le bandeau. La galerie gagne 37 px de hauteur aux deux tailles par rapport
à 004 (DPR 1 et 1,25), cartes toujours ~213 px. Les détails sont fermés au départ et le restent après
une sélection; ouvrir le bouton affiche la carte choisie, le refermer restitue exactement le viewport.
Le film montre aussi cette ouverture/fermeture. L'état vide Coach est réparti entre les contrôles et la
saisie, avec trois courts panneaux dont la hauteur réserve le texte replié. Pas de discussion simulée.
Labels secondaires 12–13 px; contrôle des titres 20 px, sous-titres 16 px et descriptions Coach 15 px
aux deux largeurs, offscreen et Windows natif à 125 %. Aucun réglage Windows changé.
