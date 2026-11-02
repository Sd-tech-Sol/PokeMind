"""Pre-window negative gates: no real external/private operation is attempted."""
import json
import uuid
from types import SimpleNamespace

import pytest
from pokemind import synthetic_qa as qa
from qa_offline_runtime import Runtime, read_fixture, MANIFEST, FORMAT


@pytest.fixture
def offline(local_tmp):
    context = SimpleNamespace(marker={'purpose': 'gui'}, root=local_tmp, validate_live=lambda: local_tmp)
    runtime = Runtime(context)
    fixture = local_tmp / 'build' / ('synthetic-release-' + uuid.uuid4().hex)
    (fixture / '.orchestrator').mkdir(parents=True)
    (fixture / '.orchestrator/SYNTHETIC_QA_ONLY').write_bytes(b'POKEMIND_SYNTHETIC_RELEASE_QA_V1\n')
    (local_tmp / MANIFEST).write_text(json.dumps({'kind': FORMAT, 'fixture': fixture.relative_to(local_tmp).as_posix()}))
    runtime.prepare(resume=True)
    yield runtime
    runtime.patch.undo()


@pytest.mark.parametrize('index', [0, 1, 2])
def test_all_window_choices_are_fake_and_development_is_blocked(offline, index):
    from pokemind.assistant.provider import ProviderError
    adapter = offline.fake_types[index](offline.fixture)
    assert adapter.health()['available']
    with pytest.raises(ProviderError, match='QA_REAL_OPERATIONS_DISABLED'):
        adapter.configure(development=True, privacy_acknowledged=True)
    with pytest.raises(ProviderError): adapter.status()
    with pytest.raises(ProviderError): adapter.compact()
    with pytest.raises(ProviderError): adapter.resume('fictional')
    output = []
    adapter.configure(development=False)
    adapter.start(None)
    adapter.ask_stream('invented', [], output.append)
    assert 'Réponse inventée' in ''.join(output)
    adapter.close()
    assert not qa.current().denials


@pytest.mark.parametrize('name', ['codex', 'claude', 'ollama', 'spawn', 'urlopen', 'opener', 'http', 'image', 'browser'])
def test_real_front_doors_blocked_before_os_or_network(offline, name):
    from pokemind.assistant import provider, codex_app_server
    from pokemind.desktop.images import ImageCache
    from PySide6.QtGui import QDesktopServices
    import urllib.request
    import http.client
    calls = {
        'codex': lambda: codex_app_server.CodexAppServer(offline.fixture),
        'claude': lambda: provider.ClaudeCode(offline.fixture),
        'ollama': lambda: provider.LocalOllama(offline.fixture),
        'spawn': lambda: provider.spawn(['INVENTED'], offline.fixture),
        'urlopen': lambda: urllib.request.urlopen('https://example.invalid/fiction'),
        'opener': lambda: urllib.request.build_opener().open('https://example.invalid/fiction'),
        'http': lambda: http.client.HTTPConnection('example.invalid').connect(),
        'image': lambda: ImageCache(offline.fixture)._get('https://example.invalid/image', 1),
        'browser': lambda: QDesktopServices.openUrl('https://example.invalid/fiction'),
    }
    with pytest.raises(provider.ProviderError, match='QA_REAL_OPERATIONS_DISABLED'): calls[name]()
    assert not qa.current().denials and offline.calls == offline.opener.calls == 0


@pytest.mark.parametrize('fault', ['wrong_kind', 'outside', 'missing_release_marker', 'aliased_marker'])
def test_resume_rejects_unqualified_fixture_before_services(offline, fault):
    path = offline.context.root / MANIFEST
    value = json.loads(path.read_text())
    if fault == 'wrong_kind': value['kind'] = 'ordinary'
    elif fault == 'outside': value['fixture'] = '../../data/local'
    elif fault == 'missing_release_marker': (offline.fixture / '.orchestrator/SYNTHETIC_QA_ONLY').unlink()
    else:
        import os
        os.link(offline.fixture / '.orchestrator/SYNTHETIC_QA_ONLY', offline.context.root / 'alias')
    path.write_text(json.dumps(value))
    with pytest.raises((ValueError, FileNotFoundError)): read_fixture(offline.context)


def test_unmarked_test_context_cannot_launch_gui():
    with pytest.raises(ValueError, match='QA_GUI_PURPOSE_REQUIRED'): Runtime(qa.current())


def test_file_pickers_return_cancel_without_native_browser(offline):
    from PySide6.QtWidgets import QFileDialog
    assert QFileDialog.getOpenFileNames() == ([], '')
    assert QFileDialog.getSaveFileName() == ('', '')
    assert QFileDialog.getExistingDirectory() == ''


def test_nonfixture_root_rejected_before_research(offline):
    from pokemind import batch_public_research
    with pytest.raises(ValueError, match='QA_EXPLICIT_FIXTURE_REQUIRED'):
        batch_public_research.research(qa.PROJECT / 'data/local', as_of='2026-10-27', topic='rules')
    assert not qa.current().denials and offline.opener.calls == 0
