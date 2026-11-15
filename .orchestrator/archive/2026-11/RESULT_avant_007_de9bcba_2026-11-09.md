# RESULT — PM-UI-DECKLAB-REAL-GALLERY-006 — AWAITING_AUDIT (2026-11-09)

**Galerie réelle intégrée dans le code privé; STOP pour audit indépendant ChatGPT.**
Base `a661bd74f86d005209d0bb6c3a06c9951599310c`, code `d6efdd2ddbd2b804e1fc1689dfaa243567640005`,
branche `work/pm-v1-lotj-final-readiness-windows`, dépôt privé `Sd-tech-Sol/PokeMind-dev`.
GO explicite propriétaire et D-300. [Résultat précédent archivé](archive/2026-11/RESULT_avant_PM-UI-DECKLAB-REAL-GALLERY-006_a661bd7_2026-11-09.md).

## Changement réel et comparaison

`DeckGallery` conserve les sections et quantités, avec des colonnes calculées sur le **viewport central** :
3 si au moins 814 px, 2 à partir de 428 px, sinon 1. Largeur identique dans toutes les catégories,
plafond 320 px par tuile, rang incomplet conservé sans remplissage. Reflow aussi lorsque la largeur change
sans changer le nombre de colonnes; scroll conservé lors d'un petit redimensionnement.

`CardTile(gallery=True)` réserve une hauteur d'art proportionnelle et le texte replié; nom 17 px,
impression conservée à 14 px, titres de catégorie 16 px repliables. `CardArt` conserve le ratio réel de chaque image,
les quatre coins, son unique animation 220 ms et ses bornes fixes. Insets réduits sans rogner l'image;
fallback complet replié, Espace/Entrée ouvrent le zoom existant avec sa provenance. Surface sélectionnée
unie et contour BrainBall (or sombre, bleu clair, tokens existants); hover distinct. Aucun nouveau moteur.

Mesures **logiques Windows natif à 125 %**, même fixture de 20 références / 60 cartes, même fenêtre,
mêmes contrôles réellement actifs; comparaison au code de base, avec le même harnais synthétique :

| Fenêtre / viewport | Colonnes avant → après | Tuile avant → après | Image avant → après |
|---|---|---|---|
| 1500×970 / 852×513 | 4 → **3** | 193×377 → 262×466 | 141×197 → **224×314** (+59 % en largeur) |
| 1100×900 / 453×443 | 2 → **2** | 203×377 → 202×424 | 147×206 → **164×230** (+12 % en largeur) |

