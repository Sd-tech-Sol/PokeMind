# RESULT — PM-UI-DECKLAB-REFERENCE-INTEGRATION-003 — AWAITING_AUDIT (2026-11-08)

**Référence originale versionnée en privé; prévisualisation Qt et film produits. STOP audit ChatGPT et réception esthétique propriétaire.**
Base `ecc06793d4f9c93ea04e8399a2572eff9d4eb314`, référence `2aa249c`,
code `84214b9944a6361eef5d9a9a7a74e5825f7256f7`, branche privée autorisée.
[Ancien RESULT](archive/2026-11/RESULT_PM-UI-PREMIUM-DECKLAB-DEMO-002_664d280_2026-11-08.md).

## Ouvrir les vrais aperçus locaux

```powershell
python demos/premium_decklab/reference.py
Start-Process .\build\qa-decklab-reference\decklab-full.png
Start-Process .\build\qa-decklab-reference\preview.mp4
```

Reproduction : `python demos/premium_decklab/reference_preview.py`.
[Guide et compromis](../demos/premium_decklab/README.md), [référence vérifiée](../docs/design/pokemind-brainball/REFERENCE_DECKLAB_PREMIUM_2026-11-08.md).

| Aperçu local ignoré par Git | Vérification Codex locale |
|---|---|
| `build/qa-decklab-reference/decklab-full.png` | Fenêtre entière 1500 × 970, 300 694 octets, décodée et vue |
| `build/qa-decklab-reference/decklab-1100.png` | Contrôle 1100 × 900, 267 037 octets, décodé et vu |
| `build/qa-decklab-reference/preview.mp4` | H.264, 1500 × 970, 120 images, 20 i/s, 6 secondes, 266 053 octets, sans audio, décodage FFmpeg complet réussi |
| `build/qa-decklab-reference/preview.gif` | 1500 × 970, 120 images toutes décodées, 6 000 ms, 661 199 octets |

Le film provient de `window.grab()` sur de vrais QWidget synthétiques; aucune capture du bureau.
Enter Qt, clic, sélection/panneau, onglet Statistiques puis retour Galerie; horloge QPropertyAnimation échantillonnée.
Survol 220 ms : 0 → 0,5386 → 0,8377 → 0,9678 → 0,9992 → 1; six images intermédiaires distinctes.
Panneau/onglets 180 ms. Curseur circulaire ajouté au film seulement. PNG principal et images de sélection/statistiques
inspectés visuellement; métadonnées locales dans `recording.json`, `verification.json`, `native-125.json`.

## Référence et réalisation

- Fast-forward `664d280` → `ecc0679`; PNG non suivi préservé. Dépôt confirmé privé par GitHub.
- PNG exact, sans recréation : RGB, 1672 × 941, 2 155 435 octets; empreinte et lien dans le document de référence.
  Image fournie par le propriétaire, visuellement conforme à la maquette annoncée, sans renseignement personnel visible.
  Autorisation limitée au privé; représentations Pokémon conceptuelles, aucune licence publique de cartes déduite.
- Adaptation de présentation dans `demos/`, sans modification de `src/` : le vrai MainWindow construit Store/Services,
  historique et travaux dès son constructeur. Le prototype évite cette initialisation; aucune base/root personnel.
- Ordre des sept rubriques, sélecteur de deck, trois onglets et dock Coach de 355 px calqués sur `window.py`.
  ChatInput, AnimatedStack, CardArt via DemoCard, palette/logo/icônes existants réutilisés.
- Bandeau de deck, contours électriques, ambiance bleue et sélection or; six illustrations fictives originales,
  aucun téléchargement, cache TCGdex ou faux conseil IA. Coach explicitement hors ligne et commandes désactivées.
- Grille cinq colonnes à 1500, trois à 1100; panneau de sélection au centre, Coach à droite; clavier et mouvement réduit.

## Écarts visuels et limites de réception

Art géométrique fictif plus simple que les cartes Pokémon détaillées de la référence; six images distinctes seulement,
donc deuxième rangée partielle à grande largeur. Défilement vertical nécessaire pour le bas de galerie aux deux formats.
Identité fournie par le vrai PokeMind; bandeau moins illustré, lueurs mesurées. Pas de barre supérieure redondante,
nouveaux filtres/onglets, simulateur, optimisation, graphiques d'impact ou pourcentages inventés.
Coach avec ses contrôles réels représentés mais sans connexion; texte de présentation, aucune réponse IA simulée.
Panneau de carte synthétique au centre; ce n'est pas le widget de galerie de production. Sombre FR-CA seulement;
dock fixe dans cette étude. Les commandes d'ajout/export/comparaison de decks du vrai programme sont omises
de cet aperçu réduit. **Fidélité de direction et structure, aucune équivalence pixel à pixel ou acceptation artistique revendiquée.**

## Preuves techniques

Prévol `RUNTIME_READY`, base propriétaire non ouverte, zéro écriture/réseau par le prévol.
Tests ciblés isolés : 4 passés, puis 4 passés sous Qt natif Windows à 125 %.
Contrats testés : réseau/SQLite/chemins personnels interdits pendant instanciation, dock/navigation/onglets,
deux tailles, absence de défilement horizontal, hover intermédiaire sans déplacer les voisins, clavier/sélection,
transition réelle, arrêt au masquage et mouvement réduit, contrastes texte ≥ 4,5:1 sur les fonds palette.
Essai natif complémentaire 1500 → 1100 → 1500 à DPR 1,25 : captures 1875 × 1213 et 1375 × 1125,
défilement horizontal nul après stabilisation du layout. Aucun changement du DPI Windows.

**Porte complète `python scripts/local_gate.py` VERTE, sortie 0 : 130 Qt + 1649 cœur passés,
3 ignorés, zéro échec, 1779 passés au total.** Compilation/hygiène vertes; Qt 72 s, cœur 624 s.
Tous les pytest dans des copies isolées du gate, jamais dans le dépôt de travail ni sur les données personnelles.
Identité des quatre fichiers code/tests modifiés confirmée avec la copie de cette passe complète avant nettoyage.

## Confidentialité, Git et STOP

Aucune installation, version, sauvegarde, migration, compte, collecte, LLM, tag, release ou publication publique.
Production et données personnelles conservées sans accès; aucune dépendance installée. PNG source fourni autorisé
seul binaire versionné; aperçus/frames QA locaux ignorés. Code source testé identique à la copie isolée.
Code poussé privé; HEAD distant confirmé au SHA complet `84214b9944a6361eef5d9a9a7a74e5825f7256f7`.
GitHub à ce SHA : 0 statut, 0 check, 0 run. Agrégat `pending` sans statut, aucun run en file;
**la porte locale n'est pas une CI GitHub verte**. Un seul commit de rapport assaini; contrôle final
du HEAD distant et des statuts au SHA de rapport après push.
**AWAITING_AUDIT / NOT_RELEASE_READY.** Prochaine action : audit ChatGPT au SHA exact et visionnement propriétaire.
Aucune intégration ou installation autorisée par ce rapport.
