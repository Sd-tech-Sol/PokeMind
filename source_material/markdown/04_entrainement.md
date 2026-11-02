# VOLUME 4 — ENTRAÎNEMENT, ANALYTIQUE ET PARCOURS VERS L'EXCELLENCE

**Encyclopédie compétitive Pokémon TCG Live**  
**Programme de 90 jours, formulaires d'analyse et exercices | 9 octobre 2026**

> La progression compétitive se bâtit par cycles : jouer, documenter, expliquer, corriger, retester. Aucun PDF, aucune liste de cartes et aucune IA ne peuvent garantir de devenir « le meilleur ». Ce manuel fournit un système contrôlable pour augmenter la qualité du jeu.

## 1. Construire un dispositif d'entraînement, pas un simple historique de victoires

Les meilleurs signaux ne sont pas tous visibles dans le résultat. Une partie gagnée peut contenir deux erreurs graves que l'adversaire n'a pas punies. Une partie perdue peut avoir été jouée correctement compte tenu des tirages. Il faut donc enregistrer à la fois **le résultat**, **le contexte** et **la qualité des décisions**.

Chaque séance doit posséder un objectif limité : ouvertures, calcul des Récompenses, séquence de pioche/recherche, gestion du Banc, plan d'affrontement, ou résilience sous perturbation. Le problème des longues sessions de classement sans objectif est qu'elles entraînent autant les mauvais automatismes que les bons.

**Routine efficace de 60 minutes** : 10 minutes de lecture/revue de deux scénarios; 35 minutes de parties; 10 minutes de revue du journal du dernier match; 5 minutes de synthèse d'un seul comportement à améliorer lors de la prochaine séance. Une séance plus longue n'est pas nécessairement meilleure si la qualité des décisions diminue.

## 2. Construire son tableau de bord de partie

Pour chaque partie, saisir les données ci-dessous immédiatement après le match :

| Champ | Exemple/consigne |
|---|---|
| Date et format | 2026-10-09, Standard 30C |
| Version du deck | Dragapult_v03, liste enregistrée |
| Adversaire | Catégorie observée, p. ex. Basic Box |
| Initiative | Premier ou deuxième |
| Résultat | Gagné / perdu / nul si le mode le prévoit |
| Cause principale | Mauvais sequencing / prizes / ressources / hasard / autre |
| Tour critique | Tour 3, Supporter joué trop tôt |
| Options réellement disponibles | Ligne A, ligne B, outs connus |
| Carte ou interaction à vérifier | Référence précise et lien de carte |
| Meilleur correctif testable | Retarder l'attachement, compter les outs |

La fonction de statistiques de l'éditeur TCG Live peut fournir victoire/défaite par deck; les journaux de combat exportés apportent davantage de détails sur l'exécution. Ne suppose pas que ces données sont complètes ni qu'elles se synchronisent avec ton carnet de suivi externe. [S07][S10]

## 3. Analyse post-partie en sept questions

1. Quel était mon **plan de Récompenses** après mon premier tour utile?
2. À quel tour avais-je une ligne de victoire plausible et qu'est-ce qui me manquait?
3. Quelle action irréversible ai-je faite avant d'avoir consulté une information gratuite?
4. Est-ce que j'ai posé un Pokémon de soutien qui n'était pas nécessaire pour gagner?
5. Quelle carte de l'adversaire aurait le mieux puni mon terrain final?
6. Est-ce que ma décision était mauvaise au moment où je l'ai prise, ou seulement malchanceuse dans son résultat?
7. Quelle seule règle concrète essayerai-je au prochain match comparable?

**Classement des erreurs** : A = erreur qui change presque sûrement l'issue; B = erreur qui réduit clairement les chances; C = erreur mineure ou amélioration possible; N = événement non contrôlable. Une fin de partie malchanceuse ne justifie pas d'inventer une erreur A. Inversement, un beau résultat ne fait pas disparaître une erreur B.

## 4. Statistiques : éviter les conclusions abusives

Le taux de victoire empirique est `victoires / parties` si on ne joue que des parties gagnées/perdues. Pour les nuls, préciser si on les ignore, les compte comme un demi-point ou les traite séparément. Écrire la convention, puis l'appliquer de façon constante.

