"""Archive and restore the owner's PokeMind data, from the app or from scripts (owner, 2026-11-05).

From the app (Settings, Data): « Archiver mes données… » writes one zip where the owner chooses, while
nothing else runs; « Restaurer une archive… » writes a request, PokeMind closes, and the next launch
archives the current data first, then puts the zip's data in place, before anything opens a file in
data/local (as the reset does). The app handles only data/local and the terminal workspace.

From scripts/archive_data.py, reset_data.py and restore_data.py, PokeMind closed: the same, on the whole
%LOCALAPPDATA%\\PokeMind folder (or POKEMIND_DATA_ROOT), with the archives beside it in PokeMind-archives.

- A zip is written under a partial name, then read back entirely (CRC of every file, same names and sizes)
  before it gets its final name; an earlier archive is never written over.
- What is replaced is moved aside in one go (any failure puts everything back) and deleted only once a
  verified zip of it exists. A restore keeps each file's date (it places each game in its season).
Nothing here reads what a file says; it only copies bytes.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from pokemind import data_location
from pokemind.data_reset import _wait_for_exit, remove_tree

ARCHIVES = 'PokeMind-archives'
PREFIX = 'PokeMind-'
TRASH = '.reinitialisation-'
KEEP = (data_location.POINTER,)
FOLDERS = ('data/local', 'workspace')
APP_PARTS = ('data/local', 'workspace')
APP_EXCLUDED = ('data/local/test-runs',)  # synthetic test output, never owner data
RESTORE_REQUEST = 'restore-request.json'
STORED = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.zip', '.gz', '.7z', '.exe', '.dll', '.pyd'}
SPARE = 200 << 20


def account_folder():
    override = os.environ.get('POKEMIND_DATA_ROOT')
    return Path(override).absolute() if override else data_location.app_folder()


def archive_folder(root):
    """Beside the account folder, never inside: a reset never takes its own archives."""
    return Path(root).absolute().parent / ARCHIVES


def default_name():
    return PREFIX + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip'


def running():
    """True while a PokeMind window is open (installed copy or the one inside the project)."""
    if sys.platform != 'win32':
        return False
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq PokeMind.exe', '/FO', 'CSV', '/NH'],
                         capture_output=True, text=True, timeout=30,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
    return '"pokemind.exe"' in out.casefold()


def _posix(relative):
    return PurePosixPath(*Path(relative).parts).as_posix()


def _starts(root, parts, *, pointer=False):
    """The top-level paths handled: the given parts, or every child but leftovers (and the pointer, which
    is archived but never moved: the one in use stays)."""
    if parts:
        return [Path(p) for p in parts]
    return [Path(c.name) for c in sorted(root.iterdir())
            if (pointer or c.name not in KEEP) and not c.name.startswith(TRASH)]


def _inventory(root, parts=None, excluded=()):
    """(files as (relative, size), folders): refuses links and junctions instead of following them."""
    files, folders = [], []
    for start in _starts(root, parts, pointer=True):
        path = root / start
        if data_location._redirected(path):
            raise ValueError('ARCHIVE_REDIRECT_REFUSED')
        if not path.exists() or _posix(start) in excluded:
            continue
        for parent in reversed(start.parents[:-1]):
            if parent not in folders:
                folders.append(parent)
        if path.is_file():
            files.append((start, path.stat().st_size))
            continue
        for folder, dirs, names in os.walk(path):
            current = Path(folder)
            for name in dirs + names:
                if data_location._redirected(current / name):
                    raise ValueError('ARCHIVE_REDIRECT_REFUSED')
            relative = current.relative_to(root)
            dirs[:] = sorted(d for d in dirs if _posix(relative / d) not in excluded and not d.startswith(TRASH))
            folders.append(relative)
            files.extend((relative / name, (current / name).stat().st_size) for name in sorted(names))
    return files, folders


def _target(dest):
    stamp = default_name()[len(PREFIX):-4]
    for suffix in [''] + ['-%d' % n for n in range(2, 100)]:
        path = dest / (PREFIX + stamp + suffix + '.zip')
        if not path.exists():
            return path
    raise FileExistsError(stamp)


def verify(path, written, folders=()):
    """Every file read back (CRC), with the names and sizes written."""
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ARCHIVE_CRC_MISMATCH')
        listed = {i.filename: i.file_size for i in archive.infolist() if not i.is_dir()}
        dirs = {i.filename.rstrip('/') for i in archive.infolist() if i.is_dir()}
    if listed != written or not {_posix(f) for f in folders} <= dirs:
        raise ValueError('ARCHIVE_CONTENT_MISMATCH')


def archive(root=None, dest=None, *, target=None, parts=None, excluded=(), app=False,
            progress=lambda done, total: None):
    """One verified zip; returns its receipt. The app calls it with app=True while nothing else runs."""
    root = Path(root or account_folder()).absolute()
    if not app and running():  # an open window may be writing its databases
        raise ValueError('POKEMIND_RUNNING')
    if not root.is_dir() or data_location._redirected(root):
        raise ValueError('ARCHIVE_SOURCE_UNAVAILABLE')
    if target:
        target = Path(target).absolute()
        if target.suffix.casefold() != '.zip':
            target = target.with_name(target.name + '.zip')
        dest = target.parent
    else:
        dest = Path(dest or archive_folder(root)).absolute()
    if dest.resolve().is_relative_to(root.resolve()):
        raise ValueError('ARCHIVE_INSIDE_SOURCE')
    files, folders = _inventory(root, parts, excluded)
    total = sum(size for _, size in files)
    dest.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(dest).free < total + SPARE:
        raise ValueError('ARCHIVE_SPACE')
    target = target or _target(dest)
    partial = target.with_name(target.name + '.partial-' + uuid.uuid4().hex[:8])
    done, written = 0, {}
    try:
        with zipfile.ZipFile(partial, 'x', zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6,
                             strict_timestamps=False) as out:
            for folder in folders:
                out.write(root / folder, _posix(folder) + '/')
            for relative, size in files:
                kind = zipfile.ZIP_STORED if relative.suffix.casefold() in STORED else zipfile.ZIP_DEFLATED
                name = _posix(relative)
                try:
                    out.write(root / relative, name, compress_type=kind)
                except FileNotFoundError:
                    if not app:
                        raise
                    continue  # a temporary file the open app removed meanwhile
                written[name] = out.getinfo(name).file_size  # a log may grow while the app archives
                done += size
                progress(done, total)
        verify(partial, written, folders)
        os.replace(partial, target)  # the owner chose this name, and confirmed replacing it if it existed
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {'status': 'ARCHIVED', 'zip': str(target), 'files': len(written), 'bytes': total,
            'zip_bytes': target.stat().st_size}


def _move(source, target, attempts=20, wait=0.5):
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError:  # a file may still be held for a moment
            if attempt == attempts - 1:
                raise
            time.sleep(wait)


def _set_aside(root, parts=None, attempts=20, wait=0.5):
    """Move what is handled into one hidden folder; any failure puts everything back."""
    trash = root / (TRASH + uuid.uuid4().hex)
    trash.mkdir()
    moved = []
    try:
        for start in _starts(root, parts):
            if (root / start) == trash or not (root / start).exists():
                continue
            (trash / start).parent.mkdir(parents=True, exist_ok=True)
            _move(root / start, trash / start, attempts, wait)
            moved.append(start)
    except OSError as error:
        for start in reversed(moved):
            os.replace(trash / start, root / start)
        remove_tree(trash)
        raise ValueError('RESET_FILE_IN_USE: ' + (str(getattr(error, 'filename', '') or '').rsplit(os.sep, 1)[-1])) from error
    return trash


def _first_launch_folders(root, parts=None):
    """Empty data/local (and workspace), and the data/local of every data folder the pointer names here."""
    for name in parts or FOLDERS:
        (root / name).mkdir(parents=True, exist_ok=True)
    if parts:
        return
    pointer = root / data_location.POINTER
    try:
        projects = json.loads(pointer.read_text(encoding='utf-8')).get('projects', {}) if pointer.is_file() else {}
    except (OSError, ValueError):
        projects = {}
    for value in projects.values() if isinstance(projects, dict) else ():
        if not isinstance(value, dict) or value.get('status') != 'outside':
            continue
        target = Path(str(value.get('data_root', '')))
        if target.is_absolute() and target.resolve().is_relative_to(root.resolve()):
            (target / 'data/local').mkdir(parents=True, exist_ok=True)


def _erase(trash):
    """Delete what was set aside, and any leftover of an earlier reset; True if something remains."""
    root = trash.parent
    for folder in [trash] + [c for c in root.iterdir() if c.name.startswith(TRASH) and c != trash]:
        remove_tree(folder)  # read-only files too
    return any(c.name.startswith(TRASH) for c in root.iterdir())


def clear_leftovers(root=None):
    """Finish deleting what an earlier reset set aside (already in its verified archive)."""
    root = Path(root or account_folder()).absolute()
    if running():
        raise ValueError('POKEMIND_RUNNING')
    leftovers = [c for c in root.iterdir() if c.name.startswith(TRASH) and c.is_dir() and not c.is_symlink()]
    return bool(leftovers) and _erase(leftovers[0])


def reset(root=None, dest=None, *, progress=lambda done, total: None):
    """Archive (verified), then empty the account folder for a first launch."""
    root = Path(root or account_folder()).absolute()
    receipt = archive(root, dest, progress=progress)
    trash = _set_aside(root)
    _first_launch_folders(root)
    return receipt | {'status': 'RESET', 'leftover': _erase(trash)}


def _under(name, parts):
    name = name.rstrip('/')
    return any(name == p or name.startswith(p + '/') or p.startswith(name + '/') for p in parts)


def members(path, parts=None):
    """The zip's entries to put back: safe names only (no absolute path, drive, '..' or link)."""
    with zipfile.ZipFile(path) as source:
        infos = source.infolist()
    for info in infos:
        name = PurePosixPath(info.filename)
        if info.filename.startswith(('/', '\\')) or ':' in info.filename or '..' in name.parts or '\\' in info.filename:
            raise ValueError('RESTORE_NAME_REFUSED')
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('RESTORE_LINK_REFUSED')
    if not any(i.filename.startswith('data/local/') for i in infos):
        raise ValueError('RESTORE_NOT_POKEMIND')
    return [i for i in infos if not parts or _under(i.filename, parts)]


