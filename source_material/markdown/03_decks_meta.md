# VOLUME 3 — DECKBUILDING, MÉTAGAME ET SCOUTING 2026

**Encyclopédie compétitive Pokémon TCG Live**  
**Photographie du Standard au 9 octobre 2026 — les classements changent**

> Ce volume combine des données de tournois consultées au début d'octobre 2026 et des principes durables. Ne traite jamais les pourcentages comme des prédictions certaines de tes parties. Les agrégateurs utilisent des échantillons, des regroupements d'archétypes, des formats et des dates qui diffèrent. Des résultats de plateforme en ligne ne sont pas une mesure directe de la ligue classée de TCG Live. [S16][S17][S18]

## 1. Construire un deck, ce n'est pas accumuler des cartes fortes

Un deck compétitif de 60 cartes doit faire la **même chose importante** assez souvent, tout en disposant d'issues lorsque l'adversaire contrarie le premier plan. Sa force se juge par la vitesse de démarrage, la fréquence des tours morts, la qualité des attaques obtenues, les Récompenses concédées et l'adaptation aux affrontements dominants.

Commence par écrire une **phrase de victoire** : « Je veux préparer cet attaquant au plus tard au tour X, puis prendre les Récompenses selon un parcours que ma liste peut exécuter. » Si tu ne peux pas dire comment le deck prend six Récompenses, il est encore au stade de collection de synergies.

Le format impose 60 cartes, normalement quatre exemplaires au maximum d'une même carte par nom hors exceptions comme les Énergies de Base et les restrictions spéciales. Vérifie toujours les cas particuliers dans le texte et les règles du format : la quantité autorisée dépend d'un nom précis, pas simplement d'une illustration différente.

## 2. Les huit fonctions d'un deck solide

1. **Attaquant principal** capable de réaliser le plan de Récompenses.
2. **Attaquant secondaire** qui répare un matchup ou un seuil de dégâts.
3. **Moteur de pioche** afin de transformer une main faible en actions utiles.
4. **Recherche Pokémon** pour rejoindre rapidement les éléments de l'évolution.
5. **Énergies et accélération** pour attaquer au bon tour sans surcharger les cartes mortes.
6. **Mobilité** pour choisir l'attaquant, sortir d'un piège et diminuer le coût de retraite.
7. **Interaction** : gust, perturbation de main, Stade, suppression ou pression sur le moteur adverse.
8. **Récupération** : moyen raisonnable de refaire des attaquants et de récupérer une ressource nécessaire.

La bonne proportion varie énormément d'un archétype à l'autre. Un deck d'Évolution de Niveau 2 a souvent davantage besoin de cartes de recherche et de pioche qu'un deck de Pokémon de Base agressif; un deck à attaques peu coûteuses peut jouer moins d'Énergies. Les « 20 Pokémon / 30 Dresseurs / 10 Énergies » n'ont aucune valeur universelle : copier une liste établie puis modifier avec méthode est généralement plus fiable.

## 3. Trouver la liste de départ

**Méthode A — référence récente.** Sur Limitless TCG, choisir un grand tournoi, ouvrir les listes du Top 8, et comparer plusieurs listes du même archétype. Noter les cartes communes et les différences visibles. Une carte jouée à quatre exemplaires dans toutes les listes est probablement un noyau. Un unique objet apparaissant chez un joueur peut être une adaptation locale ou personnelle.

**Méthode B — cohérence du plan.** Écrire pour chaque carte : « Quel problème résout-elle? À quel tour? De combien d'exemplaires ai-je besoin? » Éviter les cartes incluses « parce qu'elles ont l'air puissantes » sans lien direct avec la victoire.

**Méthode C — tests sans modification.** Tester la liste copiée durant une trentaine de parties contre différents affrontements pour apprendre ce qu'elle **cherche** à faire avant de décider qu'une carte est mauvaise. Dix défaites ne suffisent pas à identifier statistiquement un problème précis.

## 4. La stabilité : des probabilités qu'on peut calculer

Pour une main de **7 cartes** tirées uniformément d'un deck de **60**, la probabilité d'avoir au moins un exemplaire d'une carte jouée à `k` copies est : `1 - C(60-k,7) / C(60,7)`. Ceci est un calcul de probabilité élémentaire avant condition de mulligan et effets de recherche; les sept cartes de départ réelles d'une partie avec Pokémon de Base obligatoire possèdent une distribution conditionnelle.