**Incertitude de l'échantillon.** Sur 20 matchs à 60 % (12 victoires), un succès de trois parties de suite peut faire osciller énormément la proportion. Sur 200 matchs, le pourcentage se stabilise davantage, mais il peut encore varier selon les adversaires. Une approximation de l'écart-type du taux observé est `sqrt(p*(1-p)/n)`; à p = 0,5 et n = 100, elle vaut 5 points de pourcentage environ. Ce n'est qu'une approximation et non une garantie de résultats futurs.

**Décomposer avant de conclure** : total; vs les trois meilleurs decks; premier/deuxième tour; nombre de modifications de la liste; nombre d'erreurs majeures. Un deck passant de 55 % à 45 % peut simplement avoir rencontré davantage de ses mauvais affrontements.

**Biais classiques.** Biais du survivant (on regarde seulement les decks gagnants); biais de sélection (tes adversaires changent avec ton rang); biais de récence (la dernière défaite paraît plus importante); biais de causalité (une nouvelle carte coïncide avec plus de victoires sans en être la cause).

## 5. Exploiter les journaux de bataille sans automatisation fragile

Le journal de combat de TCG Live se récupère depuis l'interface de résultats lorsqu'il est proposé. Conserver le texte original localement, classé par date et version de liste. Créer ensuite un court résumé manuel ou assisté par IA : tours pertinents, ressources dépensées, moment où un K.-O. supplémentaire devenait possible, et décision alternative. [S10]

**Important** : le log ne contient pas forcément toutes les informations cachées au moment de la décision. Une IA qui voit une carte piochée trois tours plus tard risque de suggérer rétrospectivement un plan impossible à connaître. Toute revue doit respecter l'**information disponible à l'instant exact**. Ne jamais utiliser un moteur qui voit des éléments privés non divulgués pendant une partie contre des joueurs en direct ou des logiciels non autorisés.

**Gabarit d'instruction d'analyse** : « Tu es un entraîneur de TCG. Voici une partie dont j'ai retiré les identifiants. Pour chaque tour, distingue cartes visibles, cartes probables et cartes inconnues. Trouve au maximum trois erreurs contrôlables; cite la séquence d'actions et explique deux lignes légales possibles sans utiliser l'information révélée plus tard. Si une règle ou un texte de carte n'est pas certain, marque-le à vérifier. »

## 6. Programme de 90 jours

### Phase I — Jours 1 à 14 : règles, ouverture et précision

**Objectifs** : lire les textes sans erreurs, répéter la mise en place, reconnaître les contraintes des cartes, terminer chaque tour avec les actions principales accomplies. **Travail** : 20 minutes quotidiennes de théorie et 2 à 4 parties à objectif spécifique. **Mesure** : erreurs d'attachement, de Supporter, de retraite et de cibles injustifiées par tranche de dix parties. **Livrable** : une version de deck fixe et quinze parties documentées.

### Phase II — Jours 15 à 30 : maîtriser une liste

**Objectifs** : savoir les quantités des cartes du noyau, les outs initiaux et les transitions vers les attaquants. **Travail** : 20 parties sans modifier le deck; revue détaillée de cinq défaites; étude de la liste de référence et de deux variantes. **Mesure** : premier tour utile d'attaque, fréquence des mains bloquées, qualité des séquences. **Livrable** : une fiche de chaque carte et de sa fonction.

### Phase III — Jours 31 à 45 : parcours de Récompenses

**Objectifs** : annoncer le chemin à six Récompenses au tour 2 et l'actualiser après une nouvelle révélation. **Travail** : écrire l'ordre théorique des K.-O. pour chaque partie; revoir trois erreurs de gust et d'attaquant; vérifier la position des cartes Récompense pendant les recherches. **Mesure** : erreurs de ciblage et parties perdues à une Récompense du gain.

### Phase IV — Jours 46 à 60 : matchups

**Objectifs** : connaître trois affrontements très répandus à fond et disposer d'un plan initial et d'un plan de secours. **Travail** : cinq parties ciblées par archetype si possible, lecture des listes récentes, trois séances où tu joues le deck adverse pour comprendre ses difficultés. **Mesure** : taux de victoire par matchup avec incertitude, non seul taux global.

### Phase V — Jours 61 à 75 : prise de décision sous pression

**Objectifs** : prendre les décisions principales plus vite sans cliquer aveuglément; rester lucide après un tirage difficile. **Travail** : enregistrer le temps d'analyse de trois tours clés, résoudre des puzzles de position et jouer des sessions de pratique avec objectif. **Mesure** : nombre d'erreurs irréversibles et de tours ratés, y compris dans les victoires.

