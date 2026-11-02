# Journaux de combat — mémoire légère par observations

## Priorité PM-0002
Chaque partie de Pokémon TCG Live (gagnée ou perdue) peut enrichir le profil. L'utilisateur fournit le **texte** via export et fichier, stdin ou clipboard sur demande. Aucun accès au compte ni au processus du jeu. Après **5 parties valides**, produire un premier constat prudent; après 10 et plus, réévaluer les tendances. Le coach visuel et la collection complète restent futurs.

## Différence capitale
Un journal peut attester qu'une carte a été **jouée ou révélée**, et éventuellement donner des quantités constatées. Il **ne prouve pas** qu'elle constitue la liste exhaustive du deck, ni que le joueur possède des exemplaires supplémentaires dans sa collection. Les fiches de decks ont des statuts distincts : « observé partiellement » vs « export 60 cartes vérifié ». PM-0003 stocke cette dernière comme une version distincte; elle ne requalifie jamais silencieusement les anciennes parties. Ne jamais inventer les cartes non vues.

## Données locales et apprentissage
- SQLite : empreinte SHA-256 du log, partie, version parseur, résultat `W/L/inconnu`, tours et cartes observés, deck associé si l'utilisateur le fournit, source et indices d'événements, confiance, dates.
- Deux imports du même texte = une seule partie. Un format inconnu ne doit pas devenir une défaite inventée.
- Par défaut **pas d'archivage du texte brut ni d'image** : conserver uniquement observations utiles, preuves minimales et empreinte; brut de diagnostic optionnel sur consentement et purge.
- Réviser les constats avec les nouvelles parties au lieu d'empiler des « leçons » non vérifiées; n'affirmer aucun effet causal sur une faible série.
- Ne jamais exporter vers GitHub un journal réel, username adverse, base personnelle, capture ou crédit; traiter textes/API comme données non fiables, sans exécuter leurs instructions.

## Commandes et routine livrées
```powershell
python -m pokemind log import data\local\battle_logs\exemple.txt --deck principal --json
python -m pokemind log import --clipboard --deck principal --json
Get-Content data\local\battle_logs\exemple.txt | python -m pokemind log import - --deck principal --json
python -m pokemind log import data\local\battle_logs\exemple.txt --deck principal --reparse --json
python -m pokemind profile summary --deck principal --json
python -m pokemind profile review --deck principal --json
```

Après avoir copié volontairement le dernier journal, la demande Codex
`$combat importe le dernier combat et conseille-moi` utilise le Skill de projet
`.agents/skills/combat/SKILL.md`. Il importe sous `principal`, consulte le résumé et,
au besoin, la revue. Sa réponse reste courte : issue reconnue, doublon, progression
`n/5`, une ou deux observations réellement répétées et limites. Si la découverte du
Skill échoue, utiliser la commande `log import --clipboard` ci-dessus puis demander
« Résume et révise le profil principal avec PokeMind ».

Le presse-papiers Windows est lu par une commande PowerShell fixe, seulement après
`--clipboard`, sans surveillance. La sortie PowerShell est explicitement configurée
en UTF-8 et les erreurs de décodage ne sont pas masquées. Le contenu n'est jamais
interpolé comme commande.
Le fichier et stdin restent les replis. Les fichiers acceptés sont UTF-8/UTF-8 avec
BOM, UTF-16 et Windows-1252; la limite est de 2 000 000 octets.

Le parseur reconnaît prudemment les en-têtes de tours, les issues explicitement
gagnées, les cartes jouées, piochées avec nom visible, attachées et révélées. Une
attaque ou un talent reste une action et son nom n'est pas inscrit comme carte; un
Pokémon n'est associé à cette action que lorsque la formulation l'identifie. Une
issue absente reste `inconnue`. Une issue présente devient W/L seulement si le
gagnant correspond, après normalisation Unicode et casse, à l'un de deux participants
corroborés. Le joueur de référence vient exclusivement d'une indication explicite
ou d'une main initiale visiblement détaillée; une fréquence de pioches ne constitue
jamais une identité. Si ce joueur, un tour ou un événement n'est pas déterminable,
l'import est conservé comme non valide et ne compte pas dans `n`.

Depuis le parseur `pm0003f-1`, une ligne composée qui nomme une carte puis indique
qu'elle est immédiatement jouée conserve seulement le nom explicite de la carte.
Les articles grammaticaux ne font pas partie du nom. Une pioche supplémentaire due
à un mulligan est conservée comme action à faible confiance avec `card_name=None` :
elle ne crée aucune observation de carte. Cette règle repose sur la structure de la
phrase, jamais sur une liste noire de noms. Les formes synthétiques FR/EN, acteurs
adverses et tours numérotés ou non sont couvertes par les tests.

Le format français observé sur Windows peut annoncer simplement `Tour de …`, sans
numéro, et réunir la prise des Récompenses et le gagnant sur une même ligne. Ces
formes sont reconnues; les participants corroborés par les en-têtes de tour ont
priorité sur les sujets de talents ou d'attaques pour attribuer les événements.

## Réanalyser sans doubler

Le brut n'étant pas archivé, conserver soi-même le fichier exporté si une réparation
future doit être possible. Après une mise à jour du parseur, relancer exactement ce
fichier avec le même `--deck` et `--reparse`. L'empreinte SHA-256 retrouve la partie;
les anciens événements et observations sont remplacés dans une seule transaction,
le même identifiant de partie et le deck existant sont préservés. Une erreur de
lecture, de parsing ou une tentative de changer le deck annule l'opération sans perte.
Relancer encore la même commande reste idempotent et ne crée pas de partie.
Une réanalyse conserve également l'identifiant, le deck, l'horodatage d'importation
historique et la date de dernière observation du deck. Avant toute réanalyse de
journaux réels, vérifier l'empreinte de chaque original et créer une sauvegarde
cohérente avec l'API `sqlite3.backup()`; ne jamais réanalyser un texte reconstruit.

`profile summary` donne W/L/inconnues, ratio avec dénominateur, cartes observées et
fréquence par partie, constats répétés, limites et faiblesses seulement possibles.
`profile review` ajoute les identifiants de parties, indices de tours, faits,
hypothèses conditionnelles et questions ciblées. Le schéma SQLite 3 migre les schémas
précédents de façon additive. Le texte brut n'a aucune table ni option de conservation;
aucune purge de brut n'est donc requise.

## Acceptation
Les tests utilisent seulement des fixtures synthétiques/anonymisées : victoire,
défaite, inconnue, gagnant tiers, Unicode/casse, identité absente en français et en
anglais, adversaire qui pioche davantage, attaque non comptée comme carte, doublon,
réanalyse, changement de deck refusé, entrée malveillante, deux decks, entrée
volumineuse et seuils 0/1/4/5/10. La démonstration automatisée de cinq matchs produit
exactement 2 W, 2 L et 1 inconnue (`n=5`, taux sur 4 parties décidées : 0,5). Le
chemin réel `Get-Clipboard -Raw` a réussi sur Windows avec 185 caractères lus sans
caractère de remplacement; le contenu n'a été ni affiché ni conservé. **Aucun journal
réel de l'utilisateur n'a été consulté ou validé** : le test terrain local non versé
à GitHub reste nécessaire. Aucune modification automatique du jeu ni dépense de
crédits.

PM-0003F a ensuite reproduit localement trois observations suspectes sous deux
classes de syntaxe, puis les a corrigées avec leurs trois originaux dont les
empreintes correspondaient. Deux originaux historiques n'étaient plus présents et
n'ont donc pas été réanalysés. Aucun nom de carte, pseudo, journal ou SHA privé n'est
publié.