def restore(path, root=None, dest=None, *, parts=None, excluded=(), app=False, progress=lambda done, total: None):
    """Put a zip back: the current content is archived first, then replaced; the pointer in use stays."""
    path = Path(path).absolute()
    root = Path(root or account_folder()).absolute()
    if not app and running():
        raise ValueError('POKEMIND_RUNNING')
    chosen = members(path, parts)
    with zipfile.ZipFile(path) as source:
        if source.testzip() is not None:
            raise ValueError('ARCHIVE_CRC_MISMATCH')
    root.mkdir(parents=True, exist_ok=True)
    before = None
    if [f for f, _ in _inventory(root, parts, excluded)[0] if _posix(f) not in KEEP]:  # more than the pointer
        before = archive(root, dest, parts=parts, excluded=excluded, app=app, progress=progress)
    trash = _set_aside(root, parts)
    total, done = sum(i.file_size for i in chosen), 0
    try:
        with zipfile.ZipFile(path) as source:
            for info in chosen:
                if not parts and info.filename.rstrip('/') in KEEP and (root / info.filename).exists():
                    continue  # the pointer in use stays
                target = root / PurePosixPath(info.filename)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(info) as reader, target.open('xb') as writer:
                    shutil.copyfileobj(reader, writer, 1 << 20)
                stamp = time.mktime(info.date_time + (0, 0, -1))
                os.utime(target, (stamp, stamp))
                done += info.file_size
                progress(done, total)
    except BaseException:
        for start in _starts(root, parts):
            current = root / start
            if current != trash and current.exists():
                remove_tree(current) if current.is_dir() else current.unlink()
        for start in _starts(trash, parts):
            if (trash / start).exists():
                (root / start).parent.mkdir(parents=True, exist_ok=True)
                os.replace(trash / start, root / start)
        remove_tree(trash)
        raise
    _first_launch_folders(root, parts)
    return {'status': 'RESTORED', 'zip': str(path), 'files': sum(not i.is_dir() for i in chosen),
            'previous_archive': before and before['zip'], 'leftover': _erase(trash)}


