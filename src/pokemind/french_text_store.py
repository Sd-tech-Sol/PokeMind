"""Additive, attributed French supplements in an explicitly marked PUBLIC cache."""
from __future__ import annotations

from copy import deepcopy
import json
import re
import unicodedata
from urllib.parse import quote

from pokemind.cards import CatalogError, _canonical_sha256
from pokemind.database import connect_readonly, connect_writable, utc_now
from pokemind.french_text import LICENSE, LICENSE_URL
from pokemind.public_campaign import require_public_database

TABLE = "catalog_french_text_fields"


def _exists(connection):
    return bool(connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone())


def coverage_fields(connection):
    if not _exists(connection):
        return {"stored_cards":0,"stored_fields":0,"fields_by_kind":{}}
    counts = {row[0]:row[1] for row in connection.execute(f"""SELECT
        CASE WHEN instr(field,'.')>0 THEN substr(field,1,instr(field,'.')-1) ELSE field END kind,
        count(*) FROM {TABLE} GROUP BY kind""")}
    return {"stored_cards":connection.execute(f"SELECT count(DISTINCT printing_id) FROM {TABLE}").fetchone()[0],
        "stored_fields":sum(counts.values()),"fields_by_kind":counts,
        "native_tcgdex_counts_unchanged":True,"official_printing_or_legality_proven":False,
        "freshness_checked_on_each_show_and_search":True}


def _originals(connection, printing_id):
    rows = connection.execute("""SELECT t.language,t.status,t.payload_sha256,
        p.payload_json,p.payload_sha256 auxiliary_hash FROM catalog_translations t
        LEFT JOIN catalog_detail_payloads p ON p.entity_id=t.printing_id AND p.language=t.language AND p.kind='cards'
        WHERE t.printing_id=?""", (printing_id,)).fetchall()
    result = {}
    for row in rows:
        if row["status"] not in {"present", "absent"} or row["payload_json"] is None:
            return None
        payload = json.loads(row["payload_json"])
        if row["payload_sha256"] != row["auxiliary_hash"] or row["payload_sha256"] != _canonical_sha256(payload):
            return None
        result[row["language"]] = payload or {}
    return result if set(result) == {"en", "fr"} else None


def _value(payload, field):
    value = payload
    for part in field.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def parallel_description_key(payload):
    ids = payload.get("dexId")
    value = payload.get("description")
    if not isinstance(value,str) or not isinstance(ids,list) or not ids or any(type(i) is not int for i in ids):
        return None
    paragraph = re.sub(r"\s+"," ",unicodedata.normalize("NFC",value)).strip()
    return (tuple(sorted(ids)), paragraph) if paragraph else None


def _parallel_valid(record, originals, related):
    return bool(related and record.get("field") == "description" and
        record.get("match_basis") == "identical_English_description_and_dexId" and
        all(record.get("related_" + lang + "_payload_sha256") == _canonical_sha256(related[lang]) for lang in ("en","fr")) and
        parallel_description_key(originals["en"]) is not None and
        parallel_description_key(originals["en"]) == parallel_description_key(related["en"]))


def _validated(record, originals, related=None):
    if (not isinstance(record, dict) or not re.fullmatch(r"(?:name|description|effect|(?:attacks|abilities)\.[0-9]{1,2}\.(?:name|effect))", record.get("field", ""))
            or record.get("text_kind") not in {"published_community_translation", "published_french_transcription", "published_parallel_description"}
            or not isinstance(record.get("value"), str) or not 0 < len(record["value"].strip()) <= 20_000
            or record.get("official_text_verified") is not False
            or not isinstance(record.get("source_title"), str) or not 0 < len(record["source_title"]) <= 300
            or type(record.get("revid")) is not int or not 0 < record["revid"] < 10**12
            or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", record.get("timestamp", ""))
            or not re.fullmatch(r"[0-9a-f]{64}", record.get("response_sha256", ""))):
        raise CatalogError("FRENCH_SUPPLEMENT_RECORD_REJECTED")
    if originals is None or any(record.get(lang + "_payload_sha256") != _canonical_sha256(originals[lang]) for lang in ("en", "fr")):
        raise CatalogError("FRENCH_SUPPLEMENT_SOURCE_CHANGED")
    if _value(originals["fr"], record["field"]):
        raise CatalogError("FRENCH_SUPPLEMENT_NATIVE_OVERWRITE_BLOCKED")
    if _value(originals["en"], record["field"]) is None:
        raise CatalogError("FRENCH_SUPPLEMENT_UNKNOWN_FIELD_BLOCKED")
    if record["text_kind"] == "published_parallel_description" and not _parallel_valid(record,originals,related):
        raise CatalogError("FRENCH_SUPPLEMENT_PARALLEL_MATCH_REJECTED")
    return record


