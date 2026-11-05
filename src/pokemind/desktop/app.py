"""Native launch entry point, also used by the windowed Windows executable."""
from __future__ import annotations
from pokemind.desktop.i18n import T, J, display

import sys
import os
import re
from pathlib import Path


def synthetic_release_root(root):
    """Reject ordinary projects before creating any window or reading data."""
    from pokemind.battle_batch import safe_path
    root = Path(root).absolute()
    if root.parent.name != 'build' or not re.fullmatch('synthetic-release-[0-9a-f]{32}', root.name):
        raise ValueError('SYNTHETIC_RELEASE_ROOT_REQUIRED')
    marker = safe_path(root.parent.parent, root / '.orchestrator/SYNTHETIC_QA_ONLY')
    if marker.stat().st_nlink != 1 or marker.read_bytes() != b'POKEMIND_SYNTHETIC_RELEASE_QA_V1\n':
        raise ValueError('SYNTHETIC_RELEASE_MARKER_REQUIRED')
    return root


def human_size(count):
    return ('%.1f Go' % (count / 1e9)) if count >= 1e9 else ('%d Mo' % max(1, round(count / 1e6)))


def offer_move(project):
    """Ask once, then copy data/local out of the project with a progress bar (original untouched).

    Returns (data root, state, outcome); the caller logs the outcome once diagnostics are set up.
    """
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QProgressDialog
    from pokemind.desktop.i18n import QMessageBox
    from pokemind import data_location
    target = data_location.choose_target()
    try:
        files, _ = data_location.inventory(project)
    except (ValueError, OSError) as error:
        return project, 'project', 'inventaire impossible · ' + str(error.args[0] if error.args else type(error).__name__)[:60]
    size = human_size(sum(size for _, size in files))
    answer = QMessageBox.question(None, T('Sortir tes données du projet'),
        T('Tes données PokeMind (combats, decks, discussions, mémoire) sont encore dans le dossier du projet, '
          'où un nettoyage Git ou un agent pourrait les effacer. PokeMind peut les copier dans :')
        + '\n' + str(target) + '\n(' + size + ', ' + str(len(files)) + ' ' + T('fichiers, chacun vérifié).')
        + '\n\n' + T('L’original reste intact dans le projet. Copier maintenant et utiliser la copie?'),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
    if answer != QMessageBox.StandardButton.Yes:
        data_location.use_project(project, 'declined')
        return project, 'project', 'copie refusée par le propriétaire'
    dialog = QProgressDialog(T('Copie vérifiée de tes données…'), T('Annuler'), 0, 1000)
    dialog.setWindowTitle('PokeMind')
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.show()

    def progress(done, total):
        dialog.setValue(int(done * 1000 / max(total, 1)))
        dialog.setLabelText(T('Copie vérifiée de tes données…') + ' ' + human_size(done) + ' / ' + size)
        QApplication.processEvents()
    try:
        receipt = data_location.copy_out(project, target, progress=progress, cancelled=dialog.wasCanceled)
    except (ValueError, OSError) as error:
        dialog.close()
        code = str(error.args[0] if error.args else type(error).__name__)[:60]
        QMessageBox.warning(None, 'PokeMind', T('Copie interrompue :') + ' ' + code + '. '
            + T('Rien n’a été remplacé; PokeMind continue avec le dossier du projet et te reproposera la copie.'))
        return project, 'project', 'copie interrompue · ' + code
    dialog.close()
    QMessageBox.information(None, 'PokeMind', T('Copie vérifiée :') + ' ' + str(receipt['files']) + ' '
        + T('fichiers. PokeMind utilise maintenant :') + '\n' + str(target) + '\n\n'
        + T('L’original reste dans le projet. Vérifie tes combats, decks et discussions; en cas de problème : '
            'Réglages → « Revenir au dossier du projet ».'))
    return target, 'outside', 'données copiées hors du projet · %d fichiers vérifiés' % receipt['files']


def relaunch(project_root):
    """Start PokeMind again (after a reset request): the same executable, or the same command from the sources."""
    from PySide6.QtCore import QProcess
    if getattr(sys, 'frozen', False):
        started = QProcess.startDetached(sys.executable, [], str(Path(sys.executable).parent))
    else:
        started = QProcess.startDetached(sys.executable, ['-m', 'pokemind', 'desktop'], str(project_root))
    return bool(started[0] if isinstance(started, tuple) else started)


def reset_notice(reset):
    """Tell the owner what the reset did, before the welcome assistant."""
    from pokemind.desktop.i18n import QMessageBox
    from pokemind.desktop.reset_dialog import LABELS
    if reset['status'] == 'RESET':
        head = (T('PokeMind a été réinitialisé.') if reset.get('full') else
                T('Données retirées :') + ' ' + J(', ', [LABELS[c] for c in reset.get('categories', ())]) + '.')
        text = head + '\n\n' + (
            T('Une copie de tes anciennes données est gardée ici :') + '\n' + reset['kept_copy'] if reset.get('kept_copy')
            else T('Les anciennes données ont été effacées.'))
        QMessageBox.information(None, 'PokeMind', text)
        return
    text = T('La réinitialisation n’a pas pu se faire : un fichier était encore utilisé. Rien n’a été effacé; '
             'recommence depuis Réglages, Données.')
    if reset.get('blocked'):
        text = text + '\n\n' + T('Élément encore utilisé :') + ' ' + reset['blocked']
    if reset.get('kept_copy'):
        text = text + '\n\n' + T('Une partie des données est restée ici :') + '\n' + reset['kept_copy']
    QMessageBox.warning(None, 'PokeMind', text)


def restore_notice(restored):
    """Tell the owner what « Restaurer une archive… » did, and where the data it replaced is kept."""
    from pokemind import data_archive
    from pokemind.desktop.i18n import QMessageBox
    if restored['status'] == 'RESTORED':
        text = T('Archive restaurée :') + ' ' + restored['zip'] + '\n' + T('Fichiers remis en place :') + ' ' + str(restored['files'])
        if restored.get('previous_archive'):
            text += '\n\n' + T('Tes données d’avant sont gardées dans :') + '\n' + restored['previous_archive']
        QMessageBox.information(None, 'PokeMind', text)
        return
    reason = data_archive.MESSAGES.get(restored.get('error'), '')
    QMessageBox.warning(None, 'PokeMind', T('La restauration n’a pas pu se faire. Tes données actuelles sont restées en place.')
                        + ('\n\n' + T(reason) if reason else '') + ('\n\n' + restored['zip'] if restored.get('zip') else ''))


def first_run(root):
    """Show the welcome assistant once, when no preferences were ever saved for this data folder.

    Returns (outcome, catalogue wanted): the card catalogue is offered when it is not on this PC yet.
    """
    from pokemind import catalog_download, diagnostics
    from pokemind.assistant.sessions import Store
    from pokemind.desktop.i18n import set_language
    from pokemind.desktop.theme import palette, stylesheet
    from pokemind.desktop.welcome import WelcomeWizard
    try:
        store = Store(root)
        if store.read('preferences.json') is not None:
            return 'known', False
        preferences = store.preferences()
        set_language(preferences['language'])
        wizard = WelcomeWizard(preferences, catalog_missing=not catalog_download.ready(root))
        wizard.setPalette(palette('dark'))
        wizard.setStyleSheet(stylesheet('dark'))
        accepted = bool(wizard.exec())
        chosen = wizard.choices() if accepted else {'language': wizard.choices()['language']}
        store.write('preferences.json', store.preferences() | chosen)
        return ('accepted' if accepted else 'closed'), accepted and wizard.wants_catalog()
    except (ValueError, OSError):
        diagnostics.get('desktop').exception('Assistant de premier lancement indisponible')
        return 'failed', False


def launch(root=None):
    from PySide6.QtWidgets import QApplication
    from pokemind.desktop.i18n import QFileDialog, QMessageBox, set_language
    from pokemind.desktop.window import MainWindow
    if sys.platform == 'win32':  # the taskbar shows PokeMind's logo, not the Python one
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PokeMind.Desktop')
        except (AttributeError, OSError):
            pass
    app = QApplication.instance() or QApplication(sys.argv[:1])
    from pokemind.assistant.sessions import system_language
    set_language(system_language())  # dialogs before the window; the window then applies the saved choice
    app.setApplicationName('PokeMind')
    app.setOrganizationName('PokeMind Local')
    from pokemind.desktop.theme import logo_icon
    app.setWindowIcon(logo_icon())
    selected = Path(root).absolute() if root else Path.cwd()
    frozen = getattr(sys, 'frozen', False)
    if frozen:  # dist/PokeMind/PokeMind.exe inside the project; an installed copy has no project around it
        parents = Path(sys.executable).parents
        if len(parents) > 2 and (parents[2] / '.orchestrator/PROJECT_SPEC.md').is_file():
            selected = parents[2]
    release_qa = os.environ.get('POKEMIND_DESKTOP_SMOKE') == 'synthetic-release'
    if release_qa:
        try:
            selected = synthetic_release_root(selected)
            from qa_unified_desktop import exercise_release
        except (ValueError, OSError, ImportError):
            return 2
    standalone = not release_qa and not (selected / '.orchestrator/PROJECT_SPEC.md').is_file() and (
        frozen or os.environ.get('POKEMIND_STANDALONE') == '1')
    if standalone and os.environ.get('POKEMIND_DESKTOP_SMOKE') and not os.environ.get('POKEMIND_DATA_ROOT'):
        return 2  # release QA never opens a real %LOCALAPPDATA%\PokeMind
    if not standalone and not (selected / '.orchestrator/PROJECT_SPEC.md').is_file():
        chosen = QFileDialog.getExistingDirectory(None, T('Choisir le dossier de projet PokeMind'))
        if not chosen:
            return 1
        selected = Path(chosen)
        if not (selected / '.orchestrator/PROJECT_SPEC.md').is_file():
            QMessageBox.information(None, 'PokeMind', T('Ce dossier ne contient pas le projet PokeMind.'))
            return 2
    from pokemind import diagnostics, data_location
    outcome = None
    if standalone:
        try:
            selected, project = data_location.standalone()
        except (ValueError, OSError):
            QMessageBox.warning(None, 'PokeMind', T('Le dossier de données PokeMind est inaccessible.'))
            return 2
        data_state = 'standalone'
    else:
        project = selected
        selected, data_state = data_location.resolve(project)
    reset = restored = None
    if not release_qa:  # a reset asked from the window, before anything opens a file in data/local
        from pokemind import data_reset
        try:
            reset = data_reset.apply(selected)
        except (ValueError, OSError) as error:
            reset = {'status': 'FAILED', 'error': type(error).__name__, 'erased': False, 'kept_copy': None}
        from pokemind import data_archive
        try:  # « Restaurer une archive… »: the current data is archived first, then replaced
            restored = data_archive.apply_restore(selected)
        except (ValueError, OSError) as error:
            restored = {'status': 'FAILED', 'error': type(error).__name__, 'zip': ''}
        if (reset or restored) and not standalone:
            selected, data_state = data_location.resolve(project)
    if data_state == 'offer' and not release_qa:
        selected, data_state, outcome = offer_move(project)
    diagnostics.setup(selected)
    if outcome:
        diagnostics.get('desktop').info('Dossier de données · %s', outcome)
    if reset:
        diagnostics.get('desktop').info('Réinitialisation · %s · %s éléments%s', reset['status'], reset.get('items', 0),
                                        ' · bloqué : ' + reset['blocked'] if reset.get('blocked') else '')
    if restored:
        diagnostics.get('desktop').info('Restauration · %s · %s fichiers%s', restored['status'], restored.get('files', 0),
                                        ' · ' + restored['error'] if restored.get('error') else '')
    if data_state == 'missing':
        diagnostics.get('desktop').warning('Dossier de données introuvable; dossier du projet utilisé')
        QMessageBox.warning(None, 'PokeMind', T('Le dossier de données copié est introuvable. PokeMind utilise le '
            'dossier du projet; Réglages permet de refaire la copie.'))
    if standalone:
        diagnostics.get('desktop').info('Mode autonome · données dans le dossier de l’application')
    catalog = False
    if not release_qa and os.environ.get('POKEMIND_DESKTOP_SMOKE') != '1':
        if reset:
            reset_notice(reset)
        if restored:
            restore_notice(restored)
        welcome, catalog = first_run(selected)
        diagnostics.get('desktop').info('Premier lancement · %s', welcome)
    try:
        window = MainWindow(selected, project_root=project, data_state=data_state, download_catalog=catalog)
    except (ValueError, OSError):
        diagnostics.get('desktop').exception('Ouverture de la fenêtre impossible')
        QMessageBox.warning(None, 'PokeMind', T('Préférences ou données locales indisponibles. Aucun historique remplacé. Vérifier les fichiers de l’application dans data/local/chat.'))
        return 2
    window.show()
    if release_qa:
        return exercise_release(app, window)
    if os.environ.get('POKEMIND_DESKTOP_SMOKE') == '1':
        # Explicit local release QA. Never enabled by ordinary launches or CI.
        import json
        import time
        from PySide6.QtCore import QTimer
        started = time.monotonic()
        verified = False
        smoke_code = 2
        def verify_visible():
            nonlocal verified, smoke_code
            ready = bool(window.services.report) and bool(window.deck_rows) and bool(window.gallery.tiles) and not window.data_busy and not window._startup_pending
            if not verified and (ready or time.monotonic() - started > 120):
                proof = {'frozen': bool(getattr(sys, 'frozen', False)), 'visible': window.isVisible(),
                    'windows_platform': app.platformName() == 'windows', 'report_loaded': bool(window.services.report),
                    'exact60_available': bool(window.deck_rows), 'pages': window.stack.count(),
                    'gallery_populated': bool(window.gallery.tiles),
                    'ingest_controls_available': hasattr(window.chat_input, 'files_dropped') and hasattr(window, 'view_import_button'),
                    'activity_available': hasattr(window.activity, 'elapsed'),
                    'startup_option_available': hasattr(window, 'startup_refresh'),
                    'terminal_available': all(b.isEnabled() for b in window.terminal_buttons.values())}
                target = selected / 'data/local/desktop-dev'
                target.mkdir(parents=True, exist_ok=True)
                (target / 'exe-smoke.json').write_text(json.dumps(proof), encoding='utf-8')
                window.grab().save(str(target / 'exe-smoke.png'))
                verified, smoke_code = True, 0 if ready else 2
            if verified:
                window.close()
                if not window.isVisible() and not window.pool.activeThreadCount() and not window.image_pool.activeThreadCount():
                    timer.stop()
                    app.exit(smoke_code)
        timer = QTimer()
        timer.timeout.connect(verify_visible)
        timer.start(250)
    return app.exec()


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    raise SystemExit(launch())