### Phase VI — Jours 76 à 90 : préparation compétitive

**Objectifs** : figer une liste solide, savoir la défendre, planifier une journée de tournoi et reconnaître les lignes qui exigent un pari. **Travail** : simuler un petit tournoi, jouer des adversaires variés, revoir trois meilleures parties et trois pires, définir une routine pré-match. **Mesure** : stabilité du jeu, cohérence des décisions et mise en pratique des correctifs.

## 7. Préparer un tournoi en ligne

Les tournois en ligne de Play! Limitless utilisent leurs propres règles, inscriptions, horaires, limitations de communication et méthodes de preuve. Lire la page du tournoi précis avant de s'inscrire; ne suppose pas que les règles du classement Live sont identiques. [S18]

**J-7** : confirmer le format, la date de légalité, et choisir un deck. **J-3** : vérifier les listes dominantes et tester deux mauvais matchups. **J-1** : ne plus faire de changements importants non validés; sauvegarder la liste et vérifier le client. **Jour J** : stabilité réseau, batterie/charge, interruptions, environnement calme, procédures de match. **Après** : noter les décisions, pas seulement les résultats.

Le tournoi sur table Play! Pokémon ajoute des règles de rythme, de comportement, de matériel et de résolution de litiges. Lire les documents officiels du bon format; ce PDF ne remplace pas le manuel d'arbitrage ni les règlements de l'organisateur. [S02]

## 8. Plan de révision du méta

**Hebdomadaire :** collecter les cinq meilleurs decks, part de présence, résultat et date; lire au moins une nouvelle decklist complète; vérifier trois cartes de réponse. **Mensuel :** figer un snapshot, calculer les taux de victoire par matchup sur ton propre échantillon, supprimer un correctif qui n'apporte aucun gain. **À chaque extension/rotation :** valider la légalité, mettre de côté les anciens chiffres, repartir sur un journal versionné.

**Source de vérité personnelle** : une feuille de calcul ou un simple fichier CSV de matchs, un dossier contenant les textes de journaux exportés et les decklists importables datées. Aucun nouveau logiciel n'est nécessaire pour commencer. Un tableur avec filtres couvre l'essentiel.

## 9. Une IA comme entraîneur, pas comme oracle

Les modèles de langage sont utiles pour classifier des erreurs, proposer des scénarios de pratique, résumer les matchups, expliquer les probabilités et comparer des variantes de listes. Mais ils peuvent inventer un effet de carte, confondre un ancien format, mélanger TCG Live et Pocket ou surestimer des chiffres sans connaître le filtre exact.

**Contrôle qualité** : exiger le nom, l'édition ou le numéro de la carte lorsqu'une décision dépend d'un texte particulier; croiser l'affirmation avec le Card Dex officiel; conserver les liens vers les résultats; demander à l'IA de nommer ce qu'elle ignore. Elle ne doit pas automatiser le client, contourner les règlements, lire la main adverse ou donner des conseils fondés sur de l'information cachée.

**Prompts d'entraînement utiles** :

> « Joue le rôle d'un arbitre pédagogique. Crée dix situations qui mélangent évolution, retraite, changement, Énergie et Récompenses. Donne la solution seulement après ma tentative, puis indique la source de règle à vérifier. »

> « Voici mon journal anonymisé. Réécris les décisions critiques à l'instant où elles ont eu lieu. Montre pour chacune l'information connue et les risques de deux lignes. Ne lis pas le futur et n'invente pas le texte des cartes. »

> « Voici deux listes vérifiées au même format. Identifie les cartes communes et les différences; formule au plus trois hypothèses testables sur leurs matchups sans prétendre que les résultats de tournoi prouvent la causalité. »

## 10. Banque d'exercices appliqués

<!-- EXERCICES INSÉRÉS DANS LA VERSION FINALE -->

## 11. Une grille de compétences, à noter sans complaisance

Noter de **0 à 4** chaque dimension : **0 = ne sait pas faire**, **1 = réussit avec aide**, **2 = réussit souvent**, **3 = fiable contre opposition réelle**, **4 = peut l'expliquer et se corriger**.

