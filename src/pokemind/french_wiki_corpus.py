"""Offline, integrity-checked plan from the explicitly reviewed French PUBLIC corpus."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from pokemind.cards import CatalogError, _canonical_sha256
from pokemind.database import connect_readonly
from pokemind.french_text import article_parameters, extract_fields, normalized_set, number, plain
from pokemind.french_text_store import parallel_description_key
from pokemind.public_campaign import require_public_database
from pokemind.recovery import _redirected


def _read(path, maximum):
    if (any(_redirected(p) for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_nlink != 1 or not 0 < path.stat().st_size <= maximum):
        raise CatalogError("FRENCH_CORPUS_FILE_REJECTED")
    return path.read_bytes()


def plan_fields(root, source, db):
    root, source = Path(root).absolute(), Path(source).absolute()
    if source.parent != root / "data/local" or not re.fullmatch(r"french-text-[a-z0-9-]{1,40}", source.name):
        raise CatalogError("FRENCH_CORPUS_PUBLIC_SOURCE_REQUIRED")
    marker = json.loads(_read(source / "PUBLIC_ONLY.json",4096))
    if marker != {"kind":"pokemind_public_french_text_review","schema_version":1,"personal_data":False,"japanese_cards":False}:
        raise CatalogError("FRENCH_CORPUS_MARKER_REJECTED")
    require_public_database(root, db)
    rights = json.loads(_read(source / "pokepedia-siteinfo.json", 16384))["query"]["rightsinfo"]
    if rights.get("url") != "https://www.pokepedia.fr/Pok%C3%A9p%C3%A9dia:Copyrights" or "3.0" not in rights.get("text", ""):
        raise CatalogError("FRENCH_CORPUS_LICENSE_REVIEW_REQUIRED")
    targets = json.loads(_read(source / "targets.json", 24 * 1024 * 1024))["targets"]
    if not isinstance(targets, list) or len(targets) > 30_000:
        raise CatalogError("FRENCH_CORPUS_TARGET_VOLUME_REJECTED")
    ledger = json.loads(_read(source / "ledger.json", 8 * 1024 * 1024))
    if ledger["data_gets"] > 4000 or ledger["discovery_gets"] > 40 or ledger["body_bytes_read"] > 134217728:
        raise CatalogError("FRENCH_CORPUS_ENVELOPE_EXCEEDED")
    mapping = json.loads(_read(source / "set-mapping.json", 262144))
    connection = connect_readonly(db)
    try:
        payloads = {(r["entity_id"],r["language"]): json.loads(r["payload_json"]) or {} for r in connection.execute(
            "SELECT entity_id,language,payload_json FROM catalog_detail_payloads WHERE kind='cards'")}
        identities = {r["tcgdex_id"]:dict(r) for r in connection.execute("SELECT p.tcgdex_id,p.set_id,p.local_id,s.name_en,s.name_fr FROM catalog_printings p JOIN catalog_sets s ON s.tcgdex_id=p.set_id")}
    finally:
        connection.close()
    aliases = defaultdict(set)
    for (entity, lang), en in payloads.items():
        fr = payloads.get((entity,"fr"),{})
        if lang == "en" and en.get("name") and fr.get("name"):
            aliases[en["name"]].add(fr["name"])
    index, scopes = defaultdict(list), defaultdict(set)
    seen = set()
    for target in targets:
        entity = target.get("tcgdex_id")
        actual = identities.get(entity)
        if (not actual or entity in seen or any(target.get(k) != actual[k] for k in ("set_id","local_id"))
                or target.get("set_en") != actual["name_en"] or target.get("set_fr") != actual["name_fr"]):
            raise CatalogError("FRENCH_CORPUS_TARGET_IDENTITY_MISMATCH")
        seen.add(entity)
        en, fr = payloads[entity,"en"], payloads[entity,"fr"]
        if any(target.get(lang + "_payload_sha256") != _canonical_sha256(payloads[entity,lang]) for lang in ("en","fr")):
            raise CatalogError("FRENCH_CORPUS_TARGET_SOURCE_CHANGED")
        target["known_french_names"] = sorted(aliases[en.get("name")])
        target["en_name"],target["fr_name"] = en.get("name"),fr.get("name")
        target["wiki_set_aliases"] = [mapping[target["set_id"]]["wiki_set"]] if target["set_id"] in mapping else []
        # Explicit reviewed regional spelling for the international McDonald's set.
        if target["set_id"] in {"2018sm","2019sm"}:
            target["wiki_set_aliases"] += [v.removesuffix(" (International)") for v in target["wiki_set_aliases"]]
        for name in {target["set_en"],target["set_fr"],*target["wiki_set_aliases"]} - {None}:
            key = normalized_set(name)
            index[key,number(target["local_id"],target["set_id"])].append(target)
            scopes[key].add(target["set_id"])
    pages = {}
    files = set()
    total = 0
    for entry in ledger["entries"]:
        name = entry.get("file", "")
        if not re.fullmatch(r"phase[1-9][0-9]?-\d{4}\.json",name) or entry.get("status") != 200 or entry.get("error"):
            continue
        if name in files:
            raise CatalogError("FRENCH_CORPUS_DUPLICATE_RESPONSE")
        files.add(name)
        parsed = urlsplit(entry.get("url", ""))
        if parsed.scheme != "https" or parsed.netloc != "www.pokepedia.fr" or parsed.path != "/api.php":
            raise CatalogError("FRENCH_CORPUS_RESPONSE_ORIGIN_REJECTED")
        path = source / name
        body = _read(path,4194304)
        total += len(body)
        if total > 134217728 or hashlib.sha256(body).hexdigest() != entry.get("sha256"):
            raise CatalogError("FRENCH_CORPUS_RESPONSE_HASH_MISMATCH")
        data = json.loads(body)
        if data.get("error") or not isinstance(data.get("query",{}).get("pages"),list):
            raise CatalogError("FRENCH_CORPUS_SOURCE_ERROR")
        captured = datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat().replace("+00:00","Z")
        for page in data["query"]["pages"]:
            if page.get("missing"):
                continue
            revisions = page.get("revisions",[])
            if not revisions:
                continue
            revision = revisions[0]
            text = revision.get("slots",{}).get("main",{}).get("content")
            if not isinstance(text,str):
                continue
            old = pages.get(page["title"])
            if old and old["revid"] != revision["revid"]:
                raise CatalogError("FRENCH_CORPUS_CONCURRENT_REVISION_CHANGE")
            pages[page["title"]] = {"text":text,"source_title":page["title"],"revid":revision["revid"],
                "timestamp":revision["timestamp"],"response_sha256":entry["sha256"],"retrieved_at":captured}
    records, conflicts, errors = {},set(),Counter()
    description_sources = defaultdict(dict)
    rejected = defaultdict(list)
    for page in pages.values():
        try:
            parameters = article_parameters(page["text"])
            setname = plain(parameters.get("extension"))
        except CatalogError as exc:
            errors[str(exc)] += 1;continue
        key = normalized_set(setname)
        candidates = {t["tcgdex_id"]:t for sid in scopes.get(key,[]) for t in
                      index.get((key,number(parameters.get("numerocarte",""),sid)),[]) if t["set_id"] == sid}
        if not candidates:
            errors["NO_EXACT_SET_NUMBER_TARGET"] += 1
        for entity,target in candidates.items():
            try:
                fields = extract_fields(page["text"],target,payloads[entity,"en"],payloads[entity,"fr"])
            except CatalogError as exc:
                code = str(exc)
                errors[code] += 1
                if len(rejected[code]) < 20:
                    rejected[code].append({"printing_id":entity,"title":page["source_title"],
                        "wiki_name":parameters.get("nom"),"wiki_en_name":parameters.get("nomen"),
                        "expected_en":target.get("en_name"),"expected_fr":target.get("fr_name"),
                        "wiki_hp":parameters.get("pv"),"expected_hp":payloads[entity,"en"].get("hp")})
                continue
            # A page already checked for exact identity may also publish a
            # description present natively on this donor printing. Read it as
            # an attributed parallel reference; never overwrite its native FR.
            donor = fields.get("description")
            if not donor and payloads[entity,"en"].get("description"):
                donor = extract_fields(page["text"],{**target,"missing":["description"]},
                    payloads[entity,"en"],payloads[entity,"fr"]).get("description")
            description_key = parallel_description_key(payloads[entity,"en"])
            if donor and description_key:
                description_sources[description_key][donor["value"]] = {
                    "printing_id":entity,"field":"description",**donor,
                    **{k:v for k,v in page.items() if k != "text"},
                    "en_payload_sha256":target["en_payload_sha256"],"fr_payload_sha256":target["fr_payload_sha256"]}
            for field,value in fields.items():
                identity = entity,field
                row = {"printing_id":entity,"field":field,**value,
                    **{k:v for k,v in page.items() if k != "text"},
                    "en_payload_sha256":target["en_payload_sha256"],"fr_payload_sha256":target["fr_payload_sha256"]}
                if identity in records and records[identity]["value"] != row["value"]:
                    conflicts.add(identity)
                else:
                    records[identity] = row
    for identity in conflicts:
        records.pop(identity,None)
    # Flavor description only: a published French wording corresponding to the
    # identical English paragraph and identical national species IDs. It is a
    # related text reference, never an official reprint/printing equivalence.
    parallels = description_sources
    parallel_count = 0
    for target in targets:
        entity = target["tcgdex_id"]
        if "description" not in target["missing"] or (entity,"description") in records:
            continue
        values = parallels.get(parallel_description_key(payloads[entity,"en"]),{})
        if len(values) != 1:
            continue
        origin = next(iter(values.values()))
        related = origin["printing_id"]
        records[entity,"description"] = {**origin,"printing_id":entity,"text_kind":"published_parallel_description",
            "related_printing_id":related,"related_en_payload_sha256":_canonical_sha256(payloads[related,"en"]),
            "related_fr_payload_sha256":_canonical_sha256(payloads[related,"fr"]),
            "match_basis":"identical_English_description_and_dexId",
            "en_payload_sha256":target["en_payload_sha256"],"fr_payload_sha256":target["fr_payload_sha256"]}
        parallel_count += 1
    rows = list(records.values())
    report = {"source_response_files":len(files),"source_pages":len(pages),"matched_cards":len({r["printing_id"] for r in rows}),
        "published_fields":len(rows),"conflicting_fields_excluded":len(conflicts),"errors":dict(errors),
        "parallel_descriptions":parallel_count,
        "rejected_examples":dict(rejected),
        "field_counts":dict(Counter(r["field"].split(".")[0] for r in rows)),
        "japanese_cards_imported":0,"network_used":False,"native_data_modified":False}
    return rows,report
