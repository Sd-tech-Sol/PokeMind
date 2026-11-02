## What this changes

<!-- What does this contribution change, and why? -->

## Checks actually run

Tick what you **actually ran**, and leave the rest unticked. An unticked box is not a reproach; a false
claim is.

- [ ] `python scripts/local_gate.py` (full run, not `-k`)
- [ ] `.\scripts\Build-PokeMindDesktop.ps1` and a manual start of `dist\PokeMind\PokeMind.exe`
- [ ] `python scripts/scan_binary_personal_paths.py dist\PokeMind`

## Data

- [ ] No real battle log, player name, account screenshot or personal path is added.
- [ ] Added tests use invented data or a temporary directory created and destroyed by the test.

## Sensitive changes

If this contribution touches log ingestion, the data folder, the coach tools or context, the message
modes, development mode or the terminal:

- [ ] Refusal tests are added: redirection or traversal refused, a pasted log never reaching an engine that
      can run commands, no network collection without Web research, no write outside the data folder.

## User-facing strings

- [ ] No new string, **or** the string is wrapped in `T()` and its English translation is added to
      `src/pokemind/desktop/translations.py`.

## Dependencies

- [ ] No dependency added, **or** `pyproject.toml` is pinned and `THIRD_PARTY_NOTICES.md` is corrected.
