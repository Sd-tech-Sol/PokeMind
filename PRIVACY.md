# Local privacy policy

PokeMind is designed to keep your data on your PC. It contains no telemetry, advertising, account or
automatic update.

## Data processed

- **Battle logs** you paste or attach from TCG Live: each log is saved as a file in your local battle-log
  folder, and PokeMind extracts the game facts (turns, cards, outcome) for its local analysis. A log already
  imported is not saved twice.
- **Decks** you save in Deck Lab, and the notes and observations of the learning loop.
- **Coach conversations**, kept locally so you can reopen them.
- **Preferences**: language, theme, coach engine, sharing choices.

## Storage

Everything is written under `%LOCALAPPDATA%\PokeMind` for an installed copy (or the folder you chose when
running from source). Uninstalling removes the program only; your data stays until you delete it yourself.

## Network

PokeMind uses the network only for these explicit actions:

- the **card catalogue** download, offered once (public TCGdex data from GitHub, about 25 MB), and its
  **updates** when you click **Update cards** (the same download, about 25 MB);
- the **update check**, at launch at most twice a day: one request to the GitHub API for the PokeMind
  releases and one for the newest TCGdex version, then, when it changed, one request to the public TCGdex
  API for the list of sets. Nothing about you is sent; GitHub and TCGdex see the request like any visit to
  a web page. Turn it off in **Settings → Updates**. Updating PokeMind downloads the installer and its
  SHA-256 from the GitHub release, checks them, and runs the installer only when you confirm;
- **card images** from the public TCGdex API, cached locally; you can turn them off in Settings;
- a message sent in **Web research** mode: one bounded collection from public sources;
- the **coach engine** you choose: Codex CLI and Claude Code run with your own account and send your
  question and the allowed context to their provider; Ollama runs locally.
- **web searches by Codex CLI or Claude Code**: when PokeMind's local memory lacks an answer, or for a
  **Web research** message, the engine searches the web and reads public pages through its provider's own
  tools. What it found is kept as a short summary with its links and date in
  `data/local/web_memory.sqlite3`, so the next similar question is answered locally. Ollama never searches
  the web.

Nothing is sent to a cloud engine until you allow it in **Settings → AI coach**, where you also choose
whether your statistics may be shared. Raw logs, player identities and file paths are never part of the
automatic context.

## Your control

You choose what to import, which engine to use and what it may receive. Conversations can be deleted from
the chat. Settings show the data folder; moving your data out of a source folder is done by copy, and the
original is never deleted by the application. **Settings → Data → Reset PokeMind** erases the kinds of data
you tick (games and statistics, decks, discussions, knowledge, public catalogue and meta, preferences,
technical files) or everything, as on a first launch; by default what is removed is kept as a dated copy
inside the data folder, and it is erased only if you untick that copy and confirm a second time.

## Limits

Battle logs contain the in-game names of the players you met. They stay on your PC, but anyone with access
to your Windows account can read the data folder. PokeMind adds no application-level encryption and relies
on the protections of your account, your disk and the operating system. A cloud coach engine is governed by
its provider's own privacy terms.
