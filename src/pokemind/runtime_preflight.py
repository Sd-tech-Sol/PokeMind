"""First-use diagnostics using only Python and an in-memory SQLite database."""
import platform
import sqlite3
import sys


def runtime_preflight():
    fts = False
    connection = None
    try:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(body)")
            connection.execute("INSERT INTO probe VALUES ('mémoire synthétique')")
            fts = connection.execute("SELECT count(*) FROM probe WHERE probe MATCH 'mémoire'").fetchone()[0] == 1
    except sqlite3.Error:
        pass
    finally:
        if connection is not None:
            connection.close()
    ready = sys.version_info >= (3, 11) and fts
    return {"status": "RUNTIME_READY" if ready else "RUNTIME_COMPONENT_MISSING",
            "python_version": platform.python_version(), "sqlite_version": sqlite3.sqlite_version,
            "windows": sys.platform == "win32", "fts5": fts,
            "owner_database_opened": False, "network_used": False, "writes_to_disk": 0,
            "installed_by_command": False, "scheduler_contacted": False,
            "default_database_warning": "Les commandes de données sans --db visent la base personnelle; choisir la base et autoriser l'acte.",
            "safe_next_command": "python -m pokemind demo --json",
            "release_status": "NOT_RELEASE_READY"}