def import_fields(root, db, records, *, execute=False):
    require_public_database(root, db)
    records = list(records)
    if len(records) > 100_000:
        raise CatalogError("FRENCH_SUPPLEMENT_VOLUME_REJECTED")
    read = connect_readonly(db)
    try:
        originals = {}
        keys = set()
        for record in records:
            if not isinstance(record, dict):
                raise CatalogError("FRENCH_SUPPLEMENT_RECORD_REJECTED")
            entity = record.get("printing_id")
            if entity not in originals:
                originals[entity] = _originals(read, entity)
            related = _originals(read,record["related_printing_id"]) if record.get("related_printing_id") else None
            _validated(record, originals[entity],related)
            key = entity, record["field"]
            if key in keys:
                raise CatalogError("FRENCH_SUPPLEMENT_DUPLICATE_FIELD")
            keys.add(key)
    finally:
        read.close()
    report = {"status": "DRY_RUN", "fields": len(records), "cards": len(originals),
              "native_data_modified": False, "network_used": False, "license": LICENSE}
    if not execute:
        return report
    connection = connect_writable(db)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
                printing_id TEXT NOT NULL REFERENCES catalog_printings(tcgdex_id), field TEXT NOT NULL,
                value TEXT NOT NULL, value_sha256 TEXT NOT NULL, provenance_json TEXT NOT NULL,
                en_payload_sha256 TEXT NOT NULL, fr_payload_sha256 TEXT NOT NULL,
                PRIMARY KEY(printing_id,field))""")
            connection.execute("""CREATE TABLE IF NOT EXISTS catalog_french_text_documents (
                id INTEGER PRIMARY KEY,printing_id TEXT UNIQUE NOT NULL REFERENCES catalog_printings(tcgdex_id),
                name TEXT NOT NULL,body TEXT NOT NULL)""")
            connection.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS catalog_french_text_fts
                USING fts5(printing_id UNINDEXED,name,body,tokenize='unicode61 remove_diacritics 2')""")
            # Re-check under the writer transaction; no stale source can be applied.
            for record in records:
                related = _originals(connection,record["related_printing_id"]) if record.get("related_printing_id") else None
                _validated(record, _originals(connection, record["printing_id"]),related)
                provenance = {"provider": "Poképédia", "title": record["source_title"],
                    "url": "https://www.pokepedia.fr/index.php?title=" + quote(record["source_title"], safe="") + "&oldid=" + str(record["revid"]),
                    "history_url": "https://www.pokepedia.fr/index.php?title=" + quote(record["source_title"], safe="") + "&action=history",
                    "revision": record["revid"], "revision_timestamp": record["timestamp"], "retrieved_at": record.get("retrieved_at") or utc_now(),
                    "response_sha256": record["response_sha256"], "license": LICENSE, "license_url": LICENSE_URL,
                    "wiki_parameter": record["wiki_parameter"], "text_kind": record["text_kind"],
                    "official_text_verified": False, "french_printing_proven": False}
                if record["text_kind"] == "published_parallel_description":
                    provenance.update({k:record[k] for k in ("related_printing_id","related_en_payload_sha256",
                        "related_fr_payload_sha256","match_basis")})
                old = connection.execute(f"SELECT value_sha256,en_payload_sha256,fr_payload_sha256 FROM {TABLE} WHERE printing_id=? AND field=?",
                                         (record["printing_id"], record["field"])).fetchone()
                digest = _canonical_sha256(record["value"])
                if old and tuple(old) == (digest, record["en_payload_sha256"], record["fr_payload_sha256"]):
                    continue
                if old:
                    raise CatalogError("FRENCH_SUPPLEMENT_EXISTING_CONFLICT")
                connection.execute(f"INSERT INTO {TABLE} VALUES (?,?,?,?,?,?,?)", (record["printing_id"],record["field"],record["value"],digest,
                    json.dumps(provenance, ensure_ascii=False),record["en_payload_sha256"],record["fr_payload_sha256"]))
            for entity in originals:
                rows = connection.execute(f"SELECT field,value FROM {TABLE} WHERE printing_id=? ORDER BY field", (entity,)).fetchall()
                name = next((r["value"] for r in rows if r["field"] == "name"), originals[entity]["fr"].get("name") or "")
                body = "\n".join(r["value"] for r in rows if r["field"] != "name")
                old = connection.execute("SELECT id,name,body FROM catalog_french_text_documents WHERE printing_id=?", (entity,)).fetchone()
                if old and old["name"] == name and old["body"] == body:
                    continue
                connection.execute("""INSERT INTO catalog_french_text_documents(printing_id,name,body) VALUES (?,?,?)
                    ON CONFLICT(printing_id) DO UPDATE SET name=excluded.name,body=excluded.body""", (entity,name,body))
                doc = connection.execute("SELECT id FROM catalog_french_text_documents WHERE printing_id=?", (entity,)).fetchone()[0]
                connection.execute("DELETE FROM catalog_french_text_fts WHERE rowid=?", (doc,))
                connection.execute("INSERT INTO catalog_french_text_fts(rowid,printing_id,name,body) VALUES (?,?,?,?)", (doc,entity,name,body))
        report["status"] = "PUBLISHED_FRENCH_FIELDS_IMPORTED"
        return report
    finally:
        connection.close()