def request_restore(root, path, *, parts, archives, pid=None):
    """The window asks; the next launch restores, before anything opens a file in data/local."""
    parts = [p for p in APP_PARTS if p in parts]
    if 'data/local' not in parts:
        raise ValueError('RESTORE_PARTS_INVALID')
    for place in (path, archives):
        if Path(place).resolve().is_relative_to(Path(root).resolve()):
            raise ValueError('ARCHIVE_INSIDE_SOURCE')
    members(path, parts)  # an unusable zip is refused now, while the window is still open
    local = Path(root) / 'data/local'
    local.mkdir(parents=True, exist_ok=True)
    value = {'schema_version': 1, 'zip': str(Path(path).absolute()), 'parts': parts,
             'archives': str(Path(archives).absolute()), 'requested_at': datetime.now().isoformat(timespec='seconds')}
    if pid:
        value['pid'] = int(pid)
    temporary = local / (RESTORE_REQUEST + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, local / RESTORE_REQUEST)
    return value


def pending_restore(root):
    path = Path(root) / 'data/local' / RESTORE_REQUEST
    try:
        if path.is_file() and not path.is_symlink() and path.stat().st_size <= 8192:
            value = json.loads(path.read_text(encoding='utf-8'))
            if (isinstance(value, dict) and value.get('schema_version') == 1 and isinstance(value.get('zip'), str)
                    and isinstance(value.get('archives'), str) and isinstance(value.get('parts'), list)
                    and 'data/local' in value['parts'] and set(value['parts']) <= set(APP_PARTS)):
                return value
    except (OSError, ValueError):
        pass
    return None


