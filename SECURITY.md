# Security policy

## Supported versions

The latest prerelease (`v0.9.3`) is supported. Security fixes are also applied to the current `main` branch.

## Reporting a vulnerability

**Never publish vulnerability details in a public issue.**

Use [GitHub private vulnerability reporting](https://github.com/Sd-tech-Sol/PokeMind/security/advisories/new).
Do not attach exploitable details to a public issue or discussion. The maintainer aims to acknowledge a
private report within 14 days, but this is a best-effort target, not a service-level guarantee.

The project is maintained by one person, with no service commitment: no fix deadline is guaranteed.

If a published prerelease must be corrected or withdrawn, the maintainer will mark the affected GitHub
release accordingly, publish the fix on `main`, and create a replacement release when appropriate.
Security details remain private until disclosure is safe.

A useful report states the version, the impact, the minimal reproduction steps **on invented data**, and
any known mitigation. Never include a real battle log, a player name, a secret, an account screenshot or a
real user path.

## Current guarantees and limits

- Personal data lives in `%LOCALAPPDATA%\PokeMind` (or the folder the user chose), outside the program
  folder. A data folder that is a redirection (junction, symbolic link) is refused.
- Nothing is sent to a cloud coach engine before the user allows it in **Settings → AI coach**. Raw logs,
  player identities and file paths are never part of the automatic context.
- A pasted battle log is text partly written by other players: it is handled by the isolated coach and
  never reaches an engine that can run commands. Content from logs, documents or API answers is treated as
  data, never as instructions.
- The message mode (Coach, Web research, Development) is chosen by the user; no word in a message starts a
  network collection or development work.
- The card catalogue is downloaded from two fixed GitHub hosts at a pinned commit, without redirects, and
  every file is checked against its Git blob hash before it is imported.
- Development mode and the built-in terminal give Codex or Claude access to the folder they run in; a
  privacy notice must be accepted first, and they are absent from an installed copy's message modes.

These controls reduce risk without being an absolute guarantee.

## Build-machine paths in binaries

A source repository can be clean while a binary built from it still embeds the account name and directory
layout of the machine that built it. PokeMind is built with PyInstaller, which stores module paths relative
to the package (`pokemind\...`), but every artifact intended for distribution is scanned anyway before it
leaves the machine:

```powershell
python scripts\scan_binary_personal_paths.py dist\PokeMind
```

The scan looks for the account name, the user profile and the repository path, in ASCII and UTF-16LE, in
every program file and inside the compressed Python archive, and fails if it finds any of them.
`Build-PokeMindInstaller.ps1` runs it before packing and stops on any finding. Do not paste raw build logs
into public issues: they contain local paths.
