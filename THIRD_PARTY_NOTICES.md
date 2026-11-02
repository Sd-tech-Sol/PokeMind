# Third-party notices

PokeMind uses open source components and public data. The versions below are the ones pinned in
`pyproject.toml` for the Windows build. The licence texts of the installed packages are copied into the
`licenses` folder of the program; each component's own notices take precedence. No legal certification is
claimed.

## Distributed components

| Component | Version | Licence | Use |
|---|---|---|---|
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/licenses.html), shiboken6 | 6.12.0 | LGPLv3 / GPLv3 (per module) | Desktop interface (Qt Core, Gui, Widgets) |
| [pyte](https://github.com/selectel/pyte) | 0.8.2 | LGPLv3 | Terminal screen emulation |
| [pywinpty](https://github.com/andfoy/pywinpty) (with winpty and ConPTY binaries from Windows Terminal, Microsoft) | 3.0.5 | MIT | Built-in terminal |
| [wcwidth](https://github.com/jquast/wcwidth) | 0.2.13 | MIT | Terminal character widths |
| [tzdata](https://github.com/python/tzdata) | 2026.5 | Apache-2.0 | Local dates on Windows |
| Python runtime | 3.13 | PSF License | Interpreter bundled by PyInstaller |

The Qt libraries stay as separate files in the program folder. You may replace compatible LGPL libraries
and rebuild the program from the Python source in this repository; no restriction on debugging such
modifications is added. Sources: [PySide](https://code.qt.io/cgit/pyside/pyside-setup.git/),
[Qt](https://code.qt.io/cgit/qt/qtbase.git/) — use the tag matching the distributed version.

## Build tools (not distributed as libraries)

| Tool | Version | Licence |
|---|---|---|
| [PyInstaller](https://pyinstaller.org/en/stable/license.html) | 6.22.3 | GPLv2 or later, with an exception allowing distribution of the built program |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | 6 | Inno Setup License |

## Data sources

- **Card catalogue**: [TCGdex cards-database](https://github.com/tcgdex/cards-database) (MIT), downloaded
  by the user at a pinned commit and kept locally.
- **Card images**: the public [TCGdex API and assets](https://tcgdex.dev/assets), cached locally for
  personal display; they are never included in this repository or in the installer. Card illustrations and
  trademarks © Pokémon / Nintendo / Creatures / GAME FREAK, all rights reserved. The MIT licence of the
  data repository is not presented as a licence for the illustrations.
- **Public tournament results** collected on request (Web research) keep their source URL and date.

## Engines used by the coach (not distributed)

Codex CLI, Claude Code and Ollama are installed and configured by each user under their own terms;
PokeMind only starts the copies already present on the PC.
