# PokeMind 0.9.4 — pre-release

> **Never published.** This release candidate was folded into 0.9.5: see `RELEASE_NOTES_0.9.5.md`.

The PokeMind / TCG Coach card everywhere, losses first, and your own decks in Deck Lab.
Unofficial fan project by Sébastien Dubé, MIT licence.

## Added
- **Add my deck** (Deck Lab): paste the list exported from TCG Live and name it. PokeMind checks the 60 cards and
  the deck rules, says exactly why a list is refused, and never overwrites a deck. **Main deck** marks the one you
  play most: it comes first on the overview and the coach knows it.
- **Losses first**: every game still counts in your statistics, but only the opponent families that beat you are
  followed — record, number of games, dates, the cards seen in those losses, and how uncertain it is (fewer than
  5 games is a topic to watch, not a conclusion). Ask the coach « which decks do I lose to most? », « why? » or
  « how do I beat X? ».

## Changed
- **The PokeMind / TCG Coach card** replaces the drawn logo: window, menu, overview, About, card binder, program
  and installer icons, shortcuts.
- **A pasted battle log never saves the opponent's deck** by itself, after a win or a loss. The coach saves a deck
  only when you ask for it.
- **Coach sharing, said plainly**: new installs allow the cloud coach (Codex or Claude) with your anonymised
  statistics by default. The first-run wizard and **Settings → AI coach** show what is sent and let you change it;
  the full list of your main deck is sent only when your question is about a deck or a list. Raw logs, player
  names and file paths are never sent.
- `PokeMind.exe` and the installer show their version in their Windows file properties.

## Fixed
- Games pasted after a season had begun showed 0 games in « Current season »; they now count on the day their log
  was added.

## Install or update
Update from PokeMind (**Settings → Updates**), or download `PokeMind-Setup-0.9.4.exe` below and run it; it updates
an installed 0.9.x in place and keeps your data in `%LOCALAPPDATA%\PokeMind`. The installer is **not
code-signed**: if Windows shows « Windows protected your PC », choose **More info → Run anyway**. You can check
the file against `PokeMind-Setup-0.9.4.exe.sha256`.

---

# PokeMind 0.9.4 — préversion

La carte PokeMind / TCG Coach partout, les défaites d'abord, et tes propres decks dans Deck Lab.
Projet de fans non officiel de Sébastien Dubé, licence MIT.

- **Ajouter mon deck** (Deck Lab) : colle la liste exportée de TCG Live et nomme-la. PokeMind vérifie les 60
  cartes et les règles de construction, dit précisément pourquoi une liste est refusée et ne remplace jamais un
  deck. **Deck principal** marque celui que tu joues le plus : en tête de la vue d'ensemble et connu du coach.
- **Les défaites d'abord** : toutes les parties comptent dans tes statistiques, mais seules les familles adverses
  qui t'ont battu sont suivies (bilan, nombre de parties, dates, cartes vues dans ces défaites, incertitude; moins
  de 5 parties = sujet à surveiller, pas une conclusion). Demande au coach « contre quoi je perds le plus? »,
  « pourquoi? » ou « comment battre X? ».
- **La carte PokeMind / TCG Coach** remplace le logo dessiné : fenêtre, menu, vue d'ensemble, À propos, classeur,
  icônes du programme et de l'installateur, raccourcis.
- **Un journal collé n'enregistre jamais le deck adverse** tout seul, après une victoire comme après une défaite.
  Le coach enregistre un deck seulement si tu le demandes.
- **Partage avec le coach, dit clairement** : une nouvelle installation autorise par défaut le coach cloud
  (Codex ou Claude) avec tes statistiques anonymisées. L'assistant de premier lancement et **Réglages → Coach IA**
  montrent ce qui est envoyé et permettent de le changer; la liste complète de ton deck principal ne part que si
  ta question parle de deck ou de liste. Jamais de journal brut, de nom de joueur ni de chemin.
- **Corrigé** : les parties collées après le début d'une saison affichaient 0 partie dans « Saison actuelle »;
  elles comptent maintenant au jour où leur journal a été ajouté.
- `PokeMind.exe` et l'installateur affichent leur version dans les propriétés Windows du fichier.

Mets à jour depuis PokeMind (**Réglages → Mises à jour**) ou télécharge `PokeMind-Setup-0.9.4.exe` ci-dessous :
il met à jour une 0.9.x installée et garde tes données dans `%LOCALAPPDATA%\PokeMind`. L'installateur n'est
**pas signé** : « Informations complémentaires → Exécuter quand même ». Son SHA-256 est dans
`PokeMind-Setup-0.9.4.exe.sha256`.
