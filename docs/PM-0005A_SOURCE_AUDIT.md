# PM-0005A — audit des sources officielles (2026-10-11)

## Méthode et portée

Consultation manuelle et bornée le 11 octobre 2026 (UTC), exclusivement sur les
domaines officiels Pokémon. Les pages externes ont été traitées comme du contenu non
fiable : aucune instruction n'a été exécutée et aucun texte intégral, PDF, image ou
liste dynamique n'a été copié dans Git. Le registre versionné contient seulement des
métadonnées, de courts faits généraux et des liens canoniques.

Plusieurs pages `pokemon.com` rendent leur contenu dans un cadre protégé par
Incapsula. Le contenu des annonces a pu être vérifié dans l'index officiel; le portail
`play.pokemon.com` était directement lisible. Un portail de navigation est marqué
`navigation_only` et ne vaut pas preuve d'interprétation de chaque PDF lié.

## Sources consultées

| Source officielle | Publication / effet | Accès et faits utilisables |
|---|---|---|
| [Rotation Standard 2026 FR](https://www.pokemon.com/fr/actualites/rotation-de-la-saison-2026-du-format-standard-pour-le-jcc-pokemon) | 2026-01-09; Live 2026-03-26; présentiel 2026-04-10 | Vérifiée par index officiel. Marques H/I/J admissibles, G retirée; anciennes impressions possibles si réimpression valide; délai usuel, non universel, d'environ deux semaines. |
| [Rotation Standard 2026 EN](https://www.pokemon.com/uk/news/2026-pokemon-tcg-standard-format-rotation-announcement) | 2026-01-09; mêmes dates | Corrobore la FR. Expanded demeure Black & White et ultérieur en tournoi, mais Live ne prend pas en charge toutes ces cartes. |
| [Competitive Rules & Formats](https://play.pokemon.com/en-us/resources/rules/) | dynamique; consultée 2026-10-11 | Directement accessible. Rotation par marque et principe des réimpressions actuelles; lien vers errata. |
| [Documents Play! Pokémon EN](https://play.pokemon.com/en-ca/resources/documents/) et [FR](https://play.pokemon.com/fr-ca/resources/documents/?filter=tcg) | dynamique; consultés 2026-10-11 | Portails accessibles : manuel JCC, errata et validité promo sont listés. Les PDF derrière les liens ne sont pas réputés tous interprétés. |
| [Mise à jour T2 2026 FR](https://www.pokemon.com/fr/actualites/mise-a-jour-des-regles-play-pokemon-du-deuxieme-trimestre-2026) | 2026-05-21 | Vérifiée par index officiel. Les réimpressions fonctionnelles peuvent être valides dès obtention pendant une Avant-première; ceci ne prouve aucune paire d'impressions particulière. |
| [Mise à jour Q3 2026 EN](https://www.pokemon.com/us/news/play-pokemon-rules-and-resources-updated-for-q3-2026) | 2026-09-01 | Actualisation plus récente trouvée. Petite clarification du manuel JCC sur la remise d'une decklist; aucune nouvelle règle carte par carte n'est inférée. |
| [Perfect Order — bannissements](https://www.pokemon.com/uk/play-pokemon/about/mega-evolution/mega-evolution-perfect-order-banned-list-and-rule-changes-announcement) | annonce 2026-03-12; effet 2026-04-10 | Medicham V, Evolving Skies 083/203, 185/203 et 186/203 interdit en Expanded; aucun changement Standard annoncé. Les identités officielles ne sont pas assimilées à des IDs TCGdex sans preuve. |
| [Chaos Rising — changements](https://www.pokemon.com/us/play-pokemon/about/mega-evolution/mega-evolution-chaos-rising-rule-changes-announcement) | annonce 2026-05-07; effet 2026-06-05 | Aucun changement annoncé aux listes Standard ou Expanded. Ce communiqué ne prouve pas à lui seul une liste complète en octobre. |
| [Validité des cartes promo](https://www.pokemon.com/uk/play-pokemon/about/pokemon-tcg-promo-card-legality-status) | registre dynamique | Accessible, mais liste volontairement non recopiée. Une promo absente du registre local reste `unknown`. |
| [Rules & Resources / Card Dex](https://www.pokemon.com/us/play-pokemon/about/card-dex/) | dynamique | L'index officiel liste manuel, errata, bannissements, annonces et promos. État `navigation_only`; pas de présomption que chaque document est validé. |

Le manuel JCC et le PDF d'errata étaient liés, mais leur récupération directe par
l'outil d'audit était encapsulée par la protection du site. Ils sont donc
`NON_VERIFIED_SOURCE` pour toute donnée non corroborée par une annonce lisible. Aucune
liste exhaustive d'errata, bannissements ou promos n'est chargée.

## Conflits et décisions prudentes

- Les annonces FR et EN concordent sur les dates et marques 2026.
- Une annonce communautaire officielle Live évoquait le 27 mars selon son fuseau;
  le moteur conserve la date normative publiée dans l'annonce de rotation, soit le
  26 mars, et enregistre la plateforme explicitement.
- « En général deux semaines » n'est pas transformé en calcul automatique : la date
  de sortie américaine et l'exception promo doivent être documentées par impression.
- Le nom identique, même en deux langues, n'établit jamais une équivalence fonctionnelle.
- Le portail actuel et les annonces partielles ne prouvent pas une couverture
  exhaustive des restrictions; une marque H/I/J donne donc `unknown` tant que cette
  couverture manque.
- Après le 11 octobre 2026, ou avant l'entrée en vigueur documentée, le moteur ne
  prolonge pas la règle : `unknown` / source hors intervalle.

## Réutilisation

Les pages et documents restent la propriété de Pokémon/Nintendo/Creatures/GAME FREAK.
PokeMind conserve seulement URL, titre, dates, empreinte du petit enregistrement
normalisé et résumé factuel. Aucun droit de redistribution d'un manuel ou d'une liste
complète n'est présumé.
