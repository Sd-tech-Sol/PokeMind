# Changelog

All notable public changes to PokeMind are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

This file is for people who use or read the project. The far more detailed internal log of the work lives
in `.orchestrator/DECISIONS.md`, in French.

## [0.9.2] — 2026-11-05

### Added

- **Settings → Data → Reset PokeMind**: tick the kinds of data to erase (games and statistics, decks,
  discussions, knowledge, public catalogue and meta, preferences, technical files) or everything, as on a
  first launch; PokeMind then closes and opens again. What is removed is kept as a dated copy unless you
  untick it; nothing is erased if a file is still in use.
- **Seasons**: the overview and the battles page show the current TCG Live season by default (the Ranked
  Ladder that began on 5 November 2026 with Mega Evolution—Delta Reign), each past season, or every season
  together. A game counts in the season of the day its log was added to PokeMind. **New season…** starts
  one today when PokeMind does not know its date yet. The coach gets the season shown and the totals of
  each season.
- **Settings → Data → Archive my data**: the Windows *Save as* dialog chooses where the zip goes (Desktop,
  a USB key, OneDrive…); the zip is read back entirely before it is kept, while PokeMind stays open.
  **Restore an archive** picks a zip with the Windows *Open* dialog; PokeMind closes, archives your current
  data next to the chosen zip, puts the archive's data in place with each file's date (each game stays in
  its season), and opens again.
- `scripts/archive_data.py`, `scripts/reset_data.py` and `scripts/restore_data.py`: the same for the whole
  PokeMind folder of this Windows account, for troubleshooting with PokeMind closed.

### Fixed

- Deleting a discussion while a game log was being imported could crash the import at its end; the delete
  buttons now wait for the import, and a report always finds a place in the discussion.
- **Copy diagnostic** kept the oldest of its lines and cut the newest ones; it now keeps the newest and lists
  the recent errors first.
- The battle analysis no longer rebuilds the same public tournament sample and deck guides for each of its
  counter-deck plans, which made each imported game take much longer to analyse.
- The coach could not see the list of decks, nor the result of a web research: the whole answer was over the
  size a tool may return, so it got an error instead. It now gets every deck name with a number, and asks
  for one deck's full list by that number; a long answer is shortened instead of lost.
- After the first analysis of a session, the next imported games reuse the public families and the
  counter-deck plans while no public file has changed, instead of rebuilding them each time.
- **Reset…** seemed to do nothing while a game was being analysed or the coach was answering (only a short
  line in the status bar); it now stops that operation, then PokeMind closes and the reset applies. When a
  file still blocks it, the message names it.

### Changed

- The coach looks in PokeMind first, and Codex CLI or Claude Code now search the web when the answer is
  missing or too old; what they find is kept locally (summary, links, date) so a similar question is
  answered without searching again. Ollama stays local.
- **Web research** shows the engine's own answer, followed by a short PokeMind receipt of the bounded
  collection, instead of replacing the answer with the receipt.
- The Claude Code chat uses the model chosen for Claude Code in the terminal.

## [0.9.1] — 2026-11-03

### Fixed

- Deck validation now enforces one ACE SPEC card and one Radiant Pokémon per deck; a list breaking either
  rule is no longer reported as valid, and the coach cannot save it.
- The coach can save a validated deck to **My decks** when asked, without needing exact wording.

### Changed

- While battles are read or analysed, a large banner with a progress bar sits above every page, and empty
  numbers show « … » instead of zeros.
- Chat: tool calls appear as one short line (« Tools · cards ×3 · deck check »), and answers render headings,
  lists, tables and code blocks with a more readable font.

### Added

- **Delete all** in the chat history, after one confirmation.

## [0.9.0] — 2026-11-02 — first public pre-release

### Added

- Windows installer (Inno Setup) for the current account only, with a Start menu shortcut; uninstalling
  keeps the data in `%LOCALAPPDATA%\PokeMind`.
- Standalone mode: an installed copy needs no project folder and offers a one-time download of the public
  TCGdex card catalogue (French and English, about 25 MB), checked file by file.
- First-run welcome assistant (language, coach engine, battle-log habits, catalogue).
- Message mode next to **Send**: Coach, Web research (one bounded public collection) or Development.
- Coach engines: Codex CLI, Claude Code or a local Ollama model, with the same PokeMind tools (cards, dated
  legality, 60-card validation, saved decks).
- Battles page, statistics charts, card binder, Learning page and a built-in terminal.
- Optional code signing of the program, the installer and the uninstaller.
- Public repository files: `README.fr.md`, `AI_ASSISTANCE.md`, `SECURITY.md`, `PRIVACY.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CODE_SIGNING.md`, user guides in English and French, a release
  checklist, issue and pull request templates.
- The installer build writes `PokeMind-Setup-<version>.exe.sha256` next to the installer.

### Changed

- The coach receives a smaller context: the families named in the question and the 15 that beat you most,
  and within one engine session only what changed since the previous message.
- Interface language follows Windows on first launch (French for a French Windows, English otherwise).
- Original logo (two cards and a brain).

### Security

- Personal data lives outside the program and source folders; a redirected data folder is refused.
- No word in a message starts a network collection or development work; a pasted log never reaches an
  engine that can run commands.
- Release binaries are scanned for build-machine paths before packing
  (`scripts/scan_binary_personal_paths.py`, also inside the Python archive); the build stops on a match.

### Known limits

- The installer is unsigned (SmartScreen warning).
- The card catalogue is a pinned snapshot; newer sets come with a later release.
- Used by one person; tested on invented data only.
