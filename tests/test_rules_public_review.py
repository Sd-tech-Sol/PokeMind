"""Synthetic release evidence and scoped reprints, without owner data or HTTP."""
import sqlite3
from contextlib import closing

import pytest

from pokemind.cards import card_reprints
from pokemind.rules import check_card
from test_rules import _ready_db, _assertion, _coverage


def release_policy(db,platform="live"):
    _assertion(db,"synthetic-release-policy","release_window",platform=platform,
               payload={"requires_printing_legal_from":True})


def date_proof(db,entity,value,identity="synthetic-date"):
    _assertion(db,identity,"release_window",subject=entity,payload={"legal_from":value})


def verdict(db,entity="synthetic-h"):
    return check_card(db,entity,format="standard",platform="live",as_of="2026-10-11")


def test_complete_bans_and_allowed_mark_cannot_substitute_for_release_proof(local_tmp):
    db=_ready_db(local_tmp/"rules.sqlite3");_coverage(db);release_policy(db)
    result=verdict(db)
    assert result["status"]=="unknown" and "OFFICIAL_RELEASE_DATE_NOT_VERIFIED" in result["reason_codes"]
    date_proof(db,"synthetic-h","2026-10-10")
    assert verdict(db)["status"]=="legal"


@pytest.mark.parametrize("value",["2026-00-01","not-a-date",False,42])
def test_malformed_release_evidence_cannot_make_a_card_legal(local_tmp,value):
    db=_ready_db(local_tmp/"rules.sqlite3");_coverage(db);release_policy(db)
    date_proof(db,"synthetic-h",value)
    assert verdict(db)["reason_codes"]==["OFFICIAL_RELEASE_DATE_INVALID"]


def test_future_tournament_date_blocks_a_new_printing(local_tmp):
    db=_ready_db(local_tmp/"rules.sqlite3");_coverage(db);release_policy(db)
    date_proof(db,"synthetic-h","2026-10-12")
    result=verdict(db)
    assert result["status"]=="not_legal" and "WAITING_PERIOD_ACTIVE" in result["reason_codes"]


def reprint(db):
    with closing(sqlite3.connect(db)) as c, c:
        c.execute("UPDATE catalog_printings SET regulation_mark=NULL WHERE tcgdex_id='synthetic-g'")
    _assertion(db,"synthetic-equivalence","reprint_equivalence",subject="synthetic-g",
               payload={"current_printing_id":"synthetic-h"})
    date_proof(db,"synthetic-g","2026-10-10","synthetic-old-date")


def test_explicit_reprint_can_support_an_old_printing_without_a_mark(local_tmp):
    db=_ready_db(local_tmp/"rules.sqlite3");_coverage(db);release_policy(db);reprint(db)
    assert verdict(db,"synthetic-g")["reason_codes"]==["REPRINT_TARGET_RELEASE_NOT_VERIFIED"]
    date_proof(db,"synthetic-h","2026-10-10")
    result=verdict(db,"synthetic-g")
    assert result["status"]=="legal" and "FUNCTIONAL_REPRINT_VERIFIED" in result["reason_codes"]
    shown=card_reprints(db,"synthetic-g",as_of="2026-10-11")["verified_reprints"][0]
    assert shown["format"]=="standard" and shown["platform"]=="live"


@pytest.mark.parametrize("fault",["future","invalid","banned","unverified"])
def test_equivalence_cannot_bypass_the_target_evidence(local_tmp,fault):
    db=_ready_db(local_tmp/"rules.sqlite3");_coverage(db);release_policy(db);reprint(db)
    date_proof(db,"synthetic-h","2026-10-12" if fault=="future" else
               "2026-00-01" if fault=="invalid" else "2026-10-10")
    if fault in {"banned","unverified"}:
        _assertion(db,"synthetic-target-restriction","restriction",subject="synthetic-h",
                   status="non_verified" if fault=="unverified" else "verified")
    assert verdict(db,"synthetic-g")["status"]=="unknown"


def test_physical_release_policy_does_not_assert_client_release_dates(local_tmp):
    db=_ready_db(local_tmp/"rules.sqlite3");_coverage(db);release_policy(db,"in_person")
    assert verdict(db)["status"]=="legal"
