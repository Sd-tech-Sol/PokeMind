"""Write the PokeMind logo as a Windows .ico (PNG entries), a single .png, or a .bmp on white (installer).

    python scripts/make_icon.py build/pokemind.ico
    python scripts/make_icon.py docs/assets/pokemind-logo.png --size 256
    python scripts/make_icon.py build/installer/wizard-small.bmp --size 110
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def png_bytes(size):
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from pokemind.desktop.theme import logo_pixmap
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    logo_pixmap(size).save(buffer, 'PNG')
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--size', type=int, default=256)
    args = parser.parse_args(argv)
    from PySide6.QtGui import QGuiApplication
    from pokemind.desktop.theme import logo_icon_sizes
    application = QGuiApplication.instance() or QGuiApplication([])
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    if args.destination.suffix.casefold() == '.ico':
        args.destination.write_bytes(ico_bytes(logo_icon_sizes()))
    elif args.destination.suffix.casefold() == '.bmp':  # Inno Setup's wizard corner: opaque, on white
        from PySide6.QtGui import QColor, QImage, QPainter
        from pokemind.desktop.theme import logo_pixmap
        image = QImage(args.size, args.size, QImage.Format.Format_RGB32)
        image.fill(QColor('#ffffff'))
        painter = QPainter(image)
        painter.drawPixmap(0, 0, logo_pixmap(args.size))
        painter.end()
        image.save(str(args.destination), 'BMP')
    else:
        args.destination.write_bytes(png_bytes(args.size))
    del application
    print(args.destination.name)


if __name__ == '__main__':
    main()