| Copies dans le deck | Présence ≥ 1 dans 7 cartes |
|---:|---:|
| 1 | 11,67 % |
| 2 | 22,15 % |
| 3 | 31,54 % |
| 4 | 39,95 % |
| 8 | 65,36 % |
| 10 | 74,14 % |
| 12 | 80,94 % |

L'effet d'un quatrième exemplaire varie selon la fonction de la carte. Pour une carte **indispensable immédiatement**, un pourcentage de départ plus haut peut valoir une case. Pour une carte de fin de partie searchable et récupérable, une seule copie peut être rationnelle.

**Probabilité de carte en Récompense.** Un unique exemplaire réparti aléatoirement dans un deck de 60 a 6/60 = **10 %** de chances de se retrouver parmi les six Récompenses. Deux exemplaires sont **tous les deux** en Récompense avec environ **0,85 %** de probabilité. Ce calcul n'inclut pas les évolutions révélées par le jeu, les tirages déjà effectués ni les interventions de cartes.

## 5. Comparer deux cartes par les tours où elles servent

Une carte de recherche A peut être plus faible dans une situation générale, mais meilleure dans ta séquence initiale parce qu'elle cible un Pokémon de Base; une carte de recherche B peut obtenir n'importe quel Pokémon mais exiger deux défausses. Leur comparaison est conditionnelle : as-tu une main suffisante? veux-tu mettre une Énergie à la défausse? est-ce le premier ou le sixième tour?

**Test A/B utile.** Garde 58 à 59 cartes fixes. Remplace une carte, puis joue une série de parties avec suivi de la catégorie adverse, des tours de démarrage et des erreurs. Pour une comparaison fiable, alterne A et B durant des périodes comparables; ne compare pas A contre les meilleurs decks à B contre des débutants.

**Piège statistique.** Une carte associée aux meilleures listes n'est pas nécessairement **la cause** de leur réussite. Les très bons joueurs choisissent aussi des cartes spécifiques, et les listes qui survivent à un tournoi évoluent sous pression de sélection.

## 6. Lire Limitless comme un analyste

Le site **Limitless TCG** publie des résultats en présentiel, des decklists, des classements et des historiques. Sa plateforme **Play! Limitless** donne aussi des résultats de tournois en ligne. Ces deux univers sont complémentaires mais pas interchangeables. **Limitless Labs** analyse les pairings et les conversions de certains événements; ses propres pages signalent que certains classements calculés hors logiciel officiel peuvent contenir des erreurs. [S16][S17][S18]

Pour chaque chiffre, relever **la date, le format, l'extension la plus récente, la région, l'échantillon, le regroupement ou non des variantes, et le dénominateur**. Un 55 % observé sur vingt matchs n'est pas aussi convaincant qu'un 52 % observé sur mille. Une conversion « Jour 2 » n'est pas une probabilité générale de gagner une partie.

**Part de méta** = nombre de joueurs utilisant l'archétype / total des joueurs de l'échantillon. **Taux de victoire** = matchs gagnés / (gagnés + perdus + nuls selon la convention du site). **Conversion** = fraction des joueurs d'un archétype accédant à un seuil défini. Vérifie la convention propre au tableau; ne mélange pas ces nombres.

## 7. Portrait quantitatif : tournois en ligne Standard 30C

**Échantillon consulté** : Play! Limitless, Standard 2026, filtre 30C, snapshot de consultation. Le résultat visible dans cette collecte affichait environ **271 tournois, 17 131 joueurs et 36 713 matchs**. Les statistiques évoluent et des recalculs ou variantes peuvent les modifier. Ce ne sont pas les taux de victoire du classement Live. [S19]

| Archétype | Part des inscriptions | Taux de victoire affiché |
|---|---:|---:|
| Dragapult | 10,38 % | 52,99 % |
| N's Zoroark | 5,70 % | 48,85 % |
| Dragapult Dusknoir | 5,28 % | 49,32 % |
| Slowking | 5,18 % | 51,04 % |
| Basic Box | 5,14 % | 52,32 % |
| Alakazam Dudunsparce | 4,86 % | 49,97 % |
| Mega Excadrill | 4,34 % | 50,09 % |

