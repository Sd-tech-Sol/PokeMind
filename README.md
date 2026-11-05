<p align="center"><img src="docs/assets/pokemind-logo.png" width="120" alt="PokeMind logo"></p>

# PokeMind

*Read this in [French / en français](README.fr.md).*

**PokeMind is a Pokémon TCG Live companion for Windows.** It remembers your battles, decks and cards on
your PC, and lets you review them with an AI coach.

> ## Status: pre-release
>
> PokeMind **0.9.2** is a public pre-release (the first one was 0.9.0). The Windows installer is **unsigned**,
> and before these releases PokeMind had been used by **its author only**. Expect defects and missing features, and keep
> your own copy of anything important.

## Author

PokeMind is an **original creation by Sébastien Dubé**. Its only borrowings are the open source
components and public data sources listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

- Author and maintainer: **Sébastien Dubé** — <https://github.com/Sd-tech-Sol>
- Licence: [MIT](LICENSE) — © 2026 Sébastien Dubé
- Decisions and project memory: [`.orchestrator/DECISIONS.md`](.orchestrator/DECISIONS.md) and
  [`PROJECT_VISION.md`](PROJECT_VISION.md)

## Download

The Windows installer is published under [GitHub Releases](https://github.com/Sd-tech-Sol/PokeMind/releases)
as `PokeMind-Setup-<version>.exe`, with its SHA-256 in `PokeMind-Setup-<version>.exe.sha256`. It installs for your account only (no administrator
rights) in `%LOCALAPPDATA%\Programs\PokeMind`, with a Start menu shortcut.

The installer is not code-signed yet: if Windows shows « Windows protected your PC », choose
**More info → Run anyway**. See [CODE_SIGNING.md](CODE_SIGNING.md).

## What PokeMind does

- **Battles**: import your TCG Live battle logs (paste them in the chat, or drop `.txt` / `.log` files).
  Every game stays on your PC; opponents are ranked by losses and each game is shown as a timeline.
- **Coach**: talk to your own **Codex CLI**, **Claude Code** or a local **Ollama** model. A list next to
  **Send** chooses what a message does: **Coach** (local memory first; Codex or Claude search the web only
  when it lacks the answer, then remember what they found), **Web research** (search the web now, plus one
  bounded public collection) or **Development** (when run from the source folder).
- **Deck Lab**: save decks, compare them, export 60-card lists to copy into TCG Live.
- **Cards & meta**: an offline card binder (French and English texts, printings, dated legality) built
  from the public TCGdex catalogue, and the tournament results saved on your PC.
- **Learning**: observations are kept with sample sizes and hypotheses are revised; no model is retrained.
- **Terminal**: Codex, Claude Code or PowerShell in a tab, inside the app.

## What PokeMind does not do

These absences are **design choices**:

- it does **not** play for you: no overlay, no bot, no click automation, and it never talks to the game
  client;
- it is **not** meant for official tournaments or anywhere the rules forbid assistance;
- it sends **nothing** to a cloud engine until you allow it in **Settings → AI coach**, and a pasted battle
  log never reaches an engine that can run commands;
- it has **no account, no telemetry and no advertising**;
- it does **not** guess win rates, credit costs or your collection when they are not known.

## Language

The interface follows Windows on first launch: a French Windows gets French, any other language gets
English. Change it at any time in **Settings → General**; your choice is remembered.

## Exact limits of version 0.9.2

| Limit | Detail |
|---|---|
| Platform | Windows 10 and 11, 64-bit. macOS and Linux are not built. |
| Distribution | The installer is **unsigned**: Windows SmartScreen shows a warning. |
| Card catalogue | A pinned public TCGdex snapshot (about 25 MB to download, 175 MB on disk); newer sets come with a later release. |
| Coach | Depends on an engine you install yourself (Codex CLI, Claude Code or Ollama) and on its own account and limits. |
| Battle analysis | Built from what the TCG Live log shows; hidden information (hand, face-down prizes) stays unknown. |
| Real-world use | Used by one person; tests run on invented data only. |
| Name | **PokeMind** is an unofficial fan project name; no trademark search was made. |

## Security and privacy

- Your data stays in `%LOCALAPPDATA%\PokeMind`, outside the program folder; uninstalling keeps it.
- Network use is explicit: the one-time card catalogue download, card images from the public TCGdex API
  (can be turned off), **Web research** messages, and the cloud coach engines you allow, which may search
  the web when local memory lacks an answer.
- Raw logs, player identities and file paths are never part of the automatic coach context.
- All data in this repository is invented; the test suite never reads a real user folder.
- Release binaries are scanned for build-machine paths before they leave the PC.

Details: [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md).

## Development prerequisites

- Windows 10 or 11, 64-bit;
- Python 3.13 (3.11 or later);
- for the installer: [Inno Setup 6](https://jrsoftware.org/isinfo.php)
  (`winget install --id JRSoftware.InnoSetup -e --scope user`);
- optional: the Windows SDK `signtool` for code signing.

## Install and verify

```powershell
.\scripts\Install-PokeMindDesktop.ps1   # creates .venv-desktop with the desktop dependencies
.\scripts\Start-PokeMindDesktop.ps1     # runs the app from source
python scripts\local_gate.py            # copies the repository to a temporary folder, then runs the full suite
```

Never run the test suite directly inside the repository: some tests write under `data/local`.
All tests run locally on Windows. The command-line brain is also available:
`python -m pokemind preflight --json`, `python -m pokemind demo --json`.

### Building a release

```powershell
.\scripts\Build-PokeMindDesktop.ps1     # builds dist\PokeMind\PokeMind.exe
.\scripts\Build-PokeMindInstaller.ps1   # scans it, then packs dist\installer\PokeMind-Setup-<version>.exe and its .sha256
```

`Build-PokeMindInstaller.ps1` fails if `scripts/scan_binary_personal_paths.py` finds the account name, the
user profile or the repository path in the program files. Code signing is optional, see
[CODE_SIGNING.md](CODE_SIGNING.md). The full list is in [docs/release-checklist.md](docs/release-checklist.md).

User guides: [English](docs/user-guide-en.md) · [French](docs/user-guide-fr.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md). One rule outranks
all the others: **no contribution may contain real personal data** — no real battle log with player
names, no screenshot of an account, no personal path.

Issues and pull requests may be written in English or French.

## AI-assisted development

PokeMind is an original project by Sébastien Dubé — idea, product vision, requirements, priorities, and
every approval and final decision are his. Development was AI-assisted: OpenAI ChatGPT was used for
architecture and independent audits, and OpenAI Codex and Anthropic Claude Code for implementation, tests,
audits, documentation and reviews, under his direction and review. No AI tool is an author, owner or
maintainer of this project, and using them implies no affiliation with, or endorsement by, OpenAI or
Anthropic. Final responsibility and maintenance rest with Sébastien Dubé. See
[AI_ASSISTANCE.md](AI_ASSISTANCE.md) for the full disclosure.

## Repository layout

Public documentation is in English, with a French translation of the README. The project's internal
working notes are kept in French: [`.orchestrator/`](.orchestrator/) (decisions, handoffs, results) and
the `docs/LOT_*` plans record how the project was built and are not required reading to use or contribute
to PokeMind. The code is in `src/pokemind/`, the tests in `tests/`, the build and QA scripts in `scripts/`.

## Legal

PokeMind is an unofficial fan project. It is not affiliated with, endorsed or sponsored by Nintendo,
The Pokémon Company, Creatures or GAME FREAK. Pokémon is a trademark of its respective owners. The PokeMind
logo is an original design. Card texts and images belong to their owners and are shown from public sources
with their attribution.

## License

[MIT](LICENSE) — © 2026 Sébastien Dubé. The card catalogue PokeMind downloads comes from
[TCGdex](https://github.com/tcgdex/cards-database) (MIT licence).
