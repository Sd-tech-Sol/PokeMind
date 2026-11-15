"""Windows version resource of PokeMind.exe (PyInstaller --version-file), from pokemind.__version__.

Explorer, the installer log and support questions then show the same version as the app and the installer.

    python scripts/make_version_info.py build/version-info.txt
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def version() -> str:
    text = (ROOT / 'src/pokemind/__init__.py').read_text(encoding='utf-8')
    found = re.search(r'^__version__ = "(\d+)\.(\d+)\.(\d+)"$', text, re.M)
    if not found:
        raise ValueError('VERSION_NOT_FOUND')
    return '.'.join(found.groups())


def version_info(value: str) -> str:
    numbers = tuple(int(part) for part in value.split('.')) + (0,)
    strings = {'CompanyName': 'PokeMind (unofficial fan project)', 'FileDescription': 'PokeMind',
               'FileVersion': value, 'InternalName': 'PokeMind', 'LegalCopyright': 'MIT licence',
               'OriginalFilename': 'PokeMind.exe', 'ProductName': 'PokeMind', 'ProductVersion': value}
    table = ',\n'.join(f"          StringStruct('{key}', '{text}')" for key, text in strings.items())
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
{table}])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    target = Path(argv[0])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(version_info(version()), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
