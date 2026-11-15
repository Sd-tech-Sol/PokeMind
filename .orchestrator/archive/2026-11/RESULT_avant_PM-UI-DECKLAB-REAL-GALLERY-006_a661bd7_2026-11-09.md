# RESULT — PM-UI-DECKLAB-FINAL-VISUAL-FINISH-005 — AWAITING_AUDIT (2026-11-09)

**Finition du prototype isolé; direction 004 conservée. STOP audit ChatGPT et réception visuelle propriétaire.**
Base synchronisée `7639260226845e87c3e59d48843b392f1862f998`, code `4e40ec6a30e87a1fe333222b13700a6c36852513`, branche privée
`work/pm-v1-lotj-final-readiness-windows`. GO explicite propriétaire; [mandat archivé](archive/2026-11/NEXT_PROMPT_avant_PM-UI-DECKLAB-FINAL-VISUAL-FINISH-005_7639260_2026-11-09.md).
[Résultat 004 préservé](archive/2026-11/RESULT_avant_PM-UI-DECKLAB-FINAL-VISUAL-FINISH-005_7639260_2026-11-09.md).

## Voir le résultat local

```powershell
python demos/premium_decklab/reference.py
Start-Process .\build\qa-decklab-finish\decklab-full.png
Start-Process .\build\qa-decklab-finish\preview.mp4
```

Reproduction : `python demos/premium_decklab/reference_preview.py` (QWidget synthétique, aucun bureau capturé).
Capture entière 1500×970, contrôle 1100×900, MP4 et GIF dans `build/qa-decklab-finish/`, ignorés par Git.
Aperçus 004 préservés dans `build/qa-decklab-polish/`; PNG conceptuel versionné intact.

## Comparaison mesurée à fenêtre identique

| Critère | Prototype 004 | Finition 005 |
|---|---|---|
| Dragon du bandeau | Tête/ailes/corps partiellement coupés, sélecteur superposé | Silhouette entière, rapport largeur/hauteur préservé, zone sûre à droite, aucun texte superposé |
| Hauteur bandeau, DPR 1 | 149 px | 99 px; sélecteur placé dessous |
| Viewport galerie 1500×970, DPR 1 | 590 px | **627 px (+37; +6,3 %)** |
| Viewport galerie 1100×900, DPR 1 | 520 px | **557 px (+37; +7,1 %)** |
| Viewport galerie, Qt 125 %, grand / étroit | 588 / 518 px | **625 / 555 px (+37)** |
| Détails sélection | 64 px permanents | Bouton 32 px nommé selon la carte; panneau de 80 px seulement à la demande |
| Cartes / grille | ~213 px, 3×2 / 2×3 | Identiques; défilement horizontal 0 aux deux tailles |
| Sous-titres / commandes secondaires | 10–12 px selon label | 12–13 px; titres des cartes toujours 17 px |
| Coach sans discussion | Accueil haut et espace central vide | Accueil et trois panneaux courts répartis entre contrôles et saisie; hauteur des panneaux réservée au texte replié |

La source du dragon a été rendue en entier pour vérifier le crop : tous ses pixels visibles sont dans
le sprite conservé. Sprite dessiné en proportions exactes, marge verticale 7 px, sans recouvrement par
les labels à 1500 et 1100, DPR 1 et 1,25. Panorama et sprite calculés une fois en mémoire.
La créature entière est maintenant plus petite (~95×85 px à DPR 1); compromis explicite pour conserver
le bandeau compact et dégager la galerie. Aucun nouvel art ou nouvelle direction graphique.

Sélection visible sur la carte et le bouton, clic et clavier Tab/Espace fonctionnels. Le bouton ouvre/referme
les vrais détails Qt; la sélection reste synchronisée lorsque le panneau est fermé. Ouverture : viewport
539 / 469 px à DPR 1; fermeture : retour exact à 627 / 557 px, sans déplacement de scroll. Focus du bouton
à hauteur fixe : aucun décalage de grille. Défilement vertical unique pour les cartes, dernière rangée accessible.
Le Coach garde ses contrôles désactivés et son transcript Qt, sans discussion, résultat ou connexion simulés.

