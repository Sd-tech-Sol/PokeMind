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

## Next
- Code signing if a publisher identity is set up (see `CODE_SIGNING.md`).

## Later
- Refresh the card catalogue to a newer TCGdex snapshot, keeping the tested one as fallback.
- Faster incremental analysis of large battle corpora.
- Confirmation in the interface before the coach writes a note or saves a deck.
- Smaller modules for the main window and the command line.