| Compétence | Preuve observable |
|---|---|
| Règles et textes | Peu ou pas de décisions illégales confondues |
| Séquence des actions | Les engagements irréversibles sont justifiés |
| Cartes Récompense | Route initiale et route de secours écrites |
| Gestion des ressources | Pas de carte unique sacrifiée sans analyse |
| Lecture adverse | Hypothèses mises à jour avec les révélations |
| Matchups | Plans testés contre les archétypes populaires |
| Probabilités | Les outs sont comptés sans double comptage |
| Gestion du Banc | Chaque Pokémon posé a une fonction |
| Résilience | Peu de tilt, correction après erreur |
| Mise à jour du deck | Les changements suivent une hypothèse et un test |

**Interprétation** : n'améliorer qu'une ou deux dimensions prioritaires pendant une semaine. Une moyenne de 3/4 n'a aucune valeur si la gestion des Récompenses demeure à 1/4 et coûte systématiquement des matchs.

## 12. Mini-examen final : dix problèmes

**P1.** Ton deck a quatre copies d'une carte, quelle est la probabilité approximative d'en voir au moins une en sept cartes initiales, sans condition de mulligan? **P2.** Une carte unique est dans tes six Récompenses initiales : quelle était sa probabilité a priori? **P3.** Tu as trois Récompenses restantes et vois un Méga-ex adverse atteignable; que dois-tu vérifier avant de viser ce Pokémon? **P4.** Tu peux faire un K.-O. sur un Pokémon à une Récompense ou détruire le support à deux Récompenses; dans quelles conditions le second est-il préférable? **P5.** Une séquence de recherche te ferait voir la composition du deck avant une pioche; quels avantages en tirer? **P6.** Pourquoi comparer le taux de victoire de deux decks sans nombre de matchs est-il trompeur? **P7.** Un attaquant à une Récompense peut-il être meilleur qu'un ex sur le tour courant? **P8.** Quel est le danger d'avoir cinq Pokémon au Banc quand l'adversaire joue du gust? **P9.** Comment empêcher l'IA d'utiliser la connaissance du futur dans une analyse? **P10.** Pourquoi un résultat de tournoi du mois dernier ne prouve-t-il pas que la liste est optimale aujourd'hui?

**Corrigé.** P1 ~39,95 %; P2 10 %; P3 légalité/effets, quantité de dégâts, nombre de Récompenses, réponse adverse; P4 gain de tempo ou parcours de Récompenses supérieur, avec riposte soutenable; P5 estimation des Récompenses, cibles de recherche, conservation des outs; P6 échantillon, incertitude et contexte; P7 oui si meilleur échange ou meilleur tempo; P8 absence de place et cibles vulnérables; P9 figer l'information disponible tour par tour; P10 rotations, nouvelles listes, nouvelle population et variance.

## 13. Contrat personnel d'amélioration

**Je n'attribue pas automatiquement une défaite à la chance.** Je cherche d'abord les choix contrôlables, mais je reconnais quand le meilleur coup a perdu. **Je ne modifie pas ma liste après chaque défaite.** Je change uniquement une variable liée à un problème documenté. **Je ne copie pas une liste sans comprendre son plan.** **Je n'utilise pas une statistique sans contexte.** **Je sais ce que je veux faire avant de cliquer.**

Réévaluer ces engagements chaque fin de semaine et ajouter un seul nouvel exercice si une lacune persiste. C'est une discipline de progression mesurable, pas une promesse de classement.

## Sources du volume 4

- [S02] Documents officiels de tournoi Play! Pokémon : https://play.pokemon.com/en-ca/resources/documents/
- [S07] Pokémon, nouveautés du Deck Editor et statistiques : https://www.pokemon.com/us/pokemon-news/celebrate-play-pokemon-with-pokemon-tcg-lives-mid-year-event
- [S10] Pokémon, fonction Battle Log : https://community.pokemon.com/en-us/discussion/9496/letter-to-the-community-feb-20-2024
- [S11] Pokémon TCG Live Learning Lab : https://support.pokemon.com/hc/en-us/articles/45562128423444-Pok%C3%A9mon-TCG-Live-Learning-Lab-FAQ
- [S18] Plateforme de tournois Play! Limitless : https://play.limitlesstcg.com/
- [S25] Trainer Hill (analytique) : https://tools.trainerhill.com/
- [S26] Pokémon, base officielle de cartes : https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/
