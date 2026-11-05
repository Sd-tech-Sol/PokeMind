from __future__ import annotations

import getpass
import logging
import logging.handlers

import pytest

from pokemind import diagnostics


def file_handlers():
    return [h for h in logging.getLogger(diagnostics.LOGGER).handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)]


@pytest.fixture
def journal(local_tmp):
    diagnostics.reset_for_tests()
    path = diagnostics.setup(local_tmp)
    yield local_tmp, path
    diagnostics.reset_for_tests()


def test_redaction_masks_paths_user_and_email_but_keeps_file_names(local_tmp):
    user = getpass.getuser()
    text = (f'Échec C:\\Users\\{user}\\Documents\\PokeMind\\data\\local\\pokemind.sqlite3 '
            f'et \\\\serveur\\partage\\deck.txt pour inventé@example.invalid, {user} aussi; '
            f'{local_tmp}\\src\\pokemind\\cards.py')
    masked = diagnostics.redact(text, local_tmp)
    assert 'C:\\Users' not in masked and '\\\\serveur' not in masked
    assert 'example.invalid' not in masked
    assert '<chemin>/pokemind.sqlite3' in masked and '<chemin>/deck.txt' in masked
    assert '<projet>' in masked and 'cards.py' in masked
    if len(user) >= 3:
        assert user.casefold() not in masked.casefold()


def test_exception_is_written_with_traceback_and_redacted(journal):
    root, path = journal
    try:
        raise RuntimeError('lecture refusée ' + str(root / 'data/local/battle_logs/partie.txt'))
    except RuntimeError:
        diagnostics.get('desktop').exception('Tâche de fond en échec · %s', 'RuntimeError')
    content = path.read_text(encoding='utf-8')
    assert 'Tâche de fond en échec · RuntimeError' in content
    assert 'Traceback' in content and 'test_diagnostics.py' in content
    assert str(root) not in content and 'partie.txt' in content


def test_setup_is_idempotent_and_report_has_versions_and_tail(journal):
    root, path = journal
    assert diagnostics.setup(root) == path
    assert len(file_handlers()) == 1
    diagnostics.get('assistant').warning('Réponse indisponible · %s', 'CODEX_TIMEOUT')
    report = diagnostics.report(root)
    assert report.startswith('PokeMind ') and 'Python ' in report
    assert 'CODEX_TIMEOUT' in report and 'Démarrage PokeMind' in report


def test_journal_rotates_at_its_size_cap(journal, monkeypatch):
    root, path = journal
    handler, = file_handlers()
    monkeypatch.setattr(handler, 'maxBytes', 2000)
    for number in range(200):
        diagnostics.get().info('ligne synthétique %04d %s', number, 'x' * 40)
    handler.flush()
    rotated = sorted(p.name for p in path.parent.iterdir())
    assert rotated[:2] == ['pokemind.log', 'pokemind.log.1']
    assert len(rotated) <= diagnostics.BACKUPS + 1
    assert all(p.stat().st_size <= 4000 for p in path.parent.iterdir())


def test_report_puts_recent_errors_first_with_their_exception(journal):
    root, path = journal
    for number in range(7):
        try:
            [][number]
        except IndexError:
            diagnostics.get('desktop').exception('Échec inventé %d', number)
    for number in range(300):
        diagnostics.get().info('ligne synthétique %04d', number)
    report = diagnostics.report(root)
    summary, tail = report.split('Fin du journal :', 1)
    assert 'Erreurs récentes (5) :' in summary and 'Échec inventé 6' in summary and 'Échec inventé 1' not in summary
    assert 'Échec inventé 2 → IndexError: list index out of range' in summary
    assert 'ligne synthétique 0299' in tail and 'Échec inventé' not in tail  # the tail alone would have lost them
    assert tail.rstrip().endswith('ligne synthétique 0299')  # the newest lines are kept, never cut off
    assert len(report) <= diagnostics.REPORT_CHARS and report.startswith('PokeMind ')


def test_report_without_journal_is_explicit(local_tmp):
    diagnostics.reset_for_tests()
    assert 'Journal vide.' in diagnostics.report(local_tmp)
