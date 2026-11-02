"""Backend PEP 517 minimal, auditable et sans téléchargement.

Il construit uniquement le paquet Python pur de PokeMind. Cela évite qu'une
installation locale exige un backend téléchargé pendant PM-0001.
"""

from __future__ import annotations

import base64
import hashlib
import os
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DIST = "pokemind_local"
PROJECT = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']
VERSION = PROJECT['version']
DIST_INFO = f"{DIST}-{VERSION}.dist-info"
WHEEL_NAME = f"{DIST}-{VERSION}-py3-none-any.whl"


def get_requires_for_build_wheel(config_settings=None):
    return []


def get_requires_for_build_editable(config_settings=None):
    return []


def _metadata() -> str:
    result = (
        "Metadata-Version: 2.3\n"
        "Name: pokemind-local\n"
        f"Version: {VERSION}\n"
        "Summary: Cerveau local source pour Pokemon TCG Live\n"
        "Requires-Python: >=3.11\n"
        "License: MIT\n"
    )
    for extra, dependencies in PROJECT.get('optional-dependencies', {}).items():
        result += f'Provides-Extra: {extra}\n'
        for dependency in dependencies:
            requirement, separator, marker = dependency.partition(';')
            condition = f'({marker.strip()}) and ' if separator else ''
            result += f'Requires-Dist: {requirement.strip()}; {condition}extra == "{extra}"\n'
    return result + '\n'


def _wheel() -> str:
    return "Wheel-Version: 1.0\nGenerator: pokemind-build-backend\nRoot-Is-Purelib: true\nTag: py3-none-any\n"


def _entry_points() -> str:
    return "[console_scripts]\npokemind = pokemind.cli:main\n\n[gui_scripts]\npokemind-desktop = pokemind.desktop.app:launch\n"


def _record_line(name: str, data: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
    return f"{name},sha256={digest},{len(data)}"


def _build(wheel_directory: str, editable: bool) -> str:
    destination = Path(wheel_directory)
    destination.mkdir(parents=True, exist_ok=True)
    wheel_path = destination / WHEEL_NAME
    files: dict[str, bytes] = {}
    if editable:
        files[f"{DIST}.pth"] = (str((ROOT / "src").resolve()) + os.linesep).encode("utf-8")
    else:
        for source in sorted((ROOT / "src" / "pokemind").rglob("*.py")):
            relative = source.relative_to(ROOT / 'src').as_posix()
            files[relative] = source.read_bytes()
    files[f"{DIST_INFO}/METADATA"] = _metadata().encode("utf-8")
    files[f"{DIST_INFO}/WHEEL"] = _wheel().encode("utf-8")
    files[f"{DIST_INFO}/entry_points.txt"] = _entry_points().encode("utf-8")
    record_name = f"{DIST_INFO}/RECORD"
    record = "\n".join(_record_line(name, data) for name, data in files.items())
    record += f"\n{record_name},,\n"
    files[record_name] = record.encode("utf-8")
    with ZipFile(wheel_path, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return wheel_path.name


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    return _build(wheel_directory, editable=False)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    return _build(wheel_directory, editable=True)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    target = Path(metadata_directory) / DIST_INFO
    target.mkdir(parents=True, exist_ok=True)
    (target / "METADATA").write_text(_metadata(), encoding="utf-8")
    (target / "WHEEL").write_text(_wheel(), encoding="utf-8")
    (target / "entry_points.txt").write_text(_entry_points(), encoding="utf-8")
    return DIST_INFO


prepare_metadata_for_build_editable = prepare_metadata_for_build_wheel