Défilement horizontal **0** dans toute la matrice; repli à 1 colonne aussi exercé dans la vraie fenêtre
avec une galerie de 330 px. La taille accrue demande davantage de scroll vertical : maximum 2016→3532
à 1500, 3658→4146 à 1100 pour ce jeu de données. Le viewport n'est pas agrandi : commandes et Coach réels
conservés. Par rapport à 005 (~213 px d'art), le produit atteint ~224 px en grand format mais seulement
164 px en étroit : menu 224 px, vrai dock et commandes prennent plus de place. Aucun bandeau, faux Coach,
détails ou art de démo porté. Le rang initial peut demander un scroll pour lire toute l'impression.

## Preuves locales reproductibles, hors Git

`python scripts/qa_real_decklab_gallery.py --label after --scale 1.25` copie les sources sans données
personnelles et exécute les vrais tests de `MainWindow`, avec services/image I/O inventés et vrais jobs Qt.
Échelle 1 aussi disponible. `QT_SCALE_FACTOR=1.25` testé en backend Windows natif; aucun réglage DPI Windows modifié. Baseline : ajouter `--label before --baseline-ref a661bd7`.

- `build/qa-real-decklab-gallery/after-1.25/gallery-1500-dark-fr-14.png` : client complet réel,
  1875×1213 pixels pour 1500×970 logiques; fichier 1100 analogue : 1375×1125 pour 1100×900.
  Captures claires EN, textes 18 px, dernière carte/fallback et zoom disponibles dans le même dossier.
  Captures principales, fallback étroit et zoom inspectés par Codex; aucun bureau personnel capturé.
- `after-1.25/hover.mp4` : H.264, 24 frames / 20 i/s / 1,2 s, 1876×1214 (1 px ajouté à droite/en bas
  pour l'encodage pair), sans audio. `hover.gif` : 1875×1213, 8 frames après fusion des doublons, 1,2 s.
  Toutes les frames décodées; GIF aussi chargé intégralement par Pillow. Vrais événements et horloge
  d'animation Qt échantillonnée, hover puis sélection, pas une mesure de cadence physique.
- `before-1.25/`, `after-1/`, mesures JSON, `verification.json`, logs et sources isolées : ignorés.
  Images uniquement géométriques à quatre coins, aucune illustration TCG ou personnelle collectée.

## Vérifications et limites

- Prévol `RUNTIME_READY`, base propriétaire non ouverte, aucune écriture/réseau du prévol.
- **16/16 ciblés finaux Windows natif à 125 %**, thèmes sombre/clair, FR/EN, labels par défaut et 18 px.
  **16/16 Windows natif à 100 %**. Offscreen **16/16**, inclus dans la passe complète finale.
- Focus Tab, sélection unique, Espace/Entrée/Entrée pavé numérique et provenance du vrai zoom;
  coins colorés visibles au hover sans déplacement; pas de fetch sur scroll/hover; reduced motion,
  masquage, fermeture, repopulation et destruction des anciennes tuiles/animations.
- Vrais workers retardés `gallery_cards` et `images.fetch`, changement A→B : token/generation empêchent
  tout résultat A de remplacer B ou d'appeler une ancienne tuile détruite. Pipeline production inchangé.
- Vraie copie (presse-papiers remplacé en test pour ne pas lire/modifier celui du PC), export fichier
  synthétique et refus d'écrasement, vrai parseur/comparateur (60 copies communes), favoris et deck
  principal persistés en root inventé, onglet texte intact et consentement cloud toujours faux.
- Contraste calculé sur **22 paires effectivement utilisées** : minimum **5,35:1** pour les textes;
  palette inchangée, pas une certification des pixels d'images. Sélection claire bleue pour son contraste.
- Première tentative de porte interrompue après **9 échecs Qt / 129 réussis** : assertions qui supposaient
  les métriques natives en offscreen, puis un titre non replié. Corrections ciblées; une passe intermédiaire (138 Qt verts) a aussi été interrompue pour conserver
  l’impression à 14 px plutôt que 13 px. Ces tentatives ne
  valent pas preuve complète. Le backend offscreen Windows utilise des fontes de repli et une autre largeur
  de dock; contrat 3/2 vérifié sur Windows natif, repli/alignement/absence d'overflow vérifiés sur les deux.
- Porte complète isolée `python scripts/local_gate.py --keep` : **VERTE, 138 Qt + 1654 cœur = 1792 réussis,
  3 ignorés, zéro échec, sortie 0**. Compilation/hygiène vertes; Qt 74 s, cœur 520 s. Sources UI/tests/harnais
  identiques à la copie vérifiée; aucun pytest dans le dépôt de travail.

`window.py`, services, catalogue et correctif UTC/local `00eecb3`, ImageCache, consentements, statistiques,
Coach et historique ne sont pas modifiés. La suite Qt complète exerce leurs parcours existants; aucun
réseau Limitless/TCGdex réel ni moteur IA réel invoqué. Limite préexistante visible : certains boutons de
la rangée du sélecteur FR sont tronqués à 1100/125 %; cette rangée est hors galerie et n'a pas été refaite.

## Git privé et arrêt

Fast-forward `fc7468e`→`a661bd7`, arbre initial propre; correctifs `00eecb3` et prototype `4e40ec6` présents.
Diff limité à trois modules UI existants, tests Qt, harnais QA manuel et orchestration assainie.
Aucun accès/écriture aux données ou sauvegardes propriétaires, aucune dépendance ajoutée, installation,
setup, version, tag ou publication. Hotfix 0.9.5 installé et public 0.9.3 conservés sans intervention.
GitHub au SHA code : **0 statut, 0 check, 0 run**; agrégat `pending` sans statuts, donc **NO_GITHUB_STATUS**, aucune CI verte revendiquée. HEAD privé distant confirmé au SHA code après push. Un commit de code et un seul commit de rapport assaini. Contrôle du HEAD distant et de l’état Git après le push final communiqué au propriétaire dans la session.

**AWAITING_AUDIT / NOT_RELEASE_READY. STOP ChatGPT au SHA exact** et réception visuelle du propriétaire.
Aucune tranche suivante ni installation/publication déduite de ce lot.
