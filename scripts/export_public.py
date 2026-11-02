"""Export HEAD as a new repository with a single commit, for a public release. Never pushes.

    python scripts/export_public.py C:/chemin/PokeMind-public --author-name "Nom" --author-email "id+nom@users.noreply.github.com"

The tracked files are checked before anything is written: no private data path, database, key, secret,
personal e-mail domain, nor the Windows user name (hence no path into this PC's user folder) or Git
user name of this PC (read from the environment, never stored), unless that name is the chosen public author. The new
commit has exactly the same tree as HEAD, so the published content is the audited content.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_repo_hygiene import FORBIDDEN_SUFFIXES, MAX_TRACKED_BYTES, SECRET_PATTERNS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PERSONAL_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@(?:gmail|hotmail|outlook|live|yahoo|icloud)\.', re.IGNORECASE)


class ExportRefused(Exception):
    pass


def _git(cwd, *arguments, data=None):
    completed = subprocess.run(['git', '-c', 'core.autocrlf=false', *arguments], cwd=cwd, input=data,
                               capture_output=True, check=False)
    if completed.returncode:
        raise ExportRefused('git ' + arguments[0] + ' : ' + completed.stderr.decode('utf-8', 'replace').strip())
    return completed.stdout


def _plain(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).casefold()


def personal_terms(source):
    """Words that identify the person on this PC: the Windows user name and the parts of the Git user name."""
    completed = subprocess.run(['git', 'config', '--get', 'user.name'], cwd=source, capture_output=True, encoding='utf-8')
    found = {os.environ.get('USERNAME', ''), *completed.stdout.split()}
    return {term for term in found if len(term) >= 4}


def _findings(name, payload, terms):
    path = Path(name)
    result = []
    if name.startswith('data/local/') and name != 'data/local/.gitkeep':
        result.append('private-path')
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES or path.name.startswith('.env'):
        result.append('forbidden-file')
    if len(payload) > MAX_TRACKED_BYTES:
        result.append('oversize')
    result += [label for label, pattern in SECRET_PATTERNS.items() if pattern.search(payload)]
    text = payload.decode('utf-8', 'ignore')
    if PERSONAL_EMAIL.search(text):
        result.append('personal_email')
    plain = _plain(text)
    if any(term in plain for term in terms):
        result.append('personal-name')
    return result


def export(source, output, author_name, author_email, terms, message='PokeMind'):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ExportRefused('le dossier de sortie existe déjà')
    inside = output.is_relative_to(source)
    if inside and not output.is_relative_to(source / 'build'):
        raise ExportRefused('sortie dans le dépôt refusée (sauf sous build/)')
    if _git(source, 'status', '--porcelain', '--untracked-files=no').strip():
        raise ExportRefused('modifications non validées : valider ou annuler avant l’export')
    allowed = {_plain(word) for word in re.split(r'[\s._@+-]+', author_name + ' ' + author_email) if word}
    terms = {_plain(term) for term in terms} - allowed
    archive = tarfile.open(fileobj=io.BytesIO(_git(source, 'archive', '--format=tar', 'HEAD')))
    members = [member for member in archive.getmembers() if member.isfile()]
    refused = []
    for member in members:
        refused += [label + ':' + member.name for label in _findings(member.name, archive.extractfile(member).read(), terms)]
    if refused:
        raise ExportRefused('contenu refusé : ' + ', '.join(sorted(refused)))
    output.mkdir(parents=False)
    archive.extractall(output, filter='data')
    _git(output, 'init', '-q', '-b', 'main')
    _git(output, 'config', 'core.autocrlf', 'false')
    _git(output, 'add', '-A')
    _git(output, '-c', 'user.name=' + author_name, '-c', 'user.email=' + author_email, 'commit', '-q', '-m', message)
    expected = _git(source, 'rev-parse', 'HEAD^{tree}').decode().strip()
    tree = _git(output, 'rev-parse', 'HEAD^{tree}').decode().strip()
    if tree != expected:
        raise ExportRefused('arbre exporté différent de HEAD')
    return {'status': 'EXPORTED', 'files': len(members), 'tree': tree, 'same_tree_as_head': True,
            'source_commit': _git(source, 'rev-parse', 'HEAD').decode().strip(),
            'commit': _git(output, 'rev-parse', 'HEAD').decode().strip(),
            'commits': int(_git(output, 'rev-list', '--count', 'HEAD')), 'pushed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('output', type=Path)
    parser.add_argument('--author-name', required=True)
    parser.add_argument('--author-email', required=True)
    parser.add_argument('--message', default=None)
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT / 'src'))
    from pokemind import __version__
    try:
        receipt = export(ROOT, args.output, args.author_name, args.author_email, personal_terms(ROOT),
                         args.message or 'PokeMind ' + __version__)
    except ExportRefused as error:
        print(json.dumps({'status': 'REFUSED', 'error': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
