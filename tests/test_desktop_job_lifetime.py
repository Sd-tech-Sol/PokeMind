"""Background jobs never leave a wrapper on a destroyed object (owner, 2026-11-19, D-319).

The pools used to delete each Job (a QRunnable) at the end of run() while Python still held it in `jobs` and
received it in `job_finished`: a wrapper on a destroyed C++ object, which crashed the native QA in the garbage
collector (access violation). Now the pools keep it and `job_finished` frees it. Hundreds of jobs in
both pools (and a detached one), pages changing meanwhile, `gc.collect()` all along: no crash, every finished job
still valid when it reports, and every one freed afterwards (no leak of jobs or of what they captured). The check
runs in a process of its own, so a crash fails the test instead of taking pytest down.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
pytest.importorskip('PySide6')

HERE = Path(__file__).resolve().parent
JOBS_PER_POOL = 300


def test_hundreds_of_jobs_in_both_pools_survive_page_changes_and_garbage_collection(local_tmp):
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', LOCALAPPDATA=str(local_tmp), POKEMIND_TEST_OFFLINE='1',
               PYTHONFAULTHANDLER='1', PYTHONPATH=os.pathsep.join([str(HERE), str(HERE.parent / 'src')]))
    env.pop('POKEMIND_DATA_ROOT', None)
    done = subprocess.run([sys.executable, '-c', 'import sys, test_desktop_job_lifetime as t; t.check(sys.argv[1])',
                           str(local_tmp)], env=env, cwd=str(local_tmp), capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=300)
    assert done.returncode == 0 and 'JOBS : OK' in done.stdout, (done.stdout + done.stderr)[-4000:]


def check(root):
    """Run in its own process (test above)."""
    import gc
    import time
    import weakref
    import shiboken6
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from pokemind import seasons
    from pokemind.assistant import provider
    from pokemind.assistant.provider import ProviderAdapter
    from pokemind.desktop import window
    from test_desktop_narrow_window import report
    application = QApplication.instance() or QApplication([])
    seasons.OFFICIAL = ()
    provider.terminal_model = lambda: None
    games = report()

    class Fake(ProviderAdapter):
        def health(self):
            return {'available': True, 'status': 'Invented provider'}

    def load(services, update=False, **kwargs):
        services.report, services.learning = games, None
        return {'report': games, 'learning': None}
    window.Services.load = load
    window.Services.deck_options = lambda services: []
    window.CodexAppServer = window.ClaudeCode = Fake
    folder = Path(root) / 'jobs'
    folder.mkdir(parents=True, exist_ok=True)
    window.Store(folder).write('preferences.json', {'cloud_consent': False, 'sharing': 'public', 'advanced_mode': True})
    ui = window.MainWindow(folder)
    ui.resize(1100, 700)
    ui.show()

    def pump(seconds, until=lambda: False):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not until():
            application.processEvents()
            QTest.qWait(5)

    pump(10, lambda: not ui.jobs and not ui.stack.transition.isVisible())
    valid_when_reported, results, mine = [], [], []
    original = ui.job_finished

    def spy(job):
        if any(job is ref() for ref in mine):
            valid_when_reported.append(shiboken6.isValid(job))
        original(job)
    ui.job_finished = spy  # submit() connects to the attribute, so every job below reports here first

    class Captured:
        """Something a job's closure holds, as real jobs hold rows and decks: it must be freed with the job."""
    captured = []
    for number in range(JOBS_PER_POOL * 2):
        thing = Captured()
        captured.append(weakref.ref(thing))
        pool = ui.image_pool if number % 2 else ui.pool
        ui.submit(lambda e, n=number, t=thing: time.sleep(0.001 * (n % 5)) or n, results.append, pool=pool,
                  priority=number % 3 - 1)
        mine.append(weakref.ref(ui.jobs[-1]))
        if number % 40 == 0:
            ui.navigation.setCurrentRow(number // 40 % 7)
            application.processEvents()
            gc.collect()
        del thing
    ui.submit(lambda e, t=Captured(): 'detached', results.append, detached=True)
    mine.append(weakref.ref(ui.jobs[-1]))
    end = time.monotonic() + 120
    page = 0
    while time.monotonic() < end and any(ref() is not None and ref() in ui.jobs for ref in mine):
        page = (page + 1) % 7
        ui.navigation.setCurrentRow(page)
        application.processEvents()
        gc.collect()
        QTest.qWait(5)
    pump(1.5)  # the last signals are delivered; job_finished frees each job
    gc.collect()
    problems = []
    if len(results) != JOBS_PER_POOL * 2 + 1:
        problems.append('résultats %d / %d' % (len(results), JOBS_PER_POOL * 2 + 1))
    if len(valid_when_reported) != len(mine) or not all(valid_when_reported):
        problems.append('jobs invalides à la fin : %d / %d valides' % (sum(valid_when_reported), len(mine)))
    alive = sum(ref() is not None for ref in mine)
    if alive:
        problems.append('%d jobs jamais libérés' % alive)
    held = sum(ref() is not None for ref in captured)
    if held:
        problems.append('%d objets capturés jamais libérés' % held)
    ui.close()
    pump(10, lambda: not ui.isVisible())
    ui.pool.waitForDone(5000)
    ui.image_pool.waitForDone(5000)
    gc.collect()
    print('\n'.join(problems) or 'JOBS : OK')
    sys.stdout.flush()
    os._exit(1 if problems else 0)
