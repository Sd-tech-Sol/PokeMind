"""Capture/test real Deck Lab controls with invented fixtures in an isolated copy.

python scripts/qa_decklab_responsive.py --baseline-ref d6efdd2 --label before
python scripts/qa_decklab_responsive.py --label after --scale 1.25
No installed application, personal data, network or model is used.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import uuid

from local_gate import ROOT, copy_tree


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=('before', 'after'), default='after')
    parser.add_argument('--scale', choices=('1', '1.25'), default='1.25')
    parser.add_argument('--baseline-ref', help='Restore only window.py from this Git ref')
    parser.add_argument('--select', help='Optional pytest -k expression for a focused diagnostic')
    options = parser.parse_args()
    target = ROOT / 'build' / ('qadr-' + uuid.uuid4().hex[:8])
    target.mkdir(parents=True)
    copy_tree(target)
    if options.baseline_ref:
        relative = 'src/pokemind/desktop/window.py'
        result = subprocess.run(['git', 'show', options.baseline_ref + ':' + relative],
                                cwd=ROOT, capture_output=True, check=True)
        (target / relative).write_bytes(result.stdout)
    output = ROOT / 'build/qa-decklab-responsive' / (options.label + '-' + options.scale)
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, POKEMIND_TEST_OFFLINE='1', QT_QPA_PLATFORM='windows',
               QT_SCALE_FACTOR=options.scale, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(target / 'src'), POKEMIND_CONTROLS_QA_DIR=str(output))
    for name in ('POKEMIND_SYNTHETIC_QA_ROOT', 'POKEMIND_SYNTHETIC_QA_TOKEN', 'POKEMIND_DATA_ROOT'):
        env.pop(name, None)
    selection = options.select or ('deck_controls_layout' if options.baseline_ref else 'deck_controls or premium_gallery')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                             'tests/test_desktop_qt.py', '-k', selection], cwd=target,
                            env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (output / 'pytest.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    print(result.stdout[-18000:])
    print('Synthetic copy retained:', target.relative_to(ROOT))
    print('Local captures:', output.relative_to(ROOT))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