## Preuves visuelles et validation

- `decklab-full.png` : **1500×970**, 436 878 octets; `decklab-1100.png` : **1100×900**, 299 576 octets.
  Les deux vus par Codex. Détails ouverts également inspectés à 1100; contrôle 125 % vu et décodé.
- `preview.mp4` : **H.264, 1500×970, 120 images, 20 i/s, 6 s**, 334 380 octets, sans audio.
  `preview.gif` : 1 067 185 octets, 120 images / 6 000 ms. Décodage complet FFmpeg des deux réussi,
  GIF aussi décodé intégralement par Pillow. Les frames proviennent du vrai QWidget Windows : survol,
  sélection, ouverture/fermeture des détails, Statistiques puis Galerie. Horloge Qt échantillonnée;
  curseur ajouté seulement au film; aucune mesure de cadence physique revendiquée.
- `measure.json`, `measure-125.json`, `art-contrast.json`, `recording.json`, `verification.json` : mesures
  locales synthétiques, non versionnées. Captures natives Qt 125 % : 1875×1213 et 1375×1125 pixels;
  tailles logiques 1500×970 et 1100×900, aucun réglage Windows modifié.
- Prévol **RUNTIME_READY**, base propriétaire non ouverte, zéro écriture/réseau par cette commande.
- Ciblés en copies isolées : **9/9 offscreen à 125 % et 9/9 Windows natif à 125 %**. Clic, focus,
  Tab/Espace, toggles, hover 220 ms sans déplacement, sélection unique, transition 180 ms et mouvement réduit.
  Titres 20 px, sous-titres 16 px et descriptions Coach 15 px testés aux deux tailles, sans texte perdu.
  Au départ : accueil trop court en offscreen, descriptions comprimées en police agrandie et variation
  de 2 px au focus détectés, puis corrigés. Une première sélection de tests a échoué avant corrections;
  elle n'est pas présentée comme preuve complète.
- Contraste texte/fond : **16 paires ≥7,38:1** sur les tokens existants; pas une certification de tous
  les pixels du panorama ou des microtextes incorporés aux illustrations fictives.
- Porte complète isolée VERTE : **130 Qt + 1654 cœur = 1784 réussis, 3 ignorés, zéro échec**, sortie 0; compilation/hygiène vertes. Qt 73 s, cœur 573 s. Sources exécutables/tests identiques à la copie vérifiée avant nettoyage; aucun pytest dans le dépôt de travail.

## Portée, Git et STOP

Changements limités à `demos/`, `tests/test_decklab_reference.py` et orchestration. `src/`, version,
setup, dépendances, CI et référence PNG inchangés. Aucun accès à la base/cache/root personnel,
compte, sauvegarde ou journal. Aucun téléchargement d'art, installation, intégration ou publication.
Réseau limité aux opérations Git/GitHub privées autorisées. Aperçus ignorés, aucune image QA dans le commit.
Fast-forward `ee96628` → `7639260`, arbre initial propre, dépôt confirmé privé; aucun reset/force/rebase.
GitHub au SHA code : **0 statut, 0 check, 0 run** (agrégat pending sans statut); **aucune CI verte revendiquée**. HEAD privé distant confirmé au SHA code. La porte locale ne constitue pas une CI GitHub.
Un commit de code et un seul commit de rapport assaini; HEAD distant et état Git vérifiés après push final.

Limites : étude sombre FR-CA, six illustrations géométriques fictives, défilement vertical nécessaire,
dock fixe 355 px, aucun moteur Coach. Les petits textes dans les illustrations raster restent décoratifs;
les titres/sous-titres externes portent la lecture utile. Acceptation artistique finale au propriétaire,
audit indépendant réservé à ChatGPT. **AWAITING_AUDIT / NOT_RELEASE_READY**. Aucune intégration
progressive dans le vrai Deck Lab sans mandat ultérieur; installation 0.9.5 hotfix et public 0.9.3 inchangés.