def apply_restore(root, *, exit_wait=90):
    """Apply a pending restore once the closing window has ended; None when there is none."""
    value = pending_restore(root)
    request = Path(root) / 'data/local' / RESTORE_REQUEST
    if value is None:
        if request.is_file():
            request.unlink()  # an unreadable request never repeats on every launch
        return None
    request.unlink()
    _wait_for_exit(value.get('pid'), exit_wait)
    try:
        return restore(value['zip'], root, value['archives'], parts=tuple(value['parts']), excluded=APP_EXCLUDED,
                       app=True)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        return {'status': 'FAILED', 'error': error_code(error), 'zip': value['zip']}


def error_code(error):
    """A short code for the owner's message; never a path."""
    if isinstance(error, FileNotFoundError):
        return 'ARCHIVE_NOT_FOUND'
    if isinstance(error, PermissionError):
        return 'ARCHIVE_PERMISSION'
    if isinstance(error, zipfile.BadZipFile):
        return 'RESTORE_NOT_POKEMIND'
    if isinstance(error, ValueError):
        return str(error).split(':', 1)[0]
    return type(error).__name__


def size_text(value):
    for unit in ('o', 'Ko', 'Mo', 'Go'):
        if value < 1024 or unit == 'Go':
            return (f'{value:.0f} {unit}' if unit == 'o' else f'{value:.1f} {unit}').replace('.', ',')
        value /= 1024


