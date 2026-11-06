# ROADMAP.md — Roadmap

This roadmap states intentions, not promises. The detailed plan and its current step are in
`.orchestrator/NEXT_ACTION.md` (in French).

## Done — 0.9.0 pre-release (source and local installer)
- Local battle memory, statistics, Deck Lab, card binder, Learning page, built-in terminal.
- Coach with Codex CLI, Claude Code or Ollama and shared PokeMind tools.
- Explicit message mode, smaller coach context.
- Standalone installed copy with a verified card catalogue download.

## Done — 0.9.1 pre-release
- Public repository with GitHub prereleases (installer and its SHA-256).
- One ACE SPEC card and one Radiant Pokémon per deck enforced; the coach saves validated decks on request.
- Visible loading banner, « Delete all » discussions, cleaner chat rendering.

## Done — 0.9.2 pre-release
- TCG Live seasons: current season, each past season, or every season together.
- Archive and restore your data from Settings, and a reset that never stays blocked.
- The coach searches the web when its local memory lacks an answer, and keeps what it found.

## Done — 0.9.3 pre-release
- One-click updates: new TCGdex cards without restarting, and new PokeMind versions installed from
  the app with their SHA-256 checked; the first catalogue comes from the newest TCGdex version.
- BrainBall colours for the dark and light themes, with WCAG AA contrast.

## Next
- Code signing if a publisher identity is set up (see `CODE_SIGNING.md`).

## Later
- Faster incremental analysis of large battle corpora.
- Confirmation in the interface before the coach writes a note or saves a deck.
- Smaller modules for the main window and the command line.
