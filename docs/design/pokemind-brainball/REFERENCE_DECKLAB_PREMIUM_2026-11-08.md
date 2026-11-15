# Référence visuelle — Deck Lab BrainBall premium (2026-11-08)

**État : PNG reçu, décodé et inspecté visuellement par Codex le 2026-11-08.**
[Image originale](references/decklab-premium-target.png) : RGB, 1672 × 941, 2 155 435 octets.
SHA-256 : `4e5888a7b22b6c7a84168b4aa779bd4eb526c031ee80cea0357aa26938ffd2b1`.
Source fournie par le propriétaire : maquette générée dans ChatGPT, autorisée sur ce dépôt privé seulement.
Elle contient des représentations conceptuelles Pokémon; aucune licence de carte officielle ou permission
de publication publique n'en est déduite. Aucun renseignement personnel visible. Source intacte, sans optimisation.

## Intention visuelle
La dernière maquette générée dans le chat montre une **interprétation conceptuelle** d'un PokeMind Deck Lab beaucoup plus spectaculaire que les précédentes démos synthétiques : bleu nuit profond, accents bleu électrique et or, éléments lumineux subtils, grille de cartes richement illustrées, navigation latérale, panneau Coach IA à droite, bandeau du deck actif et onglets de galerie/statistiques.

## Portée réelle à préserver
- Réutiliser les données et interfaces **réelles**, existantes du PokeMind PySide6 : Deck Lab, galerie, images déjà chargées par ImageCache/TCGdex, sélection de decks, statistique publique, Coach IA séparé avec ses règles de consentement. Ne pas recréer toute l'application depuis une maquette.
- **La maquette n'est pas une spécification fonctionnelle** : elle contient des noms/cartes et des taux/recommandations inventés, ainsi que des onglets non implémentés. Ne jamais traiter ces nombres comme des données réelles ni les ajouter comme fonctions.
- Ne pas intégrer/copier les illustrations de cartes générées comme des images Pokémon officielles; utiliser les illustrations réelles légalement récupérées par le pipeline existant sur le PC, sans en versionner les fichiers.
- Éviter une refonte globale, WebView, frameworks/dépendances non nécessaires ou effets lumineux partout. Préserver thèmes clair/sombre, lisibilité, fenêtre étroite, paramètres de confidentialité, fluidité et option de mouvement réduit.

## Portée de la preuve Qt
Le mandat PM-UI-DECKLAB-REFERENCE-INTEGRATION-003 autorise un prototype isolé et une capture animée,
sans installation ni intégration au produit. La navigation, les trois onglets et le dock Coach suivent
`src/pokemind/desktop/window.py`; les six illustrations originales de la démo remplacent les cartes conceptuelles.
Les aperçus synthétiques restent locaux dans `build/qa-decklab-reference/`. Réception artistique en attente.

Retouche propriétaire suivante (PM-UI-DECKLAB-VISUAL-POLISH-004) : cartes agrandies, rangées équilibrées,
bandeau panoramique original et Coach avec accueil et panneaux explicatifs. Même référence intacte,
même shell de présentation; aucune intégration produit. Nouveaux aperçus dans `build/qa-decklab-polish/`,
anciens aperçus 003 conservés pour comparaison locale. Acceptation visuelle finale au propriétaire.
