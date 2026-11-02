"""Copy installed distribution notices into the newly built portable."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys
import argparse


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, default=root / 'dist/PokeMind/licenses')
    target = parser.parse_args().destination.absolute()
    from pokemind.battle_batch import safe_path
    safe_path(root, target, exists=False)
    target.mkdir(parents=True, exist_ok=True)
    for name in ('PySide6', 'PySide6_Essentials', 'shiboken6', 'pyinstaller', 'tzdata', 'pyte', 'wcwidth', 'pywinpty'):
        dist = distribution(name)
        for entry in dist.files or []:
            if 'license' not in str(entry).casefold() and 'copying' not in str(entry).casefold():
                continue
            source = Path(dist.locate_file(entry)).resolve()
            if not source.is_file() or not source.is_relative_to(root / '.venv-desktop'):
                continue
            relative = Path(str(entry))
            if '..' in relative.parts:
                continue
            destination = target / name / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    print('desktop_notices=collected')


if __name__ == '__main__':
    main()
