"""Dedicated foreground Windows launcher; no owner executable or normal entry."""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
from pokemind import synthetic_qa as qa


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', help='Explicit relative envelope printed by a previous offline GUI launch')
    parser.add_argument('--exercise', choices=('first', 'resume'), help='Technical reception, not owner acceptance')
    args = parser.parse_args()
    if args.exercise and (args.exercise == 'resume') != (args.workspace is not None):
        raise ValueError('QA_EXERCISE_PHASE_MISMATCH')
    if os.name != 'nt':
        raise ValueError('QA_NATIVE_WINDOWS_REQUIRED')
    context = qa.bootstrap(purpose='gui', resume=args.workspace)
    os.environ['QT_QPA_PLATFORM'] = 'windows'
    sys.path.insert(0, str(qa.PROJECT / 'tests'))
    from qa_offline_runtime import Runtime, BANNER
    runtime = Runtime(context)  # guards installed before fixture or window
    runtime.prepare(resume=args.workspace is not None)
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    app.setApplicationName('PokeMind Synthetic Offline QA')
    app.setOrganizationName('PokeMind Synthetic Offline QA')
    if app.platformName() != 'windows':
        raise ValueError('QA_NATIVE_WINDOWS_REQUIRED')
    widget = runtime.window()
    relative = context.root.relative_to(qa.PROJECT).as_posix()
    print(BANNER, flush=True)
    print('Workspace : ' + relative, flush=True)
    print("Réouverture : .\\scripts\\Start-PokeMind-Synthetic-Offline-QA.ps1 -Workspace '" + relative + "'", flush=True)
    widget.show()
    if args.exercise:
        from PySide6.QtCore import QTimer
        from qa_offline_reception import exercise
        # Exercise the same native event loop used by a normal manual launch.
        app.setQuitOnLastWindowClosed(False)
        outcome = {'code': 1}
        def receive():
            try:
                outcome['code'] = exercise(app, widget, runtime, phase=args.exercise)
            except qa.SecurityIncident:
                outcome['code'] = 2
            except Exception as exc:
                print(json.dumps({'reception_error': type(exc).__name__, 'details_redacted': True}), flush=True)
            finally:
                app.exit(outcome['code'])
        QTimer.singleShot(0, receive)
    code = app.exec()
    if args.exercise:
        code = outcome['code']
    result = {'task': qa.TASK, 'exit_code': code, 'owner_acceptance': False, **runtime.summary()}
    target = context.root / ('gui-' + context.temp.name + '.json')
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result), flush=True)
    app.shutdown()
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'startup_or_reception_error': type(exc).__name__, 'details_redacted': True}), flush=True)
        raise SystemExit(1)