MESSAGES = {
    'POKEMIND_RUNNING': 'PokeMind est ouvert. Ferme-le, puis relance la commande.',
    'ARCHIVE_SPACE': 'Pas assez d’espace libre pour l’archive.',
    'ARCHIVE_SOURCE_UNAVAILABLE': 'Le dossier PokeMind est introuvable.',
    'ARCHIVE_REDIRECT_REFUSED': 'Un lien ou une jonction est dans le dossier : rien n’a été fait.',
    'ARCHIVE_INSIDE_SOURCE': 'L’archive doit être hors du dossier des données PokeMind.',
    'RESET_FILE_IN_USE': 'Un fichier du dossier est encore utilisé (fenêtre, terminal ou explorateur ouvert dedans); '
                         'tout est resté en place.',
    'RESTORE_NAME_REFUSED': 'Cette archive contient un chemin refusé.',
    'RESTORE_LINK_REFUSED': 'Cette archive contient un lien refusé.',
    'RESTORE_NOT_POKEMIND': 'Ce fichier n’est pas une archive de données PokeMind.',
    'ARCHIVE_CRC_MISMATCH': 'L’archive est abîmée.',
    'ARCHIVE_NOT_FOUND': 'L’archive choisie est introuvable (fichier déplacé ou clé USB retirée?).',
    'ARCHIVE_PERMISSION': 'Windows refuse l’accès à cet endroit; choisis un autre dossier.',
    'ARCHIVE_CONTENT_MISMATCH': 'L’archive relue ne correspond pas aux fichiers; elle n’a pas été gardée.',
}


def main(action, argv=None):
    import argparse
    parser = argparse.ArgumentParser(description={
        'archive': 'Archive tout le dossier PokeMind de ce compte Windows dans un zip vérifié.',
        'reset': 'Archive tout (zip vérifié), puis remet PokeMind comme à sa première ouverture.',
        'restore': 'Remet le contenu d’une archive (le contenu actuel est archivé avant).'}[action])
    if action == 'restore':
        parser.add_argument('zip', help='archive PokeMind-AAAAMMJJ-HHMMSS.zip à remettre')
    parser.add_argument('--dossier', help='dossier PokeMind (défaut : %%LOCALAPPDATA%%\\PokeMind)')
    parser.add_argument('--archives', help='où écrire le zip (défaut : PokeMind-archives à côté du dossier)')
    args = parser.parse_args(argv)
    root = Path(args.dossier).absolute() if args.dossier else account_folder()
    shown = [0]

    def progress(done, total):
        percent = 100 * done // total if total else 100
        if percent >= shown[0] + 10 or done == total:
            shown[0] = percent
            print(f'  {percent} %', flush=True)
    try:
        if action == 'archive':
            print('Archive de', root, flush=True)
            result = archive(root, args.archives, progress=progress)
        elif action == 'reset':
            print('Réinitialisation de', root, '(archive d’abord)', flush=True)
            result = reset(root, args.archives, progress=progress)
        else:
            print('Restauration dans', root, flush=True)
            result = restore(args.zip, root, args.archives, progress=progress)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print('Rien n’a été effacé.', MESSAGES.get(error_code(error), 'Erreur : ' + str(error)))
        return 2
    if 'bytes' in result:
        print(f"Archive vérifiée : {result['zip']}")
        print(f"  {result['files']} fichiers, {size_text(result['bytes'])} → {size_text(result['zip_bytes'])}")
    if result.get('previous_archive'):
        print('Contenu remplacé gardé dans :', result['previous_archive'])
    if result['status'] == 'RESET':
        print('PokeMind est remis à zéro : la prochaine ouverture sera une première ouverture.')
    if result['status'] == 'RESTORED':
        print(f"Restauré : {result['files']} fichiers depuis {result['zip']}")
    if result.get('leftover'):
        print('Un dossier caché .reinitialisation-… n’a pas pu être supprimé en entier; il est sans effet.')
    return 0
