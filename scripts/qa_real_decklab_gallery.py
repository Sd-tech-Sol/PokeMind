"""Manually capture the real MainWindow with invented fixtures, in an isolated copy.

python scripts/qa_real_decklab_gallery.py --label before
python scripts/qa_real_decklab_gallery.py --label after --scale 1.25
No installed application, personal root, network, or model is used.
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='after', choices=('before', 'after'))
    parser.add_argument('--scale', default='1.25', choices=('1', '1.25'))
    parser.add_argument('--baseline-ref', help='Read only the three gallery source files at this Git ref')
    options = parser.parse_args()
    target = ROOT / 'build' / ('qarg-' + uuid.uuid4().hex[:8])
    target.mkdir(parents=True)
    copy_tree(target)
    if options.baseline_ref:
        for name in ('widgets.py', 'card_art.py', 'theme.py'):
            relative = 'src/pokemind/desktop/' + name
            value = subprocess.run(['git', 'show', options.baseline_ref + ':' + relative],
                                   cwd=ROOT, capture_output=True, check=True).stdout
            (target / relative).write_bytes(value)
    output = ROOT / 'build/qa-real-decklab-gallery' / (options.label + '-' + options.scale)
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, POKEMIND_TEST_OFFLINE='1', QT_QPA_PLATFORM='windows',
               QT_SCALE_FACTOR=options.scale, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(target / 'src'), POKEMIND_GALLERY_QA_DIR=str(output))
    if options.baseline_ref:
        env['POKEMIND_GALLERY_QA_BASELINE'] = '1'
    for name in ('POKEMIND_SYNTHETIC_QA_ROOT', 'POKEMIND_SYNTHETIC_QA_TOKEN', 'POKEMIND_DATA_ROOT'):
        env.pop(name, None)
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                             'tests/test_desktop_qt.py', '-k',
                             'premium_gallery_layout' if options.baseline_ref else 'premium_gallery'], cwd=target,
                            env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (output / 'pytest.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    frames = sorted((output / 'frames').glob('*.png'))
    if frames and not options.baseline_ref:
        from PIL import Image
        pictures = [Image.open(frame).convert('RGB') for frame in frames]
        pictures[0].save(output / 'hover.gif', save_all=True, append_images=pictures[1:],
                         duration=50, loop=0)
        for picture in pictures:
            picture.close()
    print(result.stdout[-12000:])
    print('Synthetic copy retained:', target.relative_to(ROOT))
    print('Local captures:', output.relative_to(ROOT))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
