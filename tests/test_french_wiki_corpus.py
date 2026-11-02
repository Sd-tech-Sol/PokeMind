"""Synthetic public API corpus: verified receipts precede all enrichment writes."""
import hashlib
import json
from contextlib import closing

import pytest

from pokemind.cards import CatalogError
from pokemind.database import connect_writable
from pokemind import catalog_batch_store as batch
from pokemind.french_wiki_corpus import plan_fields
from test_french_text_store import public_cache, record
from test_catalog_batch_store import card, evidence


def corpus(root, db):
    source = root / "data/local/french-text-synthetic"
    source.mkdir(parents=True)
    (source / "PUBLIC_ONLY.json").write_text(json.dumps({"kind":"pokemind_public_french_text_review",
        "schema_version":1,"personal_data":False,"japanese_cards":False}),encoding="utf-8")
    (source / "pokepedia-siteinfo.json").write_text(json.dumps({"query":{"rightsinfo":{
        "url":"https://www.pokepedia.fr/Pok%C3%A9p%C3%A9dia:Copyrights","text":"Synthetic CC 3.0 notice"}}}),encoding="utf-8")
    receipt = record(db)
    target = {"tcgdex_id":"syn-2","set_id":"syn","local_id":"2","set_en":"Synthetic Set","set_fr":"Synthetic Set",
        "missing":["name"],"en_payload_sha256":receipt["en_payload_sha256"],"fr_payload_sha256":receipt["fr_payload_sha256"]}
    (source / "targets.json").write_text(json.dumps({"targets":[target]}),encoding="utf-8")
    (source / "set-mapping.json").write_text("{}",encoding="utf-8")
    text="{{Article carte|nom=Synthetic Flame|nom-trad=Flamme fictive|extension=Synthetic Set|numerocarte=2|pv=100}}"
    page={"title":"Flamme fictive (Synthetic Set 2)","revisions":[{"revid":1234,"timestamp":"2026-01-01T00:00:00Z",
        "slots":{"main":{"content":text}}}]}
    body=json.dumps({"query":{"pages":[page]}}).encode()
    (source / "phase1-0000.json").write_bytes(body)
    (source / "ledger.json").write_text(json.dumps({"data_gets":1,"discovery_gets":1,"body_bytes_read":len(body),"entries":[{
        "file":"phase1-0000.json","status":200,"url":"https://www.pokepedia.fr/api.php?action=query",
        "sha256":hashlib.sha256(body).hexdigest()}]}),encoding="utf-8")
    return source


def test_valid_plan_is_attributed_and_read_only(local_tmp):
    db=public_cache(local_tmp); source=corpus(local_tmp,db); before=db.read_bytes()
    fields,report=plan_fields(local_tmp,source,db)
    assert report["published_fields"] == 1 and report["japanese_cards_imported"] == 0
    assert fields[0]["value"] == "Flamme fictive" and fields[0]["revid"] == 1234
    assert fields[0]["retrieved_at"].endswith("Z")
    assert db.read_bytes() == before


@pytest.mark.parametrize("fault",["hash","origin","budget","identity","duplicate","rights"])
def test_bad_receipt_target_or_envelope_rejected_without_database_changes(local_tmp,fault):
    db=public_cache(local_tmp);source=corpus(local_tmp,db)
    if fault in {"hash","origin","budget"}:
        p=source/"ledger.json";value=json.loads(p.read_text())
        if fault=="hash":value["entries"][0]["sha256"]="0"*64
        if fault=="origin":value["entries"][0]["url"]="https://untrusted.invalid/api.php"
        if fault=="budget":value["data_gets"]=4001
    elif fault in {"identity","duplicate"}:
        p=source/"targets.json";value=json.loads(p.read_text())
        if fault=="identity":value["targets"][0]["local_id"]="3"
        else:value["targets"].append(value["targets"][0])
    else:
        p=source/"pokepedia-siteinfo.json";value={"query":{"rightsinfo":{"url":"other","text":"3.0"}}}
    p.write_text(json.dumps(value),encoding="utf-8");before=db.read_bytes()
    with pytest.raises(CatalogError):plan_fields(local_tmp,source,db)
    assert db.read_bytes()==before


def test_published_description_on_native_complete_donor_only_supplies_related_reference(local_tmp):
    db=public_cache(local_tmp)
    with closing(connect_writable(db)) as connection:
        batch.store_selection(connection,"cards","en",{eid:{**card(eid),"description":"Synthetic paragraph.","dexId":[1]}
            for eid in ("syn-1","syn-2")},evidence("parallel-en"))
        batch.store_selection(connection,"cards","fr",{"syn-1":{**card("syn-1","fr"),
            "description":"Une phrase française fictive."}},evidence("parallel-fr"))
    source=corpus(local_tmp,db)
    targets=json.loads((source/"targets.json").read_text())["targets"]
    targets[0]["missing"]=["description"]
    donor={**targets[0],"tcgdex_id":"syn-1","local_id":"1","missing":[]}
    receipt=record(db,entity="syn-1")
    for lang in ("en","fr"):donor[lang+"_payload_sha256"]=receipt[lang+"_payload_sha256"]
    (source/"targets.json").write_text(json.dumps({"targets":[*targets,donor]}),encoding="utf-8")
    page=json.loads((source/"phase1-0000.json").read_bytes())
    page["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]=(
        "{{Article carte|nom=Flamme fictive|nomen=Synthetic Flame|extension=Synthetic Set|numerocarte=1|pv=100"
        "|description=Une phrase française fictive.}}")
    body=json.dumps(page).encode();(source/"phase1-0000.json").write_bytes(body)
    ledger=json.loads((source/"ledger.json").read_text());ledger["entries"][0]["sha256"]=hashlib.sha256(body).hexdigest()
    (source/"ledger.json").write_text(json.dumps(ledger),encoding="utf-8")
    before=db.read_bytes();fields,report=plan_fields(local_tmp,source,db)
    assert len(fields)==report["parallel_descriptions"]==1
    assert fields[0]["printing_id"]=="syn-2" and fields[0]["related_printing_id"]=="syn-1"
    assert fields[0]["value"]=="Une phrase française fictive."
    assert fields[0]["text_kind"]=="published_parallel_description"
    assert db.read_bytes()==before
