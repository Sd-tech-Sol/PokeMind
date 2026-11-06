"""PokeMind updates from GitHub (owner, 2026-11-05): an alert when a newer version is published, then one
click that downloads the installer, checks it and installs it; PokeMind closes and opens again.

- check: one request to the GitHub API for the releases of the public repository (prereleases included,
  drafts never). Nothing personal is sent; GitHub sees the request like any visit to a web page.
- download: the installer and its .sha256 from the same release, over HTTPS from GitHub only (redirections
  stay on GitHub's download hosts); its size and SHA-256 must match before anything runs.
- install: only for the copy set up by the PokeMind installer. The installer runs silently (a progress window
  only), waits until this window has closed, replaces the program (the data stays in %LOCALAPPDATA%\\PokeMind,
  the folder chosen at installation is kept), then opens PokeMind again. Another copy (the one built inside
  the project) gets the release page instead.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind import __version__

REPOSITORY = 'Sd-tech-Sol/PokeMind'
RELEASES_URL = 'https://api.github.com/repos/' + REPOSITORY + '/releases?per_page=10'
PAGE = 'https://github.com/' + REPOSITORY + '/releases'
DOWNLOADS = 'https://github.com/' + REPOSITORY + '/releases/download/'
HOSTS = {'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com'}
MUTEX = 'PokeMindDesktopRunning'  # packaging/PokeMind.iss waits for it before replacing the program
MAX_RELEASES, MAX_CHECKSUM, MAX_INSTALLER = 4 << 20, 4096, 400 << 20
CHECK_FILE = 'data/local/update-check.json'
CHECK_EVERY = timedelta(hours=12)


class UpdateError(Exception):
    pass


def version(text):
    match = re.fullmatch(r'v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})', str(text or '').strip())
    return tuple(int(part) for part in match.groups()) if match else None


class _GitHubRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.hostname not in HOSTS:
            raise UpdateError('UPDATE_REDIRECT_REFUSED')
        return super().redirect_request(request, fp, code, message, headers, url)


def _open(url):
    if not (url == RELEASES_URL or url.startswith(DOWNLOADS)):
        raise UpdateError('UPDATE_URL_REFUSED')
    accept = 'application/vnd.github+json' if url == RELEASES_URL else 'application/octet-stream'
    request = Request(url, headers={'User-Agent': 'PokeMind-desktop', 'Accept': accept})
    return build_opener(_GitHubRedirects).open(request, timeout=30)


def _read(response, maximum):
    body = response.read(maximum + 1)
    if len(body) > maximum:
        raise UpdateError('UPDATE_RESPONSE_TOO_LARGE')
    return body


def newest(releases, current=__version__):
    """The newest published release above the current version that carries its installer and checksum."""
    best = None
    for item in releases if isinstance(releases, list) else []:
        if not isinstance(item, dict) or item.get('draft'):
            continue
        number = version(item.get('tag_name'))
        if number is None or number <= (version(current) or (0, 0, 0)) or (best and number <= best[0]):
            continue
        name = 'PokeMind-Setup-%d.%d.%d.exe' % number
        assets = {a.get('name'): a for a in item.get('assets') or [] if isinstance(a, dict)}
        installer, checksum = assets.get(name), assets.get(name + '.sha256')
        if not installer or not checksum:
            continue
        urls = [a.get('browser_download_url') for a in (installer, checksum)]
        if not all(isinstance(u, str) and u.startswith(DOWNLOADS) for u in urls):
            continue
        size = installer.get('size')
        if type(size) is not int or not 0 < size <= MAX_INSTALLER:
            continue
        page = item.get('html_url') if str(item.get('html_url', '')).startswith(PAGE) else PAGE
        best = (number, {'status': 'AVAILABLE', 'version': '%d.%d.%d' % number, 'page': page,
                         'prerelease': bool(item.get('prerelease')), 'installer': {'name': name, 'size': size,
                         'url': urls[0]}, 'checksum': urls[1]})
    return best[1] if best else {'status': 'CURRENT', 'version': current}


def check(current=__version__, *, fetch=_open):
    with fetch(RELEASES_URL) as response:
        releases = json.loads(_read(response, MAX_RELEASES))
    return newest(releases, current)


SETUP = re.compile(r'PokeMind-Setup-\d{1,4}\.\d{1,4}\.\d{1,4}\.exe')


def folder():
    return Path(tempfile.gettempdir()) / 'PokeMind-update'


def download(release, target=None, *, progress=lambda done, total: None, cancelled=lambda: False, fetch=_open):
    """The installer, checked against its published SHA-256; returns its path."""
    installer = release['installer']
    target = Path(target or folder())
    target.mkdir(parents=True, exist_ok=True)
    with fetch(release['checksum']) as response:
        text = _read(response, MAX_CHECKSUM).decode('ascii', 'replace')
    match = re.match(r'\s*([0-9A-Fa-f]{64})(?:\s+\*?(\S+))?', text)
    if not match or (match.group(2) and match.group(2) != installer['name']):
        raise UpdateError('UPDATE_CHECKSUM_UNREADABLE')
    expected = match.group(1).lower()
    path = target / installer['name']
    for old in target.glob('PokeMind-Setup-*.exe'):  # earlier updates already installed
        if old.name != path.name and SETUP.fullmatch(old.name):
            old.unlink(missing_ok=True)
    partial = path.with_name(path.name + '.partial')
    digest, done = hashlib.sha256(), 0
    try:
        with fetch(installer['url']) as response, partial.open('wb') as out:
            while True:
                if cancelled():
                    raise UpdateError('UPDATE_CANCELLED')
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                done += len(chunk)
                if done > installer['size']:
                    raise UpdateError('UPDATE_SIZE_MISMATCH')
                digest.update(chunk)
                out.write(chunk)
                progress(done, installer['size'])
        if done != installer['size']:
            raise UpdateError('UPDATE_SIZE_MISMATCH')
        if digest.hexdigest() != expected:
            raise UpdateError('UPDATE_CHECKSUM_MISMATCH')
        os.replace(partial, path)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return path


def installed_copy(executable=None, frozen=None):
    """True for the copy set up by the PokeMind installer (its uninstaller sits beside the program)."""
    frozen = getattr(sys, 'frozen', False) if frozen is None else frozen
    return bool(frozen) and (Path(executable or sys.executable).parent / 'unins000.exe').is_file()


def start_installer(path):
    """Run the downloaded installer silently; it waits for this window to close, then reopens PokeMind."""
    flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    return subprocess.Popen([str(path), '/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/RELAUNCH=1'],
                            creationflags=flags, close_fds=True)


_MARK = None


def mark_running():
    """A named mutex the installer waits on, so it never replaces files PokeMind still uses."""
    global _MARK
    if sys.platform == 'win32' and _MARK is None:
        import ctypes
        _MARK = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX) or None
    return _MARK


def last_check(root):
    try:
        value = json.loads((Path(root) / CHECK_FILE).read_text(encoding='utf-8'))
        return value if isinstance(value, dict) and isinstance(value.get('checked_at'), str) else None
    except (OSError, ValueError):
        return None


def due(root, now=None, catalogue=None):
    """True when the last automatic check is older than CHECK_EVERY, missing, or made before PokeMind or its
    card catalogue changed: an update just installed is never offered again."""
    value = last_check(root)
    if value is None or value.get('version') != __version__ or value.get('catalogue') != catalogue:
        return True
    try:
        return value is None or (now or datetime.now()) - datetime.fromisoformat(value['checked_at']) >= CHECK_EVERY
    except ValueError:
        return True


def save_check(root, result, now=None, catalogue=None):
    """Keep the answer with what it was checked against: this PokeMind version and the catalogue commit."""
    path = Path(root) / CHECK_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(dict(result, checked_at=(now or datetime.now()).isoformat(timespec='seconds'),
                                         version=__version__, catalogue=catalogue), ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, path)
