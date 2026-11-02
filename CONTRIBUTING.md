# Contributing to PokeMind

Thank you for keeping the central principle intact: **no contribution may contain or require real personal
data** — no real battle log, player name, account screenshot, deck tied to a real account, secret or
personal path.

By taking part you accept the [code of conduct](CODE_OF_CONDUCT.md). PokeMind is a **pre-release**: read
the known limits in [CHANGELOG.md](CHANGELOG.md) and the README before reporting something as missing.

Issues and pull requests may be written in English or French. Public documentation is written in English,
with a French translation of the README; the internal working notes under `.orchestrator/` are in French.

## Environment and verification

On Windows 10 or 11 with Python 3.11 or later:

```powershell
.\scripts\Install-PokeMindDesktop.ps1
python scripts\local_gate.py
```

The local gate copies the repository to a temporary folder and runs compilation, a Git hygiene check, the
Qt tests and the core tests. **Never run pytest directly inside the repository**: some tests write under
`data/local`. A selection of tests (`-k`) helps while working, but only a green full run is proof.

## Building a release

```powershell
.\scripts\Build-PokeMindDesktop.ps1
.\scripts\Build-PokeMindInstaller.ps1
```

The installer script scans the program files with `scripts/scan_binary_personal_paths.py` and stops if a
build-machine path leaked. See [docs/release-checklist.md](docs/release-checklist.md).

## Test data

- Use only invented data: the fixtures in `tests/`, `scripts/qa_unified_desktop.py --prepare-release`, or a
  temporary directory created and destroyed by the test.
- Invented players, decks and logs must be obviously fictional (« Invented Family », « JoueurA »).
- Never point a test, a demo or a benchmark at a user folder or at `%LOCALAPPDATA%\PokeMind`.

## Sensitive changes

Any change to log ingestion, the data folder, the coach tools and context, the message modes, development
mode or the terminal must come with refusal tests: traversal or redirection refused, a pasted log never
reaching an engine that can run commands, no network collection without **Web research**, and no write
outside the data folder.

## Interface language

User-facing strings are written in French and wrapped in `T()`. Add the English translation as a
`French|||English` line in `src/pokemind/desktop/translations.py`; the language tests check both.

## Dependencies and publication

Dependencies are pinned in `pyproject.toml`. Any change must update
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). A local commit authorises neither signing, nor
distribution, nor publication.
