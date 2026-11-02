"""Recherche locale FTS5 avec repli déterministe."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from pokemind.database import connect_readonly


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
STOP_WORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du",
    "en", "et", "la", "le", "les", "ou", "par", "pour", "sur", "un", "une",
}


def query_tokens(query: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_RE.findall(query):
        normalized = token.casefold()
        if normalized not in STOP_WORDS and normalized not in tokens:
            tokens.append(normalized)
    return tokens


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _citation(row: Any) -> str:
    return (
        f"{row['title']} — {row['heading_path']} — "
        f"{row['path']}:L{row['start_line']}-L{row['end_line']} "
        f"(source {row['source_date'] or 'date inconnue'})"
    )


def _as_result(row: Any, snippet: str, score: float | int) -> dict[str, Any]:
    result = {
        "document": row["title"],
        "heading": row["heading_path"],
        "path": row["path"],
        "start_line": int(row["start_line"]),
        "end_line": int(row["end_line"]),
        "source_date": row["source_date"],
        "content_sha256": row["content_sha256"],
        "score": score,
        "snippet": snippet,
    }
    result["citation"] = _citation(row)
    return result


def search_database(db_path: Path, query: str, limit: int = 5) -> list[dict[str, Any]]:
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; exécuter d'abord 'import-seed'.")
    if not 1 <= limit <= 100:
        raise ValueError("La limite doit être comprise entre 1 et 100.")
    tokens = query_tokens(query)
    if not tokens:
        raise ValueError("La recherche doit contenir au moins un mot significatif.")

    connection = connect_readonly(db_path)
    try:
        backend_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'search_backend'"
        ).fetchone()
        backend = backend_row[0] if backend_row else "like"
        if backend == "fts5":
            expression = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
            rows = connection.execute(
                """SELECT d.title, d.path, d.source_date, s.heading_path,
                          s.start_line, s.end_line, s.content_sha256,
                          snippet(sections_fts, 1, '[', ']', ' … ', 24) AS excerpt,
                          bm25(sections_fts, 4.0, 1.0) AS score
                   FROM sections_fts
                   JOIN sections s ON s.id = sections_fts.rowid
                   JOIN documents d ON d.id = s.document_id
                   WHERE sections_fts MATCH ?
                   ORDER BY score, d.path, s.ordinal
                   LIMIT ?""",
                (expression, limit),
            ).fetchall()
            return [_as_result(row, row["excerpt"] or "", round(float(row["score"]), 6)) for row in rows]

        rows = connection.execute(
            """SELECT d.title, d.path, d.source_date, s.heading_path,
                      s.start_line, s.end_line, s.content_sha256, s.heading, s.content, s.ordinal
               FROM sections s JOIN documents d ON d.id = s.document_id"""
        ).fetchall()
        folded_tokens = [_fold(token) for token in tokens]
        matches: list[tuple[int, Any]] = []
        for row in rows:
            haystack = _fold(f"{row['heading']} {row['content']}")
            score = sum(haystack.count(token) for token in folded_tokens)
            if score:
                matches.append((score, row))
        matches.sort(key=lambda item: (-item[0], item[1]["path"], item[1]["ordinal"]))
        return [
            _as_result(row, row["content"][:280].replace("\n", " "), score)
            for score, row in matches[:limit]
        ]
    finally:
        connection.close()