**Interprétation.** Dragapult est à la fois répandu et performant sur cet échantillon. Basic Box, moins joué, affiche également un bon résultat. N's Zoroark est joué relativement souvent malgré une moyenne inférieure à 50 % dans cette population précise, ce qui ne signifie pas qu'un excellent joueur ne peut pas en tirer un bon résultat.

**Avertissement.** Des variations d'échantillon, de période, de notation des nuls et de sous-archétypes expliquent pourquoi les chiffres de deux pages du même réseau peuvent sembler se contredire. Toujours enregistrer le filtre exact dans ses notes.

## 8. Photo des grands tournois : résultats concrets

- **Championnats du monde 2026 (28 au 30 août, 797 joueurs)** : Andrew Hedrick a terminé premier avec **Dragapult**. La liste de tournoi sert d'exemple d'un deck et d'une stratégie qui ont réellement gagné en environnement de haut niveau, mais ne prétend pas déterminer la meilleure version pour tous les événements suivants. [S20]
- **Régional de Recife (3-4 octobre, 1 074 joueurs)** : Victor Carreira Rodrigues a terminé premier avec **Ogerpon / Meganium** (variante Arboliva dans la page de joueur Limitless Labs). Le Top 8 présente aussi plusieurs Dragapult, N's Zoroark, Mega Excadrill, Slowking et Rocket's Honchkrow. C'est la preuve qu'une lecture du méta ne consiste pas uniquement à copier l'archétype le plus populaire. [S21][S22]
- **Recife, conversion Jour 2** : Dragapult 358 inscrits jour 1 et 53 jour 2 (14,80 %); N's Zoroark 79 et 31 (39,24 %); Slowking 48 et 15 (31,25 %). La très forte conversion de N's Zoroark mérite enquête; elle n'établit pas à elle seule un taux intrinsèque de victoire de 39,24 %. [S23]

**Lecture professionnelle.** Ne copie pas la liste du champion sans comprendre son adversaire moyen, les matchups joués et la variance d'un tournoi. Un résultat gagnant signale qu'une stratégie peut fonctionner; il ne démontre pas qu'elle dominera au prochain événement.

## 9. Les matchups : comment lire un tableau croisé

Le format Standard est un écosystème. Ton deck peut posséder une excellente moyenne mais perdre régulièrement contre une catégorie suffisamment répandue. Les matchups pèsent plus lourd sur le choix d'un deck que la seule valeur de son taux de victoire global.

**Exemple documenté (Play! Limitless, filtre 30C)** : Dragapult était donné à environ **44,27 %** contre Basic Box sur 515 matchs, à **44,09 %** contre Mega Excadrill sur 381 matchs et **58,54 %** contre Alakazam Dudunsparce sur 439 matchs. Ce sont des observations, pas des lois. Les joueurs, variantes, dates et environnements peuvent changer ces nombres. [S24]

**Calcul de méta pondéré, simplifié** : si la population attendue est 40 % deck A, 30 % deck B, 20 % deck C et 10 % autres, et tes chances estimées sont 55 %, 45 %, 60 %, 50 %, alors `0,4×0,55 + 0,3×0,45 + 0,2×0,60 + 0,1×0,50 = 52,5 %`. Il s'agit d'une prévision illustrant la méthode, pas d'une statistique réelle.

Attention : les écarts peuvent venir de la qualité des pilotes et des listes. Un joueur qui connaît cent matchs d'un archétype peut dépasser la moyenne d'un deck théoriquement supérieur qu'il découvre.

## 10. Outil spécialisé : Trainer Hill

Trainer Hill propose des vues de métagame, tableaux d'affrontements, évolution des listes, présence des cartes et comparaison des squelettes. Il faut le consulter comme un **outil d'exploration** et vérifier ses filtres, son échantillon et sa méthode de calcul. Certaines vues peuvent nécessiter une interaction ou un accès particulier. [S25]

**Question type** : « Mes défaites contre Mega Excadrill viennent-elles de l'absence de mobilité, de l'attaquant principal ou de ma liste de Supporters? » Utilise un comparateur de decklists, isole une carte candidate, puis teste réellement cette modification. La métrique est une piste d'enquête, pas une prescription automatique.

## 11. Dossiers de reconnaissance : archétypes à maîtriser

### Dragapult et variantes

