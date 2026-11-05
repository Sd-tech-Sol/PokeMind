# PokeMind 0.9.2 — pre-release

Seasons, archive and restore, a reset that always works, and a coach that searches the web. Unofficial fan
project by Sébastien Dubé, MIT licence.

## Added
- **Seasons**: the overview and the battles page show the current TCG Live season by default (the Ranked Ladder
  that began on 5 November 2026 with Mega Evolution—Delta Reign), each past season, or every season together.
  A game counts in the season of the day its log was added to PokeMind. **New season…** starts one today when
  PokeMind does not know its date yet. Recommendations and learning still use every game, and say so.
- **Settings → Data → Archive…**: the Windows *Save as* dialog chooses where the zip of your data goes (Desktop,
  USB key, OneDrive…); the zip is read back entirely before it is kept, while PokeMind stays open.
- **Settings → Data → Restore…**: pick a zip with the Windows *Open* dialog; PokeMind closes, archives your
  current data next to it, puts the archive's data in place (each game stays in its season) and opens again.
- **Settings → Data → Reset…**: erase some kinds of data or everything, as on a first launch; what is removed is
  kept as a dated copy unless you untick it.

## Changed
- The coach looks in PokeMind first; Codex CLI or Claude Code search the web when the answer is missing or too
  old, and what they find is kept locally (summary, links, date). Ollama stays local.
- **Web research** shows the engine's own answer, followed by a short receipt of the bounded collection.
- The Claude Code chat uses the model chosen for Claude Code in the terminal.

## Fixed
- **Reset…** seemed to do nothing while a game was analysed or the coach was answering; it now stops that
  operation, then PokeMind closes and the reset applies.
- Imported games are analysed faster: public work is reused while no public file has changed.
- The coach can see your deck list and the result of a web research (the answer was too large and was lost).
- Deleting a discussion during an import could crash the import; **Copy diagnostic** keeps the newest lines.

## Install or update
Download `PokeMind-Setup-0.9.2.exe` below and run it; it updates an installed 0.9.0 or 0.9.1 in place and keeps
your data in `%LOCALAPPDATA%\PokeMind`. The installer is **not code-signed**: if Windows shows « Windows protected
your PC », choose **More info → Run anyway**. You can check the file against `PokeMind-Setup-0.9.2.exe.sha256`.

---

# PokeMind 0.9.2 — préversion

Saisons, archive et restauration, réinitialisation toujours possible, coach qui cherche sur le web. Projet de
fans non officiel de Sébastien Dubé, licence MIT.

- **Saisons** : Vue d'ensemble et Combats montrent par défaut la saison TCG Live actuelle (Ladder classé
  commencé le 5 novembre 2026 avec Méga-Évolution — Delta Reign), chaque saison passée, ou le cumul. Une partie
  compte dans la saison du jour où son journal a été ajouté. « Nouvelle saison… » en commence une aujourd'hui.
- **Réglages → Données → Archiver…** : la fenêtre « Enregistrer sous » de Windows choisit où va le zip de tes
  données; il est relu en entier avant d'être gardé, PokeMind restant ouvert.
- **Réglages → Données → Restaurer…** : choisis un zip; PokeMind se ferme, archive tes données actuelles à côté,
  remet celles du zip (chaque partie garde sa saison) et se rouvre.
- **Réinitialiser…** : effacer certains types de données ou tout; il ne reste plus bloqué pendant une analyse ou
  une réponse du coach.
- **Coach** : il regarde d'abord dans PokeMind, puis Codex CLI ou Claude Code cherchent sur le web au besoin et
  ce qui est trouvé est gardé sur ton PC. Il voit maintenant la liste de tes decks et le résultat d'une recherche.
- **Plus rapide** : les parties importées réutilisent le travail public tant qu'aucun fichier public n'a changé.

Télécharge `PokeMind-Setup-0.9.2.exe` ci-dessous : il met à jour une 0.9.0 ou 0.9.1 installée et garde tes
données dans `%LOCALAPPDATA%\PokeMind`. L'installateur n'est **pas signé** : « Informations complémentaires →
Exécuter quand même ». Son SHA-256 est dans `PokeMind-Setup-0.9.2.exe.sha256`.