def fresh_fields(connection, entity):
    if not _exists(connection):
        return []
    originals = _originals(connection, entity)
    if originals is None:
        return []
    rows = connection.execute(f"SELECT * FROM {TABLE} WHERE printing_id=? ORDER BY field", (entity,)).fetchall()
    result = []
    for row in rows:
        if not (row["en_payload_sha256"] == _canonical_sha256(originals["en"])
                and row["fr_payload_sha256"] == _canonical_sha256(originals["fr"])
                and row["value_sha256"] == _canonical_sha256(row["value"]) and not _value(originals["fr"],row["field"])):
            continue
        proof = json.loads(row["provenance_json"])
        if proof.get("text_kind") == "published_parallel_description":
            related = _originals(connection,proof.get("related_printing_id"))
            if not _parallel_valid({"field":row["field"],**proof},originals,related):
                continue
        result.append(dict(row))
    return result


def apply_to_card(connection, result):
    if result["language"] != "fr":
        return result
    rows = fresh_fields(connection, result["tcgdex_id"])
    if not rows:
        return result
    originals = _originals(connection, result["tcgdex_id"])
    source_fields = []
    for row in rows:
        parts = row["field"].split(".")
        if len(parts) == 1:
            if not result.get(parts[0]):
                result[parts[0]] = row["value"]
        else:
            kind, index, key = parts[0], int(parts[1]), parts[2]
            if result.get(kind) is None:
                result[kind] = []
            while len(result[kind]) <= index:
                skeleton = originals["en"].get(kind, [])[len(result[kind])]
                # Numeric/cost structure only; no English name/effect fallback.
                result[kind].append({k: deepcopy(v) for k,v in skeleton.items() if k not in {"name", "effect"}})
            if not result[kind][index].get(key):
                result[kind][index][key] = row["value"]
        source_fields.append({"field": row["field"], **json.loads(row["provenance_json"])})
    result["french_text_supplements"] = {"status": "published_french_supplements", "native_tcgdex_status": result["status"],
        "native_data_modified": False, "official_french_printing_proven": False, "fields": source_fields}
    if result.get("name") and "localized_name" in result.get("missing_fields", []):
        result["missing_fields"].remove("localized_name")
    if any(r["field"] != "name" for r in rows) and "localized_text" in result.get("missing_fields", []):
        result["missing_fields"].remove("localized_text")
    return result


def search_fields(connection, expression, limit):
    if not _exists(connection):
        return []
    rows = connection.execute("""SELECT d.printing_id,d.name,d.body,p.set_id,p.local_id,p.category,t.status,
        catalog_french_text_fts.name indexed_name,catalog_french_text_fts.body indexed_body,
        snippet(catalog_french_text_fts,2,'[',']',' … ',20) excerpt,
        bm25(catalog_french_text_fts) score FROM catalog_french_text_fts
        JOIN catalog_french_text_documents d ON d.id=catalog_french_text_fts.rowid
        JOIN catalog_printings p ON p.tcgdex_id=d.printing_id
        JOIN catalog_translations t ON t.printing_id=p.tcgdex_id AND t.language='fr'
        WHERE catalog_french_text_fts MATCH ? ORDER BY score,d.printing_id LIMIT ?""", (expression,limit)).fetchall()
    result = []
    for row in rows:
        fields = fresh_fields(connection, row["printing_id"])
        if not fields:
            continue
        originals = _originals(connection, row["printing_id"])
        name = next((f["value"] for f in fields if f["field"] == "name"), originals["fr"].get("name") or "")
        body = "\n".join(f["value"] for f in fields if f["field"] != "name")
        if row["name"] != name or row["body"] != body or row["indexed_name"] != name or row["indexed_body"] != body:
            continue
        result.append({"tcgdex_id": row["printing_id"], "language": "fr", "status": row["status"], "name": name,
            "set_id": row["set_id"], "local_id": row["local_id"], "category": row["category"], "snippet": row["excerpt"],
            "score": round(float(row["score"]),6), "text_source": "attributed_french_supplement"})
    return result
