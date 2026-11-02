from __future__ import annotations

import json
from pathlib import Path

import pytest

from pokemind.cli import main
from pokemind.database import database_status
from pokemind.security import neutral_exception_code, public_error


@pytest.mark.parametrize(
    "exc",
    [
        ValueError("C:\\Users\\Personne-Secrète\\deck.txt token=abc123"),
        OSError("Bearer super-secret à /private/user.sqlite3"),
        FileNotFoundError("C:\\Synthetic Name\\missing.json"),
    ],
)
def test_public_errors_never_echo_path_token_or_name(exc: BaseException) -> None:
    payload = public_error(exc)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["details_redacted"] is True
    for secret in ("Personne-Secrète", "abc123", "super-secret", "private", "Synthetic Name"):
        assert secret not in serialized


def test_controlled_error_code_is_preserved_without_suffix_detail() -> None:
    error = ValueError("WINDOWS_TIMEZONE_NOT_TORONTO: C:\\Private Name token=hidden")
    assert neutral_exception_code(error) == "WINDOWS_TIMEZONE_NOT_TORONTO"
    assert "Private Name" not in json.dumps(public_error(error))


def test_cli_json_and_human_errors_redact_missing_private_path(local_tmp: Path, capsys) -> None:
    missing = local_tmp / "Personne-Secrète token=abc123.sqlite3"
    assert main(["backup", "verify", "--backup", str(missing), "--json"]) == 2
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["error_code"] == "LOCAL_RESOURCE_NOT_FOUND"
    assert "Personne-Secrète" not in output and "abc123" not in output

    assert main(["backup", "verify", "--backup", str(missing)]) == 2
    error_output = capsys.readouterr().err
    assert "LOCAL_RESOURCE_NOT_FOUND" in error_output
    assert "Personne-Secrète" not in error_output and "abc123" not in error_output


def test_database_status_redacts_sqlite_exception_text(local_tmp: Path) -> None:
    corrupt = local_tmp / "Personne-Secrète.sqlite3"
    corrupt.write_bytes(b"not sqlite token=abc123")
    result = database_status(corrupt)
    assert result["integrity"] == "erreur_caviardee"
    assert result["integrity_error_code"] == "LOCAL_DATABASE_ERROR"
    assert "abc123" not in result["integrity"]
