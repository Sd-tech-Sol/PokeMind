"""Résolution prudente des chemins locaux de PokeMind."""

from __future__ import annotations

import os
from pathlib import Path


SEED_FILES = (
    "01_fondations.md",
    "02_strategie.md",
    "03_decks_meta.md",
    "04_entrainement.md",
)


class PathSafetyError(ValueError):
    """Un chemin sort de la zone explicitement permise."""


def find_project_root(start: Path | None = None) -> Path:
    """Trouve la racine sans consulter un autre projet."""
    configured = os.environ.get("POKEMIND_ROOT")
    origin = Path(configured) if configured else (start or Path.cwd())
    origin = origin.resolve()
    candidates = (origin, *origin.parents)
    for candidate in candidates:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / ".orchestrator" / "PROJECT_SPEC.md").is_file()
            and (candidate / "source_material" / "markdown").is_dir()
        ):
            return candidate
    raise FileNotFoundError(
        "Racine PokeMind introuvable; lancer la commande depuis le dépôt "
        "ou définir POKEMIND_ROOT."
    )


def resolve_seed_file(markdown_dir: Path, filename: str) -> Path:
    """Résout un des quatre fichiers autorisés, sans traversée ni lien sortant."""
    if filename not in SEED_FILES or Path(filename).name != filename:
        raise PathSafetyError(f"Source d'amorçage non autorisée: {filename!r}")
    base = markdown_dir.resolve(strict=True)
    candidate = (base / filename).resolve(strict=True)
    if not candidate.is_relative_to(base) or not candidate.is_file():
        raise PathSafetyError(f"Source hors du répertoire autorisé: {filename!r}")
    return candidate


def seed_paths(root: Path) -> tuple[Path, ...]:
    markdown_dir = root / "source_material" / "markdown"
    return tuple(resolve_seed_file(markdown_dir, name) for name in SEED_FILES)


def default_db_path(root: Path) -> Path:
    return root / "data" / "local" / "pokemind.sqlite3"
