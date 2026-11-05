r"""Archive tout le dossier PokeMind de ce compte Windows dans un zip vérifié.

Fermer PokeMind d'abord.

    python scripts/archive_data.py
    python scripts/archive_data.py --help

Le dossier est %LOCALAPPDATA%\PokeMind; les archives vont dans %LOCALAPPDATA%\PokeMind-archives.
Voir src/pokemind/data_archive.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from pokemind import data_archive  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(data_archive.main('archive'))
