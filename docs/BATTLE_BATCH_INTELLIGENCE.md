# Analyse réelle d’un dossier de combats avec PokeMind

Pour le parcours courant, utiliser [le coach en une commande](BATTLE_COACH.md) :
`python -m pokemind battle coach`, puis `--update` après ajout de journaux.
Le coach retrouve lui-même le rapport canonique; aucun chemin `memory.report`
n'est à fournir. Les commandes explicites ci-dessous restent disponibles.

Pour revoir un résultat déjà conservé **sans relancer cette analyse**, utiliser
`battle batch-report --report CHEMIN_EXACT` : [guide de consultation et legacy](LEGACY_BATCH_BRIDGE.md).
Le diagnostic `battle legacy-plan` est distinct, en lecture seule, sans migration.

La commande `battle batch-intelligence` réutilise le parseur, l’Observer,
la bibliothèque PUBLIC, Deck Knowledge, Counter-Deck et Learning Loop existants.
Elle n’installe aucun service, ne touche pas au client TCG Live et n’entraîne
aucun modèle. Les connaissances restent dans PokeMind, localement.

## Sélection et exécution

Le propriétaire fournit dans **son terminal seulement** les valeurs de
`POKEMIND_BATTLE_LOGS_DIR` et `POKEMIND_PLAYER_NAME`. Ne pas les inscrire dans
un fichier versionné ou dans une requête réseau. Le dossier accepté est celui
explicitement autorisé sous `data/local/battle_logs` du projet courant; la base
est obligatoirement `data/local/pokemind.sqlite3`, sélectionnée explicitement.

```powershell
python -m pokemind battle batch-intelligence --folder "$env:POKEMIND_BATTLE_LOGS_DIR" --player "$env:POKEMIND_PLAYER_NAME" --db data/local/pokemind.sqlite3 --as-of YYYY-MM-DD --apply
```

Remplacer la date par la date d’évaluation réelle. `--json` fournit la projection
privée structurée; sans cette option, PokeMind affiche directement le rapport
dans le terminal. `--no-recommendations` donne le bilan des événements seulement.
Sans `--apply`, les journaux sélectionnés sont analysés sans import ou sauvegarde
de mémoire dérivée. Cette prévisualisation ne remplace pas une exécution réelle
explicitement autorisée.

Le nom du joueur confirmé fixe le côté de référence. Un en-tête exporté différent
est signalé, et le gagnant corroboré par les participants détermine W/L; une
référence ou un gagnant inconnu demeure `unknown`. Les tours FR/EN numérotés ou
non numérotés sont pris en charge. Deux joueurs peuvent partager un numéro de
tour. Les concaténations sont isolées aux frontières de victoire; chaque morceau
doit ensuite satisfaire les mêmes contrôles. Un morceau ambigu n’est pas importé.

## Confinement et couverture

Seuls les fichiers `.txt`/`.log`, descendants compris, du dossier choisi sont
énumérés. Limites :20 000 journaux,1GiB au total,2 000 000 octets par fichier.
L’excès total est refusé avant lecture des contenus. Liens symboliques, reparse,
jonctions, ADS, hardlinks et sorties de portée sont refusés. Chaque ouverture
vérifie l’identité et la stabilité du fichier; aucun journal source n’est modifié,
renommé, déplacé ou supprimé.

Le rapport sépare fichiers admissibles, matchs uniques, segments isolés,
doublons de texte normalisé, erreurs, issues inconnues et couverture des familles.
Un fichier peut contenir plusieurs matchs; `valid` compte les matchs uniques,
`valid_files` les fichiers ayant fourni au moins un match nouveau.
Les journaux partiels restent partiels : une carte piochée cachée ne devient
pas une observation adverse, une occurrence ne prouve pas des exemplaires
supplémentaires et un proxy PUBLIC60 n’est pas le deck exact de l’adversaire.

Les actions FR « Pokémon de joueur a utilisé… » attribuent le Pokémon au
propriétaire explicitement nommé; le nom de l’attaque n’est pas une carte.
Une ligne de marqueurs « acteur…sur Pokémon de propriétaire » conserve son
ambiguïté : le Pokémon cible n’est pas crédité comme joué par l’acteur.
Les K.O. et Récompenses restent des événements citables. L’absence d’une ligne
de Récompenses ne vaut pas zéro Récompense.

## Hypothèses de familles et recommandations

Les références PUBLIC datées et leurs noms FR/EN sont réutilisés. Le classement
privilégie les signatures Pokémon et leurs évolutions prouvées, avec une règle
de priorité fixe, plutôt que les Dresseurs communs. Les alias des fournisseurs
(par exemple suffixe `ex` ou nom d’attaque ajouté au nom d’archétype) ne créent
pas automatiquement une nouvelle famille. Il s’agit d’une hypothèse non calibrée,
jamais d’une probabilité inventée ni d’une reconstruction adverse60.

Lorsqu’aucune famille PUBLIC ne convient, une signature visible est présentée
comme telle. Une attaque avec dégâts explicitement consignés a priorité sur un
talent de moteur répété; la variante d’archétype reste non confirmée. Les métriques
séparent famille impossible à nommer et signature seule. Les regroupements ne
se font pas par pseudonyme adverse.

