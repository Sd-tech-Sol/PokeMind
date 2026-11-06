"""PokeMind updates from GitHub: invented releases and installers only, never the network."""
import hashlib
import io
import json
from datetime import datetime, timedelta

import pytest

from pokemind import app_update

BODY = b'MZ invented installer bytes'


def release(tag, *, draft=False, prerelease=True, assets=True, url=None, size=None):
    name = 'PokeMind-Setup-%s.exe' % tag.lstrip('v')
    base = url or app_update.DOWNLOADS + tag + '/'
    return {'tag_name': tag, 'draft': draft, 'prerelease': prerelease,
            'html_url': app_update.PAGE + '/tag/' + tag,
            'assets': [{'name': name, 'size': size or len(BODY), 'browser_download_url': base + name},
                       {'name': name + '.sha256', 'size': 90, 'browser_download_url': base + name + '.sha256'}]
            if assets else []}


def test_the_newest_published_version_above_this_one_is_offered():
    releases = [release('v0.9.2'), release('v0.9.4', draft=True), release('v0.9.3'), release('v0.9.5', assets=False),
                release('v1.0.0', url='https://example.invalid/'), release('not-a-version')]
    found = app_update.newest(releases, '0.9.2')
    assert found['status'] == 'AVAILABLE' and found['version'] == '0.9.3' and found['prerelease']
    assert found['installer']['name'] == 'PokeMind-Setup-0.9.3.exe' and found['page'].endswith('/tag/v0.9.3')
    assert app_update.newest(releases, '0.9.3') == {'status': 'CURRENT', 'version': '0.9.3'}
    assert app_update.newest([release('v0.10.0')], '0.9.9')['version'] == '0.10.0'  # numbers, not text
    fetched = app_update.check('0.9.2', fetch=lambda url: io.BytesIO(json.dumps(releases).encode()))
    assert fetched['version'] == '0.9.3'


def fake(checksum, body=BODY):
    def fetch(url):
        if url.endswith('.sha256'):
            return io.BytesIO(checksum.encode())
        return io.BytesIO(body)
    return fetch


def test_the_installer_runs_only_once_its_published_sha256_matches(tmp_path):
    offer = app_update.newest([release('v0.9.3')], '0.9.2')
    good = hashlib.sha256(BODY).hexdigest() + '  PokeMind-Setup-0.9.3.exe\n'
    seen = []
    (tmp_path / 'PokeMind-Setup-0.9.1.exe').write_bytes(b'older update')
    (tmp_path / 'PokeMind-Setup-notes.exe').write_bytes(b'not an installer name')
    path = app_update.download(offer, tmp_path, fetch=fake(good), progress=lambda done, total: seen.append((done, total)))
    assert path.read_bytes() == BODY and seen[-1] == (len(BODY), len(BODY))
    assert sorted(p.name for p in tmp_path.iterdir()) == ['PokeMind-Setup-0.9.3.exe', 'PokeMind-Setup-notes.exe']
    (tmp_path / 'PokeMind-Setup-notes.exe').unlink()
    path.unlink()
    for checksum, body, code in ((hashlib.sha256(b'other').hexdigest(), BODY, 'UPDATE_CHECKSUM_MISMATCH'),
                                 (good, BODY + b'x', 'UPDATE_SIZE_MISMATCH'),
                                 (good, BODY[:-1], 'UPDATE_SIZE_MISMATCH'),
                                 (hashlib.sha256(BODY).hexdigest() + '  autre.exe', BODY, 'UPDATE_CHECKSUM_UNREADABLE'),
                                 ('pas une empreinte', BODY, 'UPDATE_CHECKSUM_UNREADABLE')):
        with pytest.raises(app_update.UpdateError, match=code):
            app_update.download(offer, tmp_path, fetch=fake(checksum, body))
        assert not list(tmp_path.iterdir())  # nothing left to run
    with pytest.raises(app_update.UpdateError, match='UPDATE_CANCELLED'):
        app_update.download(offer, tmp_path, fetch=fake(good), cancelled=lambda: True)


def test_only_the_public_repository_and_github_download_hosts_are_used():
    with pytest.raises(app_update.UpdateError, match='UPDATE_URL_REFUSED'):
        app_update._open('https://example.invalid/PokeMind-Setup-9.9.9.exe')
    handler = app_update._GitHubRedirects()
    with pytest.raises(app_update.UpdateError, match='UPDATE_REDIRECT_REFUSED'):
        handler.redirect_request(None, None, 302, 'Found', {}, 'https://example.invalid/setup.exe')
    with pytest.raises(app_update.UpdateError, match='UPDATE_REDIRECT_REFUSED'):
        handler.redirect_request(None, None, 302, 'Found', {}, 'http://objects.githubusercontent.com/setup.exe')


def test_only_the_installed_copy_installs_by_itself(tmp_path):
    program = tmp_path / 'PokeMind.exe'
    program.write_bytes(b'')
    assert not app_update.installed_copy(program, frozen=True)
    (tmp_path / 'unins000.exe').write_bytes(b'')
    assert app_update.installed_copy(program, frozen=True)
    assert not app_update.installed_copy(program, frozen=False)  # from source: the release page instead


def test_the_automatic_check_waits_twelve_hours_unless_something_was_updated(local_tmp, monkeypatch):
    now, commit = datetime(2026, 11, 5, 12, 0), 'a' * 40
    assert app_update.due(local_tmp, now)
    app_update.save_check(local_tmp, {'app': {'status': 'AVAILABLE', 'version': '9.9.9'}}, now, catalogue=commit)
    assert app_update.last_check(local_tmp)['app'] == {'status': 'AVAILABLE', 'version': '9.9.9'}
    assert not app_update.due(local_tmp, now + timedelta(hours=11), catalogue=commit)
    assert app_update.due(local_tmp, now + timedelta(hours=12), catalogue=commit)
    assert app_update.due(local_tmp, now + timedelta(hours=1), catalogue='b' * 40)  # new cards since
    assert app_update.due(local_tmp, now + timedelta(hours=1))  # catalogue removed by a reset
    monkeypatch.setattr(app_update, '__version__', '9.9.9')
    assert app_update.due(local_tmp, now + timedelta(hours=1), catalogue=commit)  # PokeMind 9.9.9 now installed
