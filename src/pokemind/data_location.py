"""Where the owner's data lives: outside the Git repository (audit P0-1).

The data folder keeps the historical layout (<folder>/data/local/...), so every
existing path and guard works unchanged with that folder as its root. A small
pointer in %LOCALAPPDATA%\\PokeMind records, per project folder, whether its data
was copied out and is in use. Nothing here moves or deletes the project's
data/local: the copy is verified file by file and the original stays as it was.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

POINTER = 'location.json'
# Synthetic pytest output left by direct test runs: not owner data, about 2 GB.
EXCLUDED = ('test-runs',)
CHUNK = 1 << 20


def app_folder():
    base = os.environ.get('LOCALAPPDATA') or str(Path.home() / '.local' / 'share')
    return Path(base).absolute() / 'PokeMind'


def _key(project_root):
    return os.path.normcase(str(Path(project_root).resolve()))


def _redirected(path):
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)
    except OSError:
        return False


def read_pointer():
    path = app_folder() / POINTER
    try:
        if path.is_file() and not _redirected(path) and path.stat().st_size <= 262144:
            value = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(value, dict) and value.get('schema_version') == 1 and isinstance(value.get('projects'), dict):
                return value
    except (OSError, ValueError):
        pass
    return {'schema_version': 1, 'projects': {}}


def entry(project_root):
    value = read_pointer()['projects'].get(_key(project_root))
    return value if isinstance(value, dict) else {}


def write_entry(project_root, value):
    pointer = read_pointer()
    pointer['projects'][_key(project_root)] = value | {'updated_at': datetime.now().isoformat(timespec='seconds')}
    folder = app_folder()
    folder.mkdir(parents=True, exist_ok=True)
    if _redirected(folder):
        raise ValueError('DATA_POINTER_REDIRECT_REFUSED')
    temporary = folder / (POINTER + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(pointer, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(temporary, folder / POINTER)


def legacy_data(project_root):
    """True while the project folder holds owner data (anything but synthetic test output)."""
    try:
        return any(child.name not in EXCLUDED + ('.gitkeep',) for child in (Path(project_root) / 'data/local').iterdir())
    except OSError:
        return False


def _recorded(project_root):
    """The override or the owner's recorded choice, without looking inside the project's data/local."""
    override = os.environ.get('POKEMIND_DATA_ROOT')
    if override:
        return Path(override).absolute(), 'override'
    if os.environ.get('POKEMIND_DESKTOP_SMOKE'):
        return project_root, 'project'  # release QA never follows the owner's pointer
    current = entry(project_root)
    if current.get('status') == 'outside':
        root = Path(str(current.get('data_root', '')))
        if root.is_absolute() and (root / 'data/local').is_dir() and not _redirected(root):
            return root, 'outside'
        return project_root, 'missing'
    if current.get('status') == 'project':
        return project_root, 'project'
    return None


def resolve(project_root):
    """(data_root, state). States: override, outside, missing, offer, project."""
    project_root = Path(project_root).absolute()
    return _recorded(project_root) or (project_root, 'offer' if legacy_data(project_root) else 'project')


def cli_root(project_root):
    """Data root for the command line: the override or a copy the owner accepted; never offers or copies."""
    project_root = Path(project_root).absolute()
    root, state = _recorded(project_root) or (project_root, 'project')
    return root if state in ('override', 'outside') else project_root


def standalone():
    """(data root, workspace) for an installed PokeMind with no project folder.

    The data root is %LOCALAPPDATA%\\PokeMind (or POKEMIND_DATA_ROOT); the empty workspace beside
    data/ is where the Terminal page and explicit development requests start.
    """
    override = os.environ.get('POKEMIND_DATA_ROOT')
    root = Path(override).absolute() if override else app_folder()
    root.mkdir(parents=True, exist_ok=True)
    if _redirected(root):
        raise ValueError('DATA_ROOT_REDIRECT_REFUSED')
    workspace = root / 'workspace'
    workspace.mkdir(exist_ok=True)
    return root, workspace


def choose_target():
    """Default folder, or a new dated one beside it: an earlier copy is never written over."""
    base = app_folder()
    local = base / 'data/local'
    if not local.exists() or not any(local.iterdir()):
        return base
    return base / ('donnees-' + datetime.now().strftime('%Y%m%d-%H%M%S'))


def inventory(project_root):
    """Files to copy (relative path, size) and folders, without reading any content."""
    source = Path(project_root).absolute() / 'data/local'
    if _redirected(source) or not source.is_dir():
        raise ValueError('DATA_SOURCE_UNAVAILABLE')
    files, folders = [], []
    for folder, dirs, names in os.walk(source):
        current = Path(folder)
        if current == source:
            dirs[:] = [d for d in dirs if d not in EXCLUDED]
        for name in dirs + names:
            if _redirected(current / name):
                raise ValueError('DATA_COPY_REDIRECT_REFUSED')
        folders.extend((current / d).relative_to(source) for d in dirs)
        for name in names:
            path = current / name
            files.append((path.relative_to(source), path.stat().st_size))
    return files, folders


def _copy_one(source, destination, step=lambda count: None):
    before = source.stat()
    digest = hashlib.sha256()
    with source.open('rb') as reader, destination.open('xb') as writer:
        while block := reader.read(CHUNK):
            digest.update(block)
            writer.write(block)
            step(len(block))
        writer.flush()
        os.fsync(writer.fileno())
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('DATA_SOURCE_CHANGED_DURING_COPY')
    shutil.copystat(source, destination)
    check = hashlib.sha256()
    with destination.open('rb') as reader:
        while block := reader.read(CHUNK):
            check.update(block)
    if check.hexdigest() != digest.hexdigest():
        raise ValueError('DATA_COPY_MISMATCH')


def copy_out(project_root, target=None, *, progress=lambda done, total: None, cancelled=lambda: False):
    """Copy data/local out of the project, verify every file, then point the project at the copy.

    The copy is built in a fresh partial folder and renamed only once complete;
    on any failure that partial duplicate is removed and the pointer is unchanged.
    """
    project_root = Path(project_root).absolute()
    target = Path(target or choose_target()).absolute()
    if target.resolve().is_relative_to(project_root.resolve()):
        raise ValueError('DATA_TARGET_INSIDE_PROJECT')
    destination = target / 'data/local'
    if destination.exists() and (_redirected(destination) or any(destination.iterdir())):
        raise ValueError('DATA_TARGET_NOT_EMPTY')
    files, folders = inventory(project_root)
    total = sum(size for _, size in files)
    target.mkdir(parents=True, exist_ok=True)
    if _redirected(target) or (target / 'data').exists() and _redirected(target / 'data'):
        raise ValueError('DATA_TARGET_REDIRECT_REFUSED')
    if shutil.disk_usage(target).free < total + total // 10 + (200 << 20):
        raise ValueError('DATA_TARGET_SPACE')
    source = project_root / 'data/local'
    staging = target / 'data' / ('local.partial-' + uuid.uuid4().hex[:8])
    done = 0

    def step(count):
        nonlocal done
        if cancelled():
            raise ValueError('DATA_COPY_CANCELLED')
        done += count
        progress(done, total)
    try:
        staging.mkdir(parents=True)
        for folder in folders:
            (staging / folder).mkdir(parents=True, exist_ok=True)
        progress(0, total)
        for relative, size in files:
            if cancelled():
                raise ValueError('DATA_COPY_CANCELLED')
            try:
                _copy_one(source / relative, staging / relative, step)
            except PermissionError as error:
                raise ValueError('DATA_SOURCE_BUSY') from error
        if destination.exists():
            destination.rmdir()  # empty, checked above
        os.replace(staging, destination)
    except BaseException:
        # Only the duplicate made by this call; the project's data/local is untouched.
        shutil.rmtree(staging, ignore_errors=True)
        raise
    receipt = {'status': 'outside', 'data_root': str(target), 'copied_at': datetime.now().isoformat(timespec='seconds'),
               'files': len(files), 'bytes': total, 'excluded': list(EXCLUDED), 'verified': 'sha256 per file',
               'original': 'kept in the project, unchanged'}
    write_entry(project_root, receipt)
    return receipt


def use_project(project_root, reason):
    """Back to the project's data/local (reverted or declined); any copy stays where it is."""
    previous = entry(project_root)
    write_entry(project_root, {'status': 'project', 'reason': reason, 'previous_data_root': previous.get('data_root')})


def request_copy(project_root):
    write_entry(project_root, {'status': 'offer'})
