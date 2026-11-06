# Identité PokeMind — BrainBall électrique

Demande propriétaire du 2026-11-05 : refondre **les deux thèmes** de l'application PySide6/Qt en conservant toutes les fonctionnalités. La **carte verticale originale PokeMind / TCG Coach** est l'inspiration prioritaire : cerveau-Pokéball rose/rouge, vortex **bleu royal/électrique**, rayons cyan, blanc nacré, or. Le **troisième fond d'écran panoramique** est préféré comme fond d'écran seulement : il ne doit pas rendre l'interface violette ou transformer les panneaux en fonds illustrés.

## Fichiers

- [`palette.json`](palette.json) : **source de vérité** des valeurs HEX foncé/clair et des couleurs de marque.
- [`palette-preview.svg`](palette-preview.svg) : vue compacte des deux thèmes, basée sur les tokens ci-dessus. Illustration de palette, pas capture d'EXE.
- [`.orchestrator/NEXT_PROMPT.md`](../../../.orchestrator/NEXT_PROMPT.md) : mandat exécutable par Claude Code. `.orchestrator/NEXT_ACTION.md` lui donne priorité.

## Direction graphique

- **Foncé** : fond bleu nuit, panneaux bleu profond, champs bleu marine, texte blanc bleuté. Actions et sélection **bleu électrique**, emphase **or**, reflets cyan, défaite/erreur en rouge seulement.
- **Clair** : fond blanc bleuté, cartes blanches, menu bleu pâle, actions bleu royal foncé, accents vifs réservés aux zones décoratives. Ne pas utiliser du cyan clair comme petit texte sur blanc.
- **Bandeau `À toi de jouer`** : dégradé bleu royal → bleu électrique, lettres blanches, détails or. Pas de bandeau rouge générique.
- **Graphiques** : victoire=bleu, défaite=rouge, inconnu=or, neutre=bleu gris; ne pas coder l'information par couleur seulement.
- **Couverture** : menu, pages d'accueil, KPI, statistiques, Deck Lab, bibliothèque/classeur, recherche, chat/dock, historique, Réglages, terminal, boîtes, boutons, onglets, chargements, infobulles, scrollbars et états disabled/focus/hover.
- **Lisibilité** : contraste WCAG AA pour texte normal ≥4.5:1 et grand texte/éléments essentiels ≥3:1 sur fonds réels. Documenter tout ajustement d'une couleur.
- **Architecture** : réutiliser `src/pokemind/desktop/theme.py` : `PALETTES`, `colors()`, `palette()`, `stylesheet()`. Éliminer les valeurs visuelles codées en dur là où elles contredisent le thème; ne pas toucher à la logique, aux données, au logo, aux dépendances ni à la publication publique.

Les images originales du propriétaire ont été fournies dans la conversation ChatGPT, mais **les fichiers binaires de la carte et du fond d'écran ne sont pas nécessaires pour appliquer les couleurs** : la spécification HEX est autonome. Ne pas remplacer le logo déjà intégré à PokeMind.

**Dépôt de développement privé** : `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`. **Dépôt public** `Sd-tech-Sol/PokeMind` : aucune écriture et aucune release sans nouveau GO.
