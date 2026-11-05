# PokeMind user guide

## First launch
A short assistant asks for your language, your coach engine and how you keep your battle logs, then offers
to download the public card catalogue (about 25 MB, one minute). You can do it later in
**Settings → Data**.

## Import your battles
In TCG Live, copy a battle log and paste it in the chat, or drop `.txt` / `.log` files on it, or use
**Attach a log**. PokeMind analyses the game, keeps it locally and never imports the same log twice. The
**Battles** page lists your games, ranks opponents by losses and shows each game as a timeline.

## Talk to the coach
Pick an engine at the top of the chat (Codex CLI, Claude Code or Ollama), then allow cloud sharing once in
**Settings → AI coach** if you use a cloud engine. The list next to **Send** chooses what a message does:

- **Coach**: looks in your local memory and the card catalogue first; with Codex or Claude, it searches the
  web only when the answer is missing or too old, then remembers what it found for next time;
- **Web research**: the engine searches the web now, even if PokeMind already knows something, plus one
  bounded collection from public sources, for that message only;
- **Development** (from the source folder only): Codex or Claude work on PokeMind's code.

**Enlarge** opens the conversation in a large window. **Stop** interrupts an answer.

## Decks and cards
**Deck Lab** keeps your 60-card lists, compares them and exports them for TCG Live. **Cards & meta** opens
an offline binder: turn the pages with ‹ ›, click a card for its French and English texts, printings and
dated legality.

## Your data
Everything is in `%LOCALAPPDATA%\PokeMind`; **Settings → Data** shows the folder. Uninstalling from Windows
Settings → Apps keeps your data. Do not open two copies of PokeMind at the same time.

To erase some of your data, or start over as on the very first launch, use **Settings → Data → Reset
PokeMind** and tick what to erase: games and statistics, my decks, discussions, knowledge (web memory, kept
research, the older local brain database), public catalogue and meta, preferences, technical files, or
**Everything**. PokeMind then closes and opens again. What is removed is kept as a dated copy
(`avant-reinitialisation-…` in the data folder) unless you untick that option; without a copy it is erased.
Removing the preferences brings the welcome assistant back.
