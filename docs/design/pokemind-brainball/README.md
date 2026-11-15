# Identité PokeMind — BrainBall électrique

## Sources approuvées par le propriétaire

**Référence graphique de marque (PRIORITAIRE, 2026-11-06)** :
[`assets/branding/pokemind-tcg-coach-original.png`](../../../assets/branding/pokemind-tcg-coach-original.png).

- Fichier **PNG d'origine identique à celui fourni**, non redessiné, non recompressé : **1060 × 1484 px**, **3 086 685 octets**, format RGBA.
- SHA-256 des octets : `30824d84f594be0e1fe33b3e9531f487e497252e17d7a16ff57763b787d7f0f5`
- Git blob SHA : `18abf6bccaecba8553556fbdbeeb8d980ff4eb45`
- Dessin : carte verticale bordée d'or et de bleu nuit, **« PokeMind »** en haut, **Pokéball-cerveau** au centre, **« TCG Coach »** en bas, tourbillons bleu électrique et cyan.
- Ne pas recréer ce dessin avec QPainter, SVG redessiné, IA générative, illustration approximative ou autre image. L'original est la source permanente. Des versions **dérivées par redimensionnement/encadrement uniquement** sont permises pour les icônes multi-résolutions. Respecter les proportions et éviter de couper les textes/bordures pour la version complète.
- L'ancien logo dessiné (deux petites cartes, cerveau sur la carte rouge) est **obsolète** et doit être remplacé aux endroits de marque. Il ne faut **pas** remplacer les cartes officielles du jeu/du classeur par cette image de marque.

**Référence de couleurs** : `palette.json` (thèmes foncé et clair); `palette-preview.svg` (aperçu). Le troisième fond d'écran panoramique est une référence d'ambiance **secondaire seulement**, pas un asset à mettre derrière les panneaux de PokeMind.

## Usage prévu

- Icône de fenêtre et barre des tâches, EXE Windows, raccourci bureau/menu Démarrer, iconographie installateur, écran d'accueil, bandeau « À toi de jouer », sections « À propos » et toute autre occurrence du **logo de marque**.
- Pour les petites résolutions (16–32 px), la carte entière ne rend pas le texte lisible : conserver le lien visuel à **la même image originale** en gardant les proportions et une silhouette reconnaissable. Si une déclinaison recadrée est nécessaire pour la lisibilité, elle doit être extraite exclusivement des pixels de l'original et l'original complet doit rester disponible et utilisé là où l'espace le permet.
- Les fichiers dérivés doivent être reproductibles depuis le PNG source, embarqués dans la compilation Windows sans dépendre du dépôt ou du réseau pour fonctionner.
- Ne pas changer l'architecture des deux thèmes : foncé bleu nuit et clair bleu pâle, actions bleues, or pour l'accent, rouge pour les erreurs/défaites/destructif.

## Dérivés générés (PM-UI-BRAINBALL-BRANDING-002)

`python scripts/make_icon.py --card` vérifie le SHA-256 de l'original, rend transparent **uniquement** le blanc de
page à l'extérieur des quatre coins arrondis (remplissage depuis chaque coin, limité à un carré de 96 px), puis
réduit l'image de moitié exactement (1060×1484 → 530×742, mêmes proportions) :
`src/pokemind/desktop/branding/pokemind-card.png`, embarqué dans l'EXE et l'installateur. Tout le reste en est
mis à l'échelle sans étirement : `theme.card_pixmap` (carte entière), `theme.logo_pixmap` (carte entière centrée
dans un carré transparent), `.ico` de 16 à 256 px, images de l'installateur et `docs/assets/pokemind-logo.png`.
L'original n'est jamais modifié. Aucune recoupe : même à 16 px, c'est la silhouette de la carte entière.

## Fichiers et mandat

- [`palette.json`](palette.json) : couleurs validées pour les deux thèmes.
- [`palette-preview.svg`](palette-preview.svg) : aperçu des couleurs seulement.
- [`.orchestrator/NEXT_PROMPT.md`](../../../.orchestrator/NEXT_PROMPT.md) : mandat courant de remplacement des assets, qui remplace l'ancien mandat de couleurs déjà terminé.
- [`.orchestrator/NEXT_ACTION.md`](../../../.orchestrator/NEXT_ACTION.md) : désigne le mandat actif.

## Sécurité et diffusion

Dépôt **privé** `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`. Aucun changement ni aucune publication du dépôt **public** `Sd-tech-Sol/PokeMind` sans GO distinct du propriétaire. Tests avec fixtures synthétiques; aucune inspection ni mutation des données privées.
