"""Codes d'erreur publics neutres; aucun détail technique ou propriétaire."""

from __future__ import annotations

import re
import sqlite3
from typing import Any


_CONTROLLED_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,80}\Z")


def neutral_exception_code(exc: BaseException, namespace: str = "LOCAL") -> str:
    """Transforme une exception en code stable sans recopier ``str(exc)``."""
    raw = str(exc).strip()
    first = raw.split(":", 1)[0]
    if _CONTROLLED_CODE.fullmatch(first):
        return first
    if isinstance(exc, FileNotFoundError):
        return f"{namespace}_RESOURCE_NOT_FOUND"
    if isinstance(exc, sqlite3.DatabaseError):
        return f"{namespace}_DATABASE_ERROR"
    if isinstance(exc, OSError):
        return f"{namespace}_IO_ERROR"
    if isinstance(exc, ValueError):
        return f"{namespace}_INVALID_INPUT_OR_STATE"
    return f"{namespace}_OPERATION_FAILED"


def public_error(exc: BaseException) -> dict[str, Any]:
    code = neutral_exception_code(exc)
    messages = {
        "LOCAL_RESOURCE_NOT_FOUND": "Ressource locale introuvable; chemin et détail caviardés.",
        "LOCAL_DATABASE_ERROR": "Base locale illisible ou indisponible; détail technique caviardé.",
        "LOCAL_IO_ERROR": "Opération locale impossible; chemin et détail technique caviardés.",
        "LOCAL_INVALID_INPUT_OR_STATE": "Entrée ou état local invalide; le détail technique est caviardé.",
    }
    return {
        "error_code": code,
        "error": messages.get(code, "Opération refusée; détail technique caviardé."),
        "remediation": "Corriger l'entrée ou consulter le guide local correspondant, puis réessayer.",
        "details_redacted": True,
    }