**Observation confirmée** : poids très important en tournois 2026 et victoire du Mondial. **Mission du scout** : repérer les Pokémon qui développent la pioche, les façons de placer des dégâts au Banc, les règles exactes de l'attaque de Dragapult ex, la disponibilité de plusieurs attaquants, les transitions vers des cibles de Récompenses. **Ta réponse** : ne pas exposer de petits Pokémon qui permettent un K.-O. combiné; calculer tous les K.-O. possibles au Banc; conserver les sorties d'un éventuel contrôle précoce. **À tester** : l'effet des variantes Dusknoir/Blaziken sur les échanges et la régularité. [S20][S24]

### N's Zoroark

**Observation** : présent dans les résultats majeurs, avec une conversion notable à Recife. **Mission du scout** : identifier quels Pokémon « de N » forment les attaques et les options, et quelles ressources permettent de contourner le plan standard. **Ta réponse** : ne pas attaquer automatiquement le premier Pokémon visible; repérer la source de pression et les chemins de Récompenses réalistes. **À tester** : limites du taux moyen lorsque beaucoup de joueurs utilisent l'archétype sans la même maîtrise. [S23]

### Basic Box

**Observation** : taux de victoire solide sur l'échantillon en ligne. **Mission du scout** : le deck emploie plusieurs attaquants ou supports de Base; établir rapidement la fonction de chaque pièce révélée. **Ta réponse** : éviter de supposer qu'une Faiblesse résout tout; construire un plan par cibles et anticiper l'attaquant de réponse. **À tester** : quels matchups changent si ta propre liste remplace une seule carte de tech. [S19]

### Slowking

**Observation** : résultats compétitifs dans les gros tournois et présence à Recife. **Mission du scout** : lire attentivement la carte exacte et les effets associés; ne pas inférer le fonctionnement de l'attaque à partir du seul nom « Slowking ». **Ta réponse** : identifier ce qui permet la rotation des attaquants et la continuité de la pression. **À tester** : valeur des lignes de gust qui suppriment une pièce de soutien. [S21][S23]

### Alakazam et variantes Dudunsparce / Dusknoir

**Observation** : plusieurs variantes à Recife; les variantes diffèrent suffisamment pour ne pas leur attribuer exactement le même taux. **Mission du scout** : distinguer les façons de piocher, de poser des dégâts et de convertir les tours faibles. **Ta réponse** : préparer les seuils de K.-O. appropriés et ne pas donner gratuitement un Pokémon de soutien. **À tester** : la stratégie contre Alakazam sans supposer que toutes les versions jouent les mêmes cartes. [S22]

### Mega Excadrill

**Observation** : présent parmi les decks importants; comme Méga-ex, le risque de trois Récompenses est central pour l'évaluation. **Mission du scout** : vérifier la condition exacte des attaques, la vitesse d'installation et les protections. **Ta réponse** : calculer si ta ligne à deux Récompenses peut être convertie en une ligne plus rapide vers ses trois Récompenses. **À tester** : quel soutien doit être éliminé en priorité pour empêcher un second attaquant.

### Ogerpon / Meganium (et variantes)

**Observation** : victoire du Régional de Recife au début d'octobre 2026. **Mission du scout** : reconstituer son moteur énergétique, ses évolutions, son attaquant de secours et le rôle de variantes comme Arboliva. **Ta réponse** : décider si attaquer le moteur, les Pokémon qui portent les Énergies ou les cibles riches en Récompenses produit le meilleur tempo. **À tester** : ne pas confondre la liste gagnante avec toutes les versions du deck. [S21]

### Festival Lead

**Observation** : archétype présent dans les tournois importants. **Mission du scout** : vérifier les exigences exactes de sa condition d'attaque et la fragilité potentielle de son Banc. **Ta réponse** : travailler la course aux Récompenses en tenant compte de nombreux Pokémon à une Récompense. **À tester** : peut-on gagner en éliminant une pièce d'installation plutôt que l'attaquant immédiat? [S16]

### Dhelmise et variantes

**Observation** : participation visible sur les tableaux. **Mission du scout** : apprendre la condition d'attaque et les cartes qui permettent la répétition des attaques. **Ta réponse** : ne pas oublier les dommages progressifs et la possibilité de verrouillage. **À tester** : la perte d'une carte de mobilité transforme-t-elle le matchup? [S19]

