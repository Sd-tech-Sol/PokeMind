# Changelog

All notable public changes to PokeMind are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

This file is for people who use or read the project. The far more detailed internal log of the work lives
in `.orchestrator/DECISIONS.md`, in French.

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
