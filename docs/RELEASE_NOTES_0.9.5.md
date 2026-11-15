# PokeMind 0.9.5 — pre-release

Public statistics for your deck's archetype in Deck Lab, the PokeMind / TCG Coach card everywhere, losses first,
and your own decks in Deck Lab. Unofficial fan project by Sébastien Dubé, MIT licence.

PokeMind 0.9.4 was a release candidate that was **never published**: 0.9.5 contains every change since the public
0.9.3, listed below.

## Added
- **Deck Lab › Statistics**: public figures for the selected deck's **archetype** — not for its exact 60 cards —
  from public online Pokémon TCG Live Standard tournaments of the Limitless platform: representation, win rate and
  matchups, each with its sample size, a 95% interval, the tournaments' dates and the retrieval date. BO1 and BO3
  are never merged, byes and mirrors are excluded, and no percentage is shown below the thresholds (20 placements,
  20 matches, 10 matches for a matchup). The archetype is recognised on your PC from the Pokémon in the list,
  never from the deck's name; when it is unclear, no rate is attributed and the general public meta is shown.
  At most one automatic collection a day (shared by every deck) plus a bounded **Refresh** button; your lists
  are never sent. A collection reads one recent tournament, so samples are small: these are not worldwide
  figures.
- **Add my deck** (Deck Lab): paste the list exported from TCG Live and name it. PokeMind checks the 60 cards and
  the deck rules, says exactly why a list is refused, and never overwrites a deck. **Main deck** marks the one you
  play most: it comes first on the overview and the coach knows it.
- **Losses first**: every game still counts in your statistics, but only the opponent families that beat you are
  followed — record, number of games, dates, the cards seen in those losses, and how uncertain it is (fewer than
  5 games is a topic to watch, not a conclusion). Ask the coach « which decks do I lose to most? », « why? » or
  « how do I beat X? ».

## Changed
- **Readable ranking**: the selector puts rank and public BO1 rate before the deck name; **Ranking** lists all
  decks, with insufficient data shown explicitly. Statistics puts the public rate, sample size and period first,
  with expandable **Sources and details**. These figures describe an archetype, not your personal results.
- **Coach chat**: rounded message backgrounds keep native text selection and links.
- **The PokeMind / TCG Coach card** replaces the drawn logo: window, menu, overview, About, card binder, program
  and installer icons, shortcuts.
- **Conditional local opponent reference**: an admissible new battle can save a recent, corroborated public
  60-card reference with its source and uncertainty. This remains a hypothesis, never the opponent's exact list;
  insufficient or ambiguous evidence produces no addition. An older selected game's recovery needs an explicit
  local request; no automatic historical backfill is performed.
- **Coach sharing, said plainly**: new installs allow the cloud coach (Codex or Claude) with your anonymised
  statistics by default. The first-run wizard and **Settings → AI coach** show what is sent and let you change it;
  the full list of your main deck is sent only when your question is about a deck or a list. Raw logs, player
  names and file paths are never sent.
- `PokeMind.exe` and the installer show their version in their Windows file properties.

## Fixed
- Games pasted after a season had begun showed 0 games in « Current season »; they now count on the day their log
  was added.

## Install or update
Update from PokeMind (**Settings → Updates**), or download `PokeMind-Setup-0.9.5.exe` below and run it; it updates
an installed 0.9.x in place and keeps your data in `%LOCALAPPDATA%\PokeMind`. The installer is **not
code-signed**: if Windows shows « Windows protected your PC », choose **More info → Run anyway**. You can check
the file against `PokeMind-Setup-0.9.5.exe.sha256`.
If you already installed a local 0.9.5 candidate, the same version number may not trigger an update prompt.

---

# PokeMind 0.9.5 — préversion

Les statistiques publiques de l'archétype de ton deck dans Deck Lab, la carte PokeMind / TCG Coach partout, les
défaites d'abord, et tes propres decks dans Deck Lab. Projet de fans non officiel de Sébastien Dubé, licence MIT.

PokeMind 0.9.4 était un candidat qui n'a **jamais été publié** : la 0.9.5 contient tous les changements depuis la
0.9.3 publique, décrits ci-dessous.

