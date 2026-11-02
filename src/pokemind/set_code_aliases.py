"""Optional, versioned set-code bridge derived only from verified PUBLIC payloads.

This is an in-memory view. It never changes native identifiers or catalog_sets.
Abbreviations identify a set, not a legal printing or an equivalent card name.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from urllib.parse import urlsplit

from pokemind.catalog_batch_store import verified_payload


VERSION = "public-set-code-bridge-v1"


def payload_source(connection, kind, entity_id, language) -> dict | None:
    """Recover the importer provenance, including the original set object URL.

    The historical catalog set URL can point to a member card. Do not present
    that member's page as the source of the set abbreviation.
    """
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog_batch_queries'").fetchone():
        return None
    row = connection.execute(
        "SELECT q.evidence_json FROM catalog_detail_payloads p JOIN catalog_batch_queries q USING(query_sha256) "
        "WHERE p.kind=? AND p.entity_id=? AND p.language=?", (kind, entity_id, language)).fetchone()
    if row is None:
        return None
    proof = json.loads(row[0])
    if proof.get("language", language) != language:
        return None
    if proof.get("operation") == "literal_snapshot":
        commit = proof.get("source_commit", "")
        obj = proof.get("source_objects", {}).get(entity_id, {})
        url = obj.get("source_url", "")
        prefix = f"https://github.com/tcgdex/cards-database/blob/{commit}/data/"
        if (not re.fullmatch(r"[0-9a-f]{40}", commit)
                or proof.get("source_url") != f"https://github.com/tcgdex/cards-database/tree/{commit}/data"
                or not re.fullmatch(r"[0-9a-f]{40}", obj.get("git_blob", ""))
                or not url.startswith(prefix) or not url.endswith(".ts")
                or any(part in url[len(prefix):] for part in ("..", "?", "#", "\\"))):
            return None
        return {"source_url": url, "source_commit": commit, "git_blob": obj["git_blob"],
                "transport": "pinned_git_literal_snapshot"}
    if (proof.get("operation") == "query" and proof.get("source_url") == "https://api.tcgdex.net/v2/graphql"
            and re.fullmatch(r"[0-9a-f]{64}", proof.get("query_sha256", ""))
            and not proof.get("rest_repairs")):
        return {"source_url": proof["source_url"], "transport": "graphql_fixed_query",
                "query_sha256": proof["query_sha256"]}
    return None


def collector_key(value: str) -> str:
    """Only decimal padding is insignificant; subset/promo suffixes stay exact."""
    return str(int(value)) if re.fullmatch(r"[0-9]+", value or "") else value


def build_aliases(connection, *, as_of: str) -> dict:
    if date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("SET_ALIAS_DATE_REQUIRED")
    required = {"abbreviation_official", "content_sha256_en", "content_sha256_fr",
                "retrieved_at_en", "retrieved_at_fr", "source_url_en", "source_url_fr"}
    columns = {r[1] for r in connection.execute("PRAGMA table_info(catalog_sets)")}
    aliases = {}
    if required.issubset(columns):
        for row in connection.execute("SELECT * FROM catalog_sets ORDER BY tcgdex_id"):
            for language in ("en", "fr"):
                digest = row["content_sha256_" + language]
                payload = verified_payload(connection, "sets", row["tcgdex_id"], language, digest)
                provenance = payload_source(connection, "sets", row["tcgdex_id"], language) if payload else None
                stamp = row["retrieved_at_" + language]
                url = row["source_url_" + language] or ""
                if not payload or not provenance or payload.get("id") != row["tcgdex_id"] or not stamp or stamp[:10] > as_of:
                    continue
                release = payload.get("releaseDate")
                try:
                    if not release or date.fromisoformat(release).isoformat() != release or release > as_of:
                        continue
                except (ValueError, TypeError):
                    continue
                if (row["detail_stale_" + language] or urlsplit(url).scheme != "https"
                        or urlsplit(url).hostname not in {"github.com", "api.tcgdex.net"}):
                    continue
                code = (payload.get("abbreviation") or {}).get("official")
                if (not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,20}", code)
                        or code != row["abbreviation_official"]):
                    continue
                # Keep source card membership, language and date as corroboration.
                members = payload.get("cards")
                if not isinstance(members, list) or not members:
                    continue
                evidence = {"set_id": row["tcgdex_id"], "code": code.upper(), "language": language,
                            "release_date": release, "retrieved_at": stamp, **provenance,
                            "catalog_row_source_url": url,
                            "payload_sha256": digest, "basis": "verified_payload.abbreviation.official",
                            "members": [{"id": x.get("id"), "number": x.get("localId"), "name": x.get("name")}
                                        for x in members if isinstance(x, dict)]}
                aliases.setdefault(code.upper(), []).append(evidence)
    payload = {"version": VERSION, "as_of": as_of, "aliases": aliases}
    return {**payload, "sha256": hashlib.sha256(json.dumps(payload, sort_keys=True,
            ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
            "database_mutated": False, "legality_inferred": False}


def alias_sets(bridge: dict, code: str) -> tuple[list[str], list[dict]]:
    evidence = bridge["aliases"].get(code.upper(), [])
    return sorted({item["set_id"] for item in evidence}), evidence
