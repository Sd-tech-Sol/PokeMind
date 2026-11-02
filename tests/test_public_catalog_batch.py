"""Full synthetic PUBLIC catalog: no owner DB, replay, network or hidden writes."""
import json

import pytest

from pokemind.cards import CatalogError, NetworkFailure
from pokemind.public_catalog_batch import collect
from test_catalog_batch_store import card, extension, evidence


class FakeClient:
    def __init__(self, *, fail=False):
        self.requests_made = self.body_bytes_read = 0
        self.last_http_status, self.blocked_reason = 200, None
        self.last_evidence, self.last_raw = None, None
        self.checkpoint = None
        self.fail = fail

    def _receipt(self, key, value):
        self.requests_made += 1
        self.body_bytes_read += len(json.dumps(value))
        self.last_evidence = evidence(key)
        if self.checkpoint:
            self.checkpoint(self)

    def page(self, kind, language, page):
        if self.fail and page == 2:
            self._receipt("failure", None)
            self.last_http_status = 503
            raise NetworkFailure("TCGDEX_BATCH_HTTP_503")
        rows = []
        if page == 1:
            rows = ([extension(language)] if kind == "sets" else
                    [card(value, language) for value in (["syn-1", "syn-2"] if language == "en" else ["syn-1"])])
        self._receipt(kind + language + str(page), rows)
        return rows

    def missing(self, kind, language, ids):
        result = {entity_id: None for entity_id in ids}
        self._receipt(kind + language + "absence", result)
        return result


def test_preview_has_no_database_file_or_http(local_tmp):
    client = FakeClient()
    assert collect(local_tmp, "synthetic", client=client)["status"] == "DRY_RUN"
    assert not list(local_tmp.iterdir()) and client.requests_made == 0


def test_full_cache_is_queryable_complete_and_second_pass_is_zero_write_zero_http(local_tmp):
    client = FakeClient()
    result = collect(local_tmp, "synthetic", execute=True, create=True, client=client)
    assert result["status"] == "OBSERVED_CATALOG_COMPLETE"
    assert result["head_probes_passed"] and result["coverage"]["complete"]
    assert result["coverage"]["unique_printings"] == 2
    assert result["coverage"]["languages"]["fr"]["statuses"]["absent"] == 1
    assert not result["owner_database_opened"] and not result["old_campaign_reused"]
    db = local_tmp / "data/local/public-campaigns/lot-i-synthetic/public.sqlite3"
    before = (db.read_bytes(), db.stat().st_mtime_ns)
    unused = FakeClient()
    second = collect(local_tmp, "synthetic", execute=True, client=unused)
    assert second["status"] == "CACHE_HIT_COMPLETE" and second["new_http_requests"] == 0
    assert not second["database_modified"] and unused.requests_made == 0
    assert before == (db.read_bytes(), db.stat().st_mtime_ns)


def test_source_stop_is_persistent_and_not_a_resume_permission(local_tmp):
    first = collect(local_tmp, "synthetic", execute=True, create=True, client=FakeClient(fail=True))
    assert first["status"] == "SOURCE_STOP" and first["last_http_status"] == 503
    assert not first["coverage"]["complete"]
    second = FakeClient()
    with pytest.raises(CatalogError, match="EXISTING_RUN_CLOSED"):
        collect(local_tmp, "synthetic", execute=True, client=second)
    assert second.requests_made == 0


def test_non_public_database_is_rejected_before_http(local_tmp):
    from pokemind.database import connect_writable, initialize_schema
    from contextlib import closing
    target = local_tmp / "data/local/public-campaigns/lot-i-synthetic"
    target.mkdir(parents=True)
    (target / "PUBLIC_ONLY.json").write_text(json.dumps({
        "kind": "pokemind_public_only_lot_i", "campaign": "synthetic", "schema_version": 1}))
    db = target / "public.sqlite3"
    with closing(connect_writable(db)) as connection:
        initialize_schema(connection)
        with connection:
            connection.execute("INSERT INTO observed_decks VALUES('synthetic','observé partiellement','fixture','fixture')")
    before = db.read_bytes()
    client = FakeClient()
    with pytest.raises(ValueError, match="OWNER_OR_UNKNOWN_DATA_BLOCKED"):
        collect(local_tmp, "synthetic", execute=True, client=client)
    assert not client.requests_made and db.read_bytes() == before