Un moteur d’évolution partagé ne prouve pas son attaquant habituel : si seul
le moteur est visible et qu’un autre Pokémon inflige les dégâts, PokeMind
revient à cette signature plutôt que d’affirmer la famille habituelle.

Pour chaque famille récurrente, PokeMind montre W/L/unknown/n et les événements
des défaites. Marqueurs, K.O., durée observée et course aux Récompenses sont des
indices descriptifs, pas une preuve causale ou une faute de jeu démontrée. Les
conseils restent conditionnels aux ressources, au plateau et aux textes sourcés.

Les références personnelles enregistrées exactes60 peuvent être lues même sur
un ancien schéma sain, sans migration. Elles ne sont jamais présentées comme
version jouée sans attestation. Une comparaison de cartes utilise le résolveur
existant : deux noms FR/EN ne fusionnent que si une impression unique est prouvée;
sinon les différences restent littérales et l’équivalence inconnue. Les ajouts/
retraits et le contrôle60 sont affichés pour les propositions suffisamment
définies, sans modifier le deck joué, acheter ou fabriquer de carte.

Sans version personnelle jouée attestée, les variantes proches d’une même
famille PUBLIC peuvent fournir des ajouts/retraits exacts depuis un modèle
PUBLIC explicite. Le rapport identifie les deux références et leur source;
ce protocole de test ne constitue pas un swap personnel prouvé bénéfique.

Les autres decks sont des bases à **tester**, pas des contres ou une supériorité
de matchup prouvés. Les exports PUBLIC sont reparsés à60; sources et récupération
sont conservées, auteur/date de publication non prouvés affichés `unknown`.
Légalité Standard, disponibilité Live, possession et crédits restent inconnus
si leurs preuves respectives manquent.

## Persistance sans migration silencieuse

Avant écriture en base : chemin fixe, absence de redirection/sidecars, intégrité,
FK et schéma courant compatibles. Les imports utilisent les transactions et
la déduplication existantes; les decks seulement observés ne deviennent pas des
versions personnelles attestées. Aucun ancien enregistrement n’est reparsé ou
réassigné silencieusement. Un échec d’import conserve l’analyse dérivée et son
blocage, sans retry automatique.

Base absente/incompatible/verrouillée : aucune création ou migration silencieuse,
aucune nouvelle sauvegarde. L’analyse des journaux continue et les sorties privées
sont conservées sous `data/local/battle-intelligence` : JSON, texte et journal
Learning Loop. Les faits observés, statistiques et hypothèses sont séparés.
Les instantanés sont immuables et dédupliqués par contenu; une reprise identique
ne duplique pas la mémoire. Les fichiers de présentation par date/version sont
créés sans écraser l’existant. Le chemin canonique retourné dans `memory` désigne
toujours le résultat de l’appel.

Une correction de parseur/classification peut réviser explicitement l’hypothèse
précédente, avec motif et référence, tout en préservant le premier instantané.
Les vieux faits ne sont ni supprimés ni transformés en conclusions nouvelles.

## Recherche PUBLIC distincte

```powershell
python -m pokemind battle batch-intelligence --folder "$env:POKEMIND_BATTLE_LOGS_DIR" --player "$env:POKEMIND_PLAYER_NAME" --db data/local/pokemind.sqlite3 --as-of YYYY-MM-DD --apply --refresh-public
```

L’API de recherche ne reçoit **aucun** joueur, journal, deck privé ou statistique.
Elle consulte des endpoints PUBLIC tirés du catalogue/bibliothèque admissibles,
des ressources officielles fixes et du répertoire public d’archétypes. Priorité
aux sources Pokémon officielles, puis cartes TCGdex et listes Limitless.
Les pages HTML respectent robots; l’accès JSON est celui de l’API publique.
User-Agent déclaré, cadence bornée, redirects refusés et aucune protection
contournée. Aucun login, paywall, compte ou presse-papiers.

Enveloppe :150GET,32MiB de corps,2MiB par réponse. Chaque réservation de requête
est durable avant réseau. Refus, challenge ou erreur ferme l’hôte, sans retry;
une enveloppe fermée/incomplète n’est jamais redémarrée. Un blocage réseau ne
supprime pas l’analyse locale. Le journal d’endpoints, les corps PUBLIC et les
faits sourcés restent dans la campagne locale; un index explicite permet de les
réutiliser hors ligne au prochain lancement, sans découverte de dossiers.
Les nouvelles assertions officielles restent non vérifiées jusqu’à corroboration;
un texte de carte descriptif n’est pas une certification des règles actuelles.

## Validation et limites

Les tests créent uniquement des dossiers, identités et journaux inventés.
Collecter les modules de tests par chemins littéraux, sans conftest/découverte
locale; la CI GitHub isolée exécute la suite complète Windows/Ubuntu.
La CI certifie ces tests, pas les opérations privées du PC.

Ne jamais pousser rapports privés, journaux, bases, pseudos, noms de fichiers
personnels, chemins absolus ou empreintes privées. GitHub reçoit code, tests
inventés, guides et preuves assainies seulement. **V1 NOT_RELEASE_READY**;
après livraison et CI au SHA final : **AWAITING_AUDIT**, audit indépendant.
