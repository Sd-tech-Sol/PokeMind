"""Fail if a distribution contains the build machine's account name, user profile or repository path.

    python scripts/scan_binary_personal_paths.py dist/PokeMind [--require-archive]

Every file is searched in ASCII and UTF-16LE, case-insensitively. With PyInstaller installed (the
.venv-desktop build environment), the archive appended to PokeMind.exe is opened too and the source path
of every compiled module is checked. Findings name the file and the kind of match, never the matched text.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def needles(root=ROOT):
    """What would identify the build machine: account name, user profile and repository path."""
    found = {'account-name': os.environ.get('USERNAME', ''), 'user-profile': os.environ.get('USERPROFILE', ''),
             'repository-path': str(root)}
    return {kind: value for kind, value in found.items() if len(value) >= 4}


def _code_paths(code):
    yield code.co_filename
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            yield from _code_paths(constant)


def _archive_findings(executable, terms):
    """Source paths of the modules inside a PyInstaller executable; None when PyInstaller is unavailable."""
    try:
        from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader
    except ImportError:
        return None, 0
    findings, modules = set(), 0
    try:
        archive = CArchiveReader(str(executable))
    except Exception:  # not a PyInstaller executable
        return findings, modules
    for entry in archive.toc:
        data = archive.extract(entry)
        if not isinstance(data, bytes):
            continue
        if entry.endswith('.pyz'):
            with tempfile.TemporaryDirectory() as folder:
                copy = Path(folder) / 'archive.pyz'
                copy.write_bytes(data)
                package = ZlibArchiveReader(str(copy))
                for name in package.toc:
                    try:
                        code = package.extract(name)
                    except Exception:
                        continue
                    if isinstance(code, types.CodeType):
                        modules += 1
                        paths = ' '.join(_code_paths(code)).casefold()
                        findings |= {kind for kind, term in terms.items() if term.casefold() in paths}
        else:
            findings |= {kind for kind, term in terms.items() if term.casefold().encode('utf-8', 'ignore') in data.lower()}
    return findings, modules


def scan(folder, terms):
    folder = Path(folder)
    findings, files, modules, archive_checked = [], 0, 0, False
    encoded = [(kind, encoding, term.casefold().encode(encoding, 'ignore'))
               for kind, term in terms.items() for encoding in ('ascii', 'utf-16-le')]
    for path in sorted(p for p in folder.rglob('*') if p.is_file()):
        files += 1
        data = path.read_bytes().lower()
        relative = path.relative_to(folder).as_posix()
        findings += [{'file': relative, 'kind': kind + '/' + encoding}
                     for kind, encoding, needle in encoded if needle and needle in data]
        if path.suffix.casefold() == '.exe':
            inside, count = _archive_findings(path, terms)
            if inside is not None:
                archive_checked, modules = True, modules + count
                findings += [{'file': relative, 'kind': kind + '/archive'} for kind in sorted(inside)]
    return {'status': 'LEAK' if findings else 'CLEAN', 'files': files, 'archive_checked': archive_checked,
            'archive_modules': modules, 'findings': findings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('folder', type=Path)
    parser.add_argument('--require-archive', action='store_true',
                        help='fail when the PyInstaller archive could not be opened')
    args = parser.parse_args(argv)
    if not args.folder.is_dir():
        print(json.dumps({'status': 'ERROR', 'error': 'folder not found'}))
        return 2
    receipt = scan(args.folder, needles())
    print(json.dumps(receipt, ensure_ascii=False))
    if args.require_archive and not receipt['archive_checked']:
        return 3
    return 1 if receipt['findings'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
