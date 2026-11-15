"""PokeMind brand images, all derived from the approved card (assets/branding/pokemind-tcg-coach-original.png).

    python scripts/make_icon.py --card                       # src/pokemind/desktop/branding/pokemind-card.png
    python scripts/make_icon.py build/pokemind.ico           # Windows icon, every size (PNG entries)
    python scripts/make_icon.py docs/assets/pokemind-logo.png --size 336 --whole
    python scripts/make_icon.py build/installer/small.bmp --size 110               # square, on white
    python scripts/make_icon.py build/installer/large.bmp --size 164 --height 314 --background '#07142F'

The card is never redrawn: --card checks the original's SHA-256, makes only the white page outside its rounded
corners transparent and halves it (1060 x 1484 -> 530 x 742, same proportions). Everything else is scaled from that.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import struct
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

ORIGINAL = ROOT / 'assets' / 'branding' / 'pokemind-tcg-coach-original.png'
ORIGINAL_SHA256 = '30824d84f594be0e1fe33b3e9531f487e497252e17d7a16ff57763b787d7f0f5'
CORNER = 96      # the rounded corners fit in 96 px squares of the original (white reaches 66 px along an edge)
NEAR_WHITE = 150  # every channel at least this light: page around the card, not the card's navy border


def card_image(original=ORIGINAL):
    """The packaged card: the original's pixels, page corners transparent, exactly half size."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    data = Path(original).read_bytes()
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise SystemExit('Carte originale modifiée : SHA-256 inattendu, aucune image générée.')
    image = QImage.fromData(data).convertToFormat(QImage.Format.Format_ARGB32)
    width, height = image.width(), image.height()
    for corner_x, corner_y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        _clear_page(image, corner_x, corner_y)
    image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    half = image.scaled(width // 2, height // 2, Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)  # 1060 and 1484 are even: same ratio
    return half.convertToFormat(QImage.Format.Format_ARGB32)


def _clear_page(image, start_x, start_y):
    """Flood the near-white page from one corner, inside that corner's square only."""
    width, height = image.width(), image.height()
    left, right = (0, CORNER) if start_x == 0 else (width - CORNER, width)
    top, bottom = (0, CORNER) if start_y == 0 else (height - CORNER, height)
    pending, seen = deque([(start_x, start_y)]), {(start_x, start_y)}
    while pending:
        x, y = pending.popleft()
        value = image.pixel(x, y)
        if min((value >> 16) & 255, (value >> 8) & 255, value & 255) < NEAR_WHITE:
            continue
        image.setPixel(x, y, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if left <= nx < right and top <= ny < bottom and (nx, ny) not in seen:
                seen.add((nx, ny))
                pending.append((nx, ny))


def png_bytes(size, whole=False):
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from pokemind.desktop.theme import card_pixmap, logo_pixmap
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    (card_pixmap(size, 1.0) if whole else logo_pixmap(size, 1.0)).save(buffer, 'PNG')
    buffer.close()
    return bytes(data)


def ico_bytes(sizes):
    images = [(size, png_bytes(size)) for size in sizes]
    header = struct.pack('<HHH', 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, payload = b'', b''
    for size, data in images:
        side = 0 if size >= 256 else size  # 0 means 256 in an ICO directory entry
        entries += struct.pack('<BBBBHHII', side, side, 0, 0, 1, 32, len(data), offset + len(payload))
        payload += data
    return header + entries + payload


def bitmap(width, height, background):
    """Opaque image for Inno Setup: the whole card centred on `background`, never stretched."""
    from PySide6.QtGui import QColor, QImage, QPainter
    from pokemind.desktop.theme import card_pixmap, card_width
    card_height = min(height, int(width * 742 / 530))
    while card_width(card_height) > width:
        card_height -= 1
    picture = card_pixmap(card_height, 1.0)
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor(background))
    painter = QPainter(image)
    painter.drawPixmap((width - picture.width()) // 2, (height - picture.height()) // 2, picture)
    painter.end()
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('destination', type=Path, nargs='?')
    parser.add_argument('--card', action='store_true', help='regenerate the packaged card from the original')
    parser.add_argument('--size', type=int, default=256, help='side of a square image, or width of a .bmp')
    parser.add_argument('--height', type=int, help='.bmp height (default: square)')
    parser.add_argument('--whole', action='store_true', help='.png: the whole card, --size pixels tall')
    parser.add_argument('--background', default='#ffffff', help='.bmp background colour')
    args = parser.parse_args(argv)
    from PySide6.QtGui import QGuiApplication
    application = QGuiApplication.instance() or QGuiApplication([])
    if args.card:
        from pokemind.desktop.theme import BRAND_CARD
        destination = args.destination or BRAND_CARD
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not card_image().save(str(destination), 'PNG'):
            raise SystemExit('Écriture de la carte impossible.')
        print(destination.name)
        return
    if args.destination is None:
        parser.error('destination requise')
    from pokemind.desktop.theme import logo_icon_sizes
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = args.destination.suffix.casefold()
    if suffix == '.ico':
        args.destination.write_bytes(ico_bytes(logo_icon_sizes()))
    elif suffix == '.bmp':
        bitmap(args.size, args.height or args.size, args.background).save(str(args.destination), 'BMP')
    else:
        args.destination.write_bytes(png_bytes(args.size, args.whole))
    del application
    print(args.destination.name)


if __name__ == '__main__':
    main()
