"""Mocked PUBLIC endpoints; never touch a real provider or owner record."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from pokemind import batch_public_research as research

AS_OF = "2026-10-24"
URL = "https://api.tcgdex.net/v2/en/cards/invented-1"


class Response:
    status = 200
    def __init__(self, url, body): self.url, self.body = url, body
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def geturl(self): return self.url
    def read(self, n): return self.body[:n]


class Opener:
    def __init__(self, body=None, status=None): self.calls, self.body, self.status = [], body, status
    def open(self, request, timeout):
        self.calls.append(request.full_url)
        if self.status:
            raise HTTPError(request.full_url, self.status, "invented refusal", {}, None)
        return Response(request.full_url, self.body or json.dumps({"id": "invented-1", "name": "Invented card", "category": "Pokemon"}).encode())


def test_public_only_budget_retention_and_offline_reuse(local_tmp, monkeypatch):
    monkeypatch.setattr(research, "public_endpoints", lambda *a: [URL])
    opener = Opener()
    result = research.refresh_public(local_tmp, as_of=AS_OF, opener=opener)
    assert result["gets"] == 1 and result["facts"][0]["card"]["name"] == "Invented card"
    assert research.load_public_research(local_tmp, "2026-10-25")["facts"] == result["facts"]
    again = research.refresh_public(local_tmp, as_of=AS_OF, opener=opener)
    assert again["reused_offline"] and len(opener.calls) == 1


@pytest.mark.parametrize("status", [403, 429, 500])
def test_provider_refusal_stops_host_without_retry(local_tmp, monkeypatch, status):
    monkeypatch.setattr(research, "public_endpoints", lambda *a: [URL, URL.replace("invented-1", "invented-2")])
    opener = Opener(status=status)
    result = research.refresh_public(local_tmp, as_of=AS_OF, opener=opener)
    assert len(opener.calls) == result["gets"] == 1 and not result["facts"]
    assert result["closed_hosts"]["api.tcgdex.net"] == "HTTP_" + str(status)


@pytest.mark.parametrize("body", [b'<html>captcha</html>', b'not json', b'{"id":"wrong","name":"invented"}'])
def test_challenge_or_unproven_identity_never_becomes_fact(local_tmp, monkeypatch, body):
    monkeypatch.setattr(research, "public_endpoints", lambda *a: [URL])
    result = research.refresh_public(local_tmp, as_of=AS_OF, opener=Opener(body=body))
    assert not result["facts"] and result["closed_hosts"]


def test_get_and_byte_caps_before_exceeding_budget(local_tmp, monkeypatch):
    monkeypatch.setattr(research, "public_endpoints", lambda *a: [URL, URL.replace("invented-1", "invented-2")])
    monkeypatch.setattr(research, "MAX_GETS", 1)
    monkeypatch.setattr(research, "MAX_BYTES", 32)
    result = research.refresh_public(local_tmp, as_of=AS_OF, opener=Opener(body=b'x' * 100))
    assert result["gets"] <= 1 and result["bytes"] <= 32 and not result["facts"]


@pytest.mark.parametrize("url", ["file:///private", "https://api.tcgdex.net/v2/en/cards/test?private=1",
    "https://user:secret@api.tcgdex.net/v2/en/cards/test", "https://private.invalid/data",
    "https://api.tcgdex.net/v2/en/cards/../../private"])
def test_no_arbitrary_or_private_network_url(url):
    with pytest.raises(ValueError): research.allowed_url(url)


def test_no_private_parameters_in_public_api(local_tmp):
    with pytest.raises(TypeError):
        research.refresh_public(local_tmp, as_of=AS_OF, player="invented")


def test_robots_disallow_prevents_html_request(local_tmp, monkeypatch):
    monkeypatch.setattr(research, "public_endpoints", lambda *a: ["https://www.limitlesstcg.com/decks"])
    opener = Opener(body=b'User-agent: *\nDisallow: /decks\n')
    result = research.refresh_public(local_tmp, as_of=AS_OF, opener=opener)
    assert opener.calls == ["https://www.limitlesstcg.com/robots.txt"]
    assert result["gets"] == 1 and not result["facts"]
