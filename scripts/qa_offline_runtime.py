"""Explicit offline reception wrapper over the existing desktop and fixtures.

Imported only by the dedicated QA launcher. Python instrumentation is not an
OS sandbox. No normal launcher, provider configuration or owner EXE is changed.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

from pokemind import synthetic_qa as qa

BANNER = 'QA HORS LIGNE — DONNÉES FICTIVES'
MANIFEST = 'OFFLINE_GUI.json'
FORMAT = 'POKEMIND_OFFLINE_GUI_V1'


def read_fixture(context):
    root = context.validate_live()
    manifest = qa.no_alias(root / MANIFEST, root)
    if manifest.stat().st_size > 512:
        raise ValueError('QA_OFFLINE_MANIFEST_REQUIRED')
    value = json.loads(manifest.read_text(encoding='utf-8'))
    if (set(value) != {'kind', 'fixture'} or value['kind'] != FORMAT
            or not isinstance(value['fixture'], str)
            or not re.fullmatch('build/synthetic-release-[0-9a-f]{32}', value['fixture'])):
        raise ValueError('QA_OFFLINE_MANIFEST_REQUIRED')
    fixture = qa.no_alias(root / value['fixture'], root)
    # Verify every existing entry before Store/Services can open the fixture.
    for folder, directories, files in os.walk(fixture, followlinks=False):
        for name in directories + files:
            qa.no_alias(Path(folder) / name, root)
    from pokemind.desktop.app import synthetic_release_root
    return synthetic_release_root(fixture)


class Runtime:
    def __init__(self, context):
        if context.marker['purpose'] != 'gui':
            raise ValueError('QA_GUI_PURPOSE_REQUIRED')
        self.context, self.fixture = context, None
        self.calls, self.blocked, self.last_receipt = 0, [], None
        # Reuse the existing test double, rather than inventing another client.
        import pytest
        from test_desktop_qt import Fake
        from pokemind.assistant import provider, codex_app_server
        from pokemind.desktop import window, images
        from pokemind import batch_public_research as research
        from qa_unified_desktop import InventedOfficialOpener
        from PySide6.QtWidgets import QFileDialog, QLabel
        from PySide6.QtGui import QDesktopServices
        import urllib.request
        import http.client

        self.patch = pytest.MonkeyPatch()
        patch, runtime = self.patch, self
        self.opener = InventedOfficialOpener()

        def blocked(*args, **kwargs):
            runtime.blocked.append('REAL_PROVIDER_OR_EXTERNAL_OPERATION_DISABLED')
            raise provider.ProviderError('QA_REAL_OPERATIONS_DISABLED')

        self.block_operation = blocked
        # Neutralize the real classes as well as aliases used by the window.
        for cls in (codex_app_server.CodexAppServer, provider.ClaudeCode, provider.LocalOllama):
            for name in ('__init__', 'health', 'configure', 'start', 'ask_stream', 'resume', 'status', 'compact'):
                patch.setattr(cls, name, blocked, raising=False)
        patch.setattr(provider, 'executable', blocked)
        patch.setattr(provider, 'spawn', blocked)
        patch.setattr(urllib.request, 'urlopen', blocked)
        patch.setattr(urllib.request.OpenerDirector, 'open', blocked)
        for name in ('connect', 'request', 'send'):
            patch.setattr(http.client.HTTPConnection, name, blocked)
        patch.setattr(images.ImageCache, '_get', blocked)
        patch.setattr(QDesktopServices, 'openUrl', blocked)
        # No native file picker may browse outside this fictional fixture.
        patch.setattr(QFileDialog, 'getOpenFileNames', lambda *a, **k: ([], ''))
        patch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: ('', ''))
        patch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: '')

        class OfflineFake(Fake):
            def health(self):
                return {'available': True, 'status': BANNER + ' · doublure locale'}

            def configure(self, *, development=False, **kwargs):
                if development:
                    return blocked()
                return super().configure(development=False, **kwargs)

            def ask_stream(self, prompt, history, emit, tool=None):
                runtime.calls += 1
                emit('[Réponse fixe fictive; aucun moteur IA contacté]\n')
                return super().ask_stream(prompt, history, emit, tool=None)

            status = compact = resume = blocked

        # Distinct subclasses preserve the window's isinstance(Ollama) branch.
        self.fake_types = tuple(type(name, (OfflineFake,), {}) for name in ('QaCodex', 'QaClaude', 'QaOllama'))
        for name, cls in zip(('CodexAppServer', 'ClaudeCode', 'LocalOllama'), self.fake_types):
            patch.setattr(window, name, cls)

        original_research = research.research

        def offline_research(root, **kwargs):
            runtime.check_fixture(root)
            if kwargs.get('topic') == 'rules':
                policy = {'mode': 'derived_fields_only', 'license': 'synthetic_author_owned',
                          'reference': 'invented-offline-qa-v1'}
                result = original_research(root, **(kwargs | {'opener': runtime.opener,
                    'official_policy': {url: policy for url in (
                        'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources',
                        'https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement')}}))
            else:
                result = original_research(root, **(kwargs | {'offline': True}))
            runtime.last_receipt = result
            return result

        def offline_matchups(root, **kwargs):
            runtime.check_fixture(root)
            return {'status': 'QA_OFFLINE_NO_COLLECTION', 'gets': 0, 'persisted': False,
                    'eligible_matches': 0, 'winrate': None}

        patch.setattr(research, 'research', offline_research)
        patch.setattr(research, 'research_matchups', offline_matchups)
        original_ingest = window.MainWindow.start_ingestion
        original_link = window.MainWindow.internal_link
        original_language = window.MainWindow.apply_language

        def offline_badge(widget):
            widget.permission_badge.setText('QA : outils et fournisseurs réels désactivés')
            widget.permission_badge.setStyleSheet('color:#ffdf8a;font-weight:bold')

        def offline_language(widget):
            original_language(widget)
            if hasattr(widget, 'chat_input'):
                widget.chat_input.setPlaceholderText('Exemples entièrement fictifs seulement.\nEnter : envoyer · Shift+Enter : nouvelle ligne')
                widget.attach_button.setText('Pièces jointes désactivées en QA')
                widget.cloud_consent.setText('J’active les réponses fictives locales de cette QA (aucun envoi cloud)')
                widget.context_status.setText('Contexte local fictif · aucun envoi à un fournisseur')

        def safe_ingest(widget, text=None, paths=None, kind='log'):
            runtime.check_fixture(widget.root)
            # Paste-only QA: even an invented attachment is refused before IO.
            if paths:
                widget.provider_status.setText('QA : fichiers désactivés. Colle uniquement les exemples fictifs du guide.')
                return
            return original_ingest(widget, text=text, paths=None, kind=kind)

        def safe_link(widget, url):
            if url.scheme() != 'pokemind':
                widget.provider_status.setText('QA hors ligne : liens externes désactivés.')
                return
            return original_link(widget, url)

        patch.setattr(window.MainWindow, 'start_ingestion', safe_ingest)
        patch.setattr(window.MainWindow, 'internal_link', safe_link)
        patch.setattr(window.MainWindow, 'update_permission_badge', offline_badge)
        patch.setattr(window.MainWindow, 'apply_language', offline_language)
        self.window_type, self.label_type = window.MainWindow, QLabel

    def check_fixture(self, root):
        self.context.validate_live()
        if self.fixture is None or qa.lexical(root) != self.fixture:
            raise ValueError('QA_EXPLICIT_FIXTURE_REQUIRED')

    def prepare(self, *, resume=False):
        self.context.validate_live()
        if resume:
            self.fixture = read_fixture(self.context)
        else:
            from qa_unified_desktop import prepare_release, LOG
            self.fixture = prepare_release(qa.PROJECT)
            for name, text in (('journal-fictif.txt', LOG),
                               ('journal-partiel.txt', 'Reference player: InventedSelf\nTurn # 1 - InventedSelf\'s Turn\n')):
                with (self.fixture / 'qa-inputs' / name).open('x', encoding='utf-8') as stream:
                    stream.write(text)
            with (self.context.root / MANIFEST).open('x', encoding='utf-8') as stream:
                json.dump({'kind': FORMAT, 'fixture': self.fixture.relative_to(self.context.root).as_posix()}, stream)
            if read_fixture(self.context) != self.fixture:
                raise ValueError('QA_FIXTURE_PREPARATION_FAILED')
        return self.fixture

    def window(self):
        self.check_fixture(self.fixture)
        if read_fixture(self.context) != self.fixture:
            raise ValueError('QA_FIXTURE_CHANGED')
        widget = self.window_type(self.fixture)
        widget.setWindowTitle(BANNER)
        label = self.label_type(BANNER + '\nCollage fictif seulement · fichiers, outils, fournisseurs et liens externes désactivés')
        label.setWordWrap(True)
        label.setStyleSheet('background:#593d0b;color:#fff1bc;padding:10px;font-weight:bold;')
        widget.setMenuWidget(label)
        widget.qa_banner = label
        for index in range(widget.provider.count()):
            widget.provider.setItemText(index, widget.provider.itemData(index).capitalize() + ' · doublure hors ligne')
        widget.cloud_consent.setText('J’active les réponses fictives locales de cette QA (aucun envoi cloud)')
        widget.attach_button.setEnabled(False)
        widget.card_images.setChecked(False)
        widget.card_images.setEnabled(False)
        widget.watch_logs.setChecked(False)
        widget.watch_logs.setEnabled(False)
        widget.apply_language()
        widget.provider_status.setText('Doublure locale prête · aucun moteur réel')
        return widget

    def summary(self):
        return {'fake_provider_calls': self.calls, 'invented_source_calls': self.opener.calls,
                'blocked_real_operations': len(self.blocked), **self.context.summary()}
