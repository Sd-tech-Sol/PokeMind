# RESULT — PM-UI-PREMIUM-DECKLAB-001 — AWAITING_AUDIT (2026-11-08)

**Galerie Deck Lab polie, code privé livré; STOP pour audit indépendant ChatGPT.**
Code : `b4d03600ce7d133a403e5d362a5924837f0514b9`, branche `work/pm-v1-lotj-final-readiness-windows`.
Base : `da7efc1458b3b4388c0e782a3454b42d3bacf402`. Décision [D-295](DECISIONS.md).
[Rapport précédent archivé](archive/2026-11/RESULT_PM-RELEASE-095-RECEPTION-HOTFIX-INSTALL-001_ddded32_2026-11-08.md).

## Résultat et périmètre

- Synchronisation fetch/pull **fast-forward** de `ddded32` à `da7efc1`, arbre initial propre, dépôt confirmé privé;
  hotfix `00eecb3` et réception propriétaire inclus. Mandat complet et continuité relus, sans autre tâche exécutée.
- Avant : sections serrées, groupes courts centrés, cadre générique et reflet marqué. Après : sections espacées,
  tuiles alignées à gauche et de même largeur entre catégories, noms et impressions sur plusieurs lignes, surfaces
  BrainBall et cadre de sélection explicite. Palette JSON inchangée; styles nouveaux limités à la galerie.
- `CardTile`/`DeckGallery`/`CardArt` réutilisés : animation existante **220 ms OutCubic**, zoom optique **1,8 %**,
  soulèvement **2 px**, reflet discret et liseré bleu. La sélection utilise le token `focus`, persiste jusqu'au
  prochain focus/activation et ne s'enregistre jamais. Le hover ne sélectionne pas une autre carte.
- Pas de mouvement du layout : le zoom reste dans l'encart réservé. `MotionEffects` garde les autres contrôles
  et évite une deuxième couche sur les cartes de galerie. Pas de nouveau timer, snapshot, moteur ou dépendance.
- Mouvement désactivé, page masquée, fermeture et remplacement de galerie : animations arrêtées/nettoyées.
  Un événement tardif sur une carte masquée ne redémarre pas l'animation. Tab/Espace et agrandissement conservés.
- Défaut révélé par les essais corrigé : la grille Qt comprimait les labels longs contre l'image à hauteur fixe;
  la tuile réserve maintenant la hauteur réellement requise à sa largeur et sa police. Pas de chevauchement.
- **Cinq fichiers code/tests seulement** : quatre modules visuels et `tests/test_desktop_qt.py`. `window.py`,
  services, catalogue, cache/pipeline images et hotfix UTC/local inchangés; aucune logique de deck/statistiques,
  préférence, confidentialité, version ou ressource de production modifiée.

## Preuves locales isolées

Toutes les suites ont tourné dans les copies synthétiques de `scripts/local_gate.py`, hors du dépôt de travail,
avec `data/local` exclu, réseau hors ligne et Qt `offscreen`. Aucun pytest direct dans le dépôt propriétaire.

| Vérification finale | Passés | Ignorés | Échecs | Code |
|---|---:|---:|---:|---:|
| Ciblée : galerie/motion/images/thème, Qt | 12 | 0 | 0 | 0 |
| Ciblée : cœur | 22 | 0 | 0 | 0 |
| **Porte complète : Qt** | **130** | **0** | **0** | **0** |
| **Porte complète : cœur** | **1639** | **3** | **0** | **0** |

**`python scripts/local_gate.py` : PORTE LOCALE VERTE, sortie 0.** Compilation et hygiène vertes;
Qt 79 s, cœur 623 s; **1769 passés au total, 3 ignorés**. Source testée identique au commit de code livré.
Huit cas Qt ajoutés : images aux quatre coins non coupées au zoom, géométries voisines immobiles,
sélection distincte du hover, clavier et dialogue, arrêt/désactivation/héritage du réglage,
FR/EN, clair/sombre, fenêtres 1100/1500 px, police 14/18 px, labels sans chevauchement et repli honnête.
Défilement/redimensionnement conservent les pixmaps sans nouveau fetch; remplacement détruit les anciennes tuiles.
Les échecs ciblés de développement (attente d'affichage Qt et chevauchement) ont été corrigés avant ces passes vertes.

Captures **du composant Qt natif Windows, entièrement synthétiques**, avant/après :
`build/qa-premium-decklab/before-*.png` et `after-*.png` (**12 PNG**, ignorés par Git).
Vérification visuelle locale des deux thèmes, des images géométriques et du repli, dont police agrandie.
Aucun contenu propriétaire ni illustration TCG redistribuée. Scripts locaux `capture.py` et `measure.py` au même endroit.
Mesure exploratoire unique sur 60 tuiles de repli : base/correctif, affichage **662,3/635,3 ms**;
120 défilements **1029,2/869,5 ms**, aucune animation active à la fin. Pas un benchmark ni une garantie de latence.
DPI physique Windows non changé; police agrandie exercée. Essais sur composant/fixtures, pas réception propriétaire.

## Confidentialité, Git et arrêt

Prévol `RUNTIME_READY`, sortie 0 : base propriétaire non ouverte, aucun réseau ni écriture par le prévol.
Aucun accès aux données personnelles, sauvegarde, migration, Setup, installation, build binaire ou publication.
L'installation **0.9.5 hotfix acceptée** reste intacte; les sauvegardes existantes restent conservées, sans inspection.
Version publique **0.9.3**, aucun push public/tag/release. Constats locaux rapportés par Codex, pas VERIFIED.

Code poussé uniquement sur la branche privée; HEAD distant de code vérifié au SHA exact `b4d0360`.
GitHub au même SHA : **0 statut, 0 check, 0 run** (état agrégé `pending` faute de statuts, aucun run en attente).
Aucun fichier workflow suivi à HEAD; aucune CI déclenchée ni présentée verte. Un seul commit de rapport assaini,
avec RESULT remplacé, archive et suivis cohérents; contrôle du HEAD distant et des statuts au SHA final après push.
**AWAITING_AUDIT / NOT_RELEASE_READY : STOP ChatGPT.** Aucune autre tranche, installation ou publication autorisée.
