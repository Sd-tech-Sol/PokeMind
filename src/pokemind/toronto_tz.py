"""ZoneInfo Toronto portable pour les installations Windows sans paquet tzdata.

Le repli TZif encode la règle IANA moderne EST/EDT de Toronto. Les cycles PokeMind
visent les dates actuelles et futures; ils n'utilisent pas cette table pour une
décision historique antérieure au régime moderne.
"""

from __future__ import annotations

import io
import struct
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _portable_tzif() -> bytes:
    counts = struct.pack(">6l", 0, 0, 0, 0, 1, 4)
    header = b"TZif2" + (b"\0" * 15) + counts
    standard = struct.pack(">lbb", -18_000, 0, 0) + b"EST\0"
    # Règle IANA/POSIX actuelle : deuxième dimanche de mars, premier dimanche
    # de novembre. ZoneInfo interprète ensuite elle-même offsets et ambiguïtés.
    return header + standard + header + standard + b"\nEST5EDT,M3.2.0,M11.1.0\n"


@lru_cache(maxsize=1)
def toronto_zone() -> ZoneInfo:
    try:
        return ZoneInfo("America/Toronto")
    except ZoneInfoNotFoundError:
        return ZoneInfo.from_file(io.BytesIO(_portable_tzif()), key="America/Toronto")