- **Classement lisible** : rang et taux public BO1 précèdent le nom du deck; **Classement** liste tous les decks,
  avec les données insuffisantes explicites. Statistiques met le taux public, l'échantillon et la période en
  premier, avec **Sources et détails** repliable. Ces chiffres décrivent un archétype, pas tes résultats personnels.
- **Chat du Coach** : fonds de messages arrondis, sélection native du texte et liens conservés.
- **Deck Lab › Statistiques** : chiffres publics de l'**archétype** du deck choisi — pas de ses 60 cartes exactes —
  tirés des tournois publics en ligne Pokémon TCG Live Standard de la plateforme Limitless : représentation, taux
  de victoire et matchups, chacun avec sa taille d'échantillon, un intervalle à 95 %, les dates des tournois et la
  date de récupération. BO1 et BO3 ne sont jamais fusionnés, les byes et les miroirs sont exclus, et aucun
  pourcentage n'apparaît sous les seuils (20 placements, 20 matchs, 10 matchs pour un matchup). L'archétype est
  reconnu sur ton PC à partir des Pokémon de la liste, jamais du nom du deck; s'il est incertain, aucun taux n'est
  attribué et la méta publique générale est montrée. Au plus une collecte automatique par jour (partagée par tous
  les decks) et un bouton **Actualiser** borné; tes listes ne sont jamais envoyées. Une collecte lit un tournoi
  récent : les échantillons sont petits, ce ne sont pas des chiffres mondiaux.
- **Ajouter mon deck** (Deck Lab) : colle la liste exportée de TCG Live et nomme-la. PokeMind vérifie les 60
  cartes et les règles de construction, dit précisément pourquoi une liste est refusée et ne remplace jamais un
  deck. **Deck principal** marque celui que tu joues le plus : en tête de la vue d'ensemble et connu du coach.
- **Les défaites d'abord** : toutes les parties comptent dans tes statistiques, mais seules les familles adverses
  qui t'ont battu sont suivies (bilan, nombre de parties, dates, cartes vues dans ces défaites, incertitude; moins
  de 5 parties = sujet à surveiller, pas une conclusion). Demande au coach « contre quoi je perds le plus? »,
  « pourquoi? » ou « comment battre X? ».
- **La carte PokeMind / TCG Coach** remplace le logo dessiné : fenêtre, menu, vue d'ensemble, À propos, classeur,
  icônes du programme et de l'installateur, raccourcis.
- **Référence adverse locale conditionnelle** : une nouvelle partie admissible peut enregistrer une référence
  publique récente de 60 cartes corroborée, avec sa source et son incertitude. Elle reste une hypothèse, jamais
  la liste exacte de l'adversaire; une preuve insuffisante ou ambiguë ne produit aucun ajout. Le rattrapage d'une
  ancienne partie sélectionnée exige une demande locale explicite; aucun balayage historique automatique.
- **Partage avec le coach, dit clairement** : une nouvelle installation autorise par défaut le coach cloud
  (Codex ou Claude) avec tes statistiques anonymisées. L'assistant de premier lancement et **Réglages → Coach IA**
  montrent ce qui est envoyé et permettent de le changer; la liste complète de ton deck principal ne part que si
  ta question parle de deck ou de liste. Jamais de journal brut, de nom de joueur ni de chemin.
- **Corrigé** : les parties collées après le début d'une saison affichaient 0 partie dans « Saison actuelle »;
  elles comptent maintenant au jour où leur journal a été ajouté.
- `PokeMind.exe` et l'installateur affichent leur version dans les propriétés Windows du fichier.

Mets à jour depuis PokeMind (**Réglages → Mises à jour**) ou télécharge `PokeMind-Setup-0.9.5.exe` ci-dessous :
il met à jour une 0.9.x installée et garde tes données dans `%LOCALAPPDATA%\PokeMind`. L'installateur n'est
**pas signé** : « Informations complémentaires → Exécuter quand même ». Son SHA-256 est dans
`PokeMind-Setup-0.9.5.exe.sha256`.
Si tu as déjà installé un candidat local 0.9.5, le même numéro peut ne pas déclencher d'avis de mise à jour.