### Les decks moins courants et surprises

Un tournoi n'est pas rempli exclusivement des sept meilleures lignes du classement. Les versions Rocket's Honchkrow, Lucario Hariyama, Hydrapple, Crustle et autres imposent une reconnaissance rapide. Le protocole universel vaut mieux que mémoriser cent listes : lire le texte exact; trouver le moteur; identifier les dégâts maximaux sur un tour; calculer le parcours de Récompenses; conserver une solution de déplacement. [S22]

## 12. Choisir un deck pour gagner plutôt que pour impressionner

Classer chaque candidat de 1 à 5 dans : stabilité initiale, plafond stratégique, longueur des parties, complexité de pilotage, qualité contre les trois decks les plus fréquents, exposition à un mauvais affrontement, coût en crédits, fatigue mentale et aisance personnelle. Un deck légèrement inférieur statistiquement mais maîtrisé depuis deux cents parties peut être un meilleur choix pour toi.

**Règle de sélection.** Choisir au départ **un deck principal** et **un deck d'étude**. Le principal sert au classement et aux tournois; l'étude sert à comprendre ce que fait l'adversaire. Changer de deck principal seulement lorsqu'un signal explicite l'impose : rotation, nouvelle extension, baisse durable sur un échantillon pertinent, ou matchup dominante devenue réellement intenable.

## 13. Protocole de mise à jour du méta

**Chaque semaine :** consulter les derniers Régionaux/Internationaux, relever les cinq archétypes dominants, comparer leur part et leur conversion, puis examiner les cartes qui apparaissent davantage dans les bons résultats. Noter les changements. **À chaque nouvelle extension :** suspendre les conclusions fortes, tester le format et distinguer hype et résultats reproductibles.

Une fiche méta doit avoir les champs : `date | format | période | région | nombre de matchs/joueurs | regroupement | archétype | part | taux de victoire | contre-decks | confiance`. Sans ces champs, tu risques de mélanger des séries statistiques qui racontent des histoires différentes.

## 14. Compte rendu et limites de la recherche

**Vérifié directement** : annonce officielle de rotation; pages de résultats Limitless des Mondiaux 2026 et de Recife; liste des archétypes populaires en Standard 30C; conversions de Recife dans Labs; pages d'affrontements Play! Limitless; fonctionnalités offertes par Trainer Hill. **Non établi** : taux de victoire personnel du joueur, meilleure liste absolue après une future extension, résultat de chaque match de chaque tournoi mondial et carte parfaite pour tous les adversaires. Ces questions exigent des données nouvelles ou des tests du joueur.

Ce manuel ne reproduit pas des milliers de listes de cartes ni l'intégralité de guides appartenant à d'autres auteurs. Il synthétise des principes, des résultats ponctuels et les méthodes permettant de consulter les sources primaires à jour. Les listes complètes doivent être récupérées par les liens de tournoi afin d'éviter une liste figée/illégale à la prochaine rotation.

## Sources du volume 3

- [S01] Rotation officielle 2026 : https://www.pokemon.com/fr/actualites/rotation-de-la-saison-2026-du-format-standard-pour-le-jcc-pokemon
- [S16] Limitless TCG, métagame et classements : https://www.limitlesstcg.com/
- [S17] Limitless Labs, analyses : https://labs.limitlesstcg.com/
- [S18] Play! Limitless, plateforme de tournois en ligne : https://play.limitlesstcg.com/
- [S19] Play! Limitless, Standard 2026, filtre 30C : https://play.limitlesstcg.com/decks?format=standard&rotation=2026&set=30C
- [S20] Limitless, listes des Championnats du monde 2026 : https://limitlesstcg.com/tournaments/515/decklists
- [S21] Limitless, listes du Régional de Recife : https://www.limitlesstcg.com/tournaments/580/decklists
- [S22] Limitless, classement de Recife : https://www.limitlesstcg.com/tournaments/580
- [S23] Limitless Labs, conversions par deck à Recife : https://labs.limitlesstcg.com/0075/decks?combine=&conversion=
- [S24] Play! Limitless, matchups Dragapult, Standard 30C : https://play.limitlesstcg.com/decks/dragapult-ex/matchups?format=standard&rotation=2026&set=30C
- [S25] Trainer Hill, tableaux d'analyses : https://tools.trainerhill.com/
