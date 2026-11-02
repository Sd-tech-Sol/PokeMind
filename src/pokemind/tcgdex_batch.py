"""TCGdex's public GraphQL reader: fixed queries, no mutation or owner input.

The upstream schema/router are public at the pinned cards-database commit cited
in docs. Unlike REST briefs, these pages carry the catalog's descriptive fields.
"""
from __future__ import annotations

import hashlib
import json
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind.cards import (CatalogApiClient, CatalogError, NetworkFailure,
                            RequestBudgetExhausted, _identifier, _safe_api_url)
from urllib.parse import quote

ENDPOINT = "https://api.tcgdex.net/v2/graphql"
PAGE_SIZE = 100
MAX_RESPONSE = 8 * 1024 * 1024
CARD_FIELDS = """id localId name category hp stage rarity regulationMark illustrator
types description effect trainerType energyType retreat evolveFrom suffix dexId
item {name effect} variants {normal holo reverse firstEdition wPromo}
variants_detailed {type subtype size stamp foil}
abilities {type name effect} attacks {cost name effect damage}
weaknesses {type value} resistances {type value}
set {id name cardCount {official total}}"""
SET_FIELDS = """id name releaseDate tcgOnline serie {id name}
cardCount {official total normal holo reverse firstEd} cards {id localId name}"""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError("TCGDEX_BATCH_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise NetworkFailure("TCGDEX_BATCH_REDIRECT_BLOCKED")


class BatchClient:
    def __init__(self, *, maximum_requests=1_000, maximum_body_bytes=128 * 1024 * 1024,
                 requests_made=0, body_bytes_read=0, opener=None, sleep=time.sleep,
                 checkpoint=None):
        if (type(maximum_requests) is not int or not 1 <= maximum_requests <= 50_000
                or type(maximum_body_bytes) is not int or maximum_body_bytes < 1
                or not 0 <= requests_made <= maximum_requests
                or not 0 <= body_bytes_read <= maximum_body_bytes):
            raise CatalogError("TCGDEX_BATCH_ENVELOPE_INVALID")
        self.maximum_requests, self.maximum_body_bytes = maximum_requests, maximum_body_bytes
        self.requests_made, self.body_bytes_read = requests_made, body_bytes_read
        self.opener = opener or build_opener(_NoRedirect())
        self.sleep, self.checkpoint = sleep, checkpoint
        self.blocked_reason = None
        self.last_http_status = None
        self.last_evidence = None
        self.last_raw = None
        self.last_graphql_errors = []

    def _save(self):
        if self.checkpoint:
            self.checkpoint(self)

    def _read(self, response):
        length = response.headers.get("Content-Length")
        try:
            length = int(length) if length is not None else None
        except (ValueError, TypeError, OverflowError) as exc:
            raise CatalogError("TCGDEX_BATCH_RESPONSE_LENGTH_INVALID") from exc
        available = self.maximum_body_bytes - self.body_bytes_read
        if length is not None and (length < 0 or length > MAX_RESPONSE):
            raise CatalogError("TCGDEX_BATCH_RESPONSE_TOO_LARGE")
        if length is not None and length > available:
            raise RequestBudgetExhausted("TCGDEX_BATCH_BODY_BUDGET_EXHAUSTED")
        media_type = response.headers.get("Content-Type", "").lower()
        if "json" not in media_type:
            self.blocked_reason = "TCGDEX_BATCH_NON_JSON_BLOCKED"
            raise NetworkFailure(self.blocked_reason)
        if response.headers.get("Content-Encoding", "identity").lower() != "identity":
            raise CatalogError("TCGDEX_BATCH_ENCODING_REJECTED")
        parts, size = [], 0
        while length is None or size < length:
            available = self.maximum_body_bytes - self.body_bytes_read
            if available <= 0:
                raise RequestBudgetExhausted("TCGDEX_BATCH_BODY_BUDGET_EXHAUSTED")
            part = response.read(min(65_536, available, MAX_RESPONSE + 1 - size,
                                     length - size if length is not None else MAX_RESPONSE + 1))
            size += len(part)
            self.body_bytes_read += len(part)
            parts.append(part)
            self._save()
            if size > MAX_RESPONSE:
                raise CatalogError("TCGDEX_BATCH_RESPONSE_TOO_LARGE")
            if not part:
                break
        return b"".join(parts)

    def _reserve(self):
        if self.blocked_reason:
            raise NetworkFailure(self.blocked_reason)
        if self.requests_made >= self.maximum_requests:
            raise RequestBudgetExhausted("TCGDEX_BATCH_REQUEST_BUDGET_EXHAUSTED")
        if self.body_bytes_read >= self.maximum_body_bytes:
            raise RequestBudgetExhausted("TCGDEX_BATCH_BODY_BUDGET_EXHAUSTED")
        if self.requests_made:
            self.sleep(.5)
        self.requests_made += 1
        self.last_http_status = None
        self._save()

    def _query(self, query, *, purpose):
        body = json.dumps({"query": query}, separators=(",", ":")).encode("utf-8")
        if len(body) > 32_000:
            raise CatalogError("TCGDEX_BATCH_QUERY_TOO_LARGE")
        for attempt in range(3):
            self._reserve()  # same envelope for POST, fallback GET and retries
            request = Request(ENDPOINT, data=body, method="POST", headers={
                "Content-Type": "application/json", "Accept": "application/json",
                "Accept-Encoding": "identity", "User-Agent": "PokeMind/public-catalog-batch",
            })
            try:
                response = self.opener.open(request, timeout=30)
                try:
                    self.last_http_status = response.status
                    if response.geturl() != ENDPOINT:
                        raise NetworkFailure("TCGDEX_BATCH_FINAL_URL_BLOCKED")
                    raw = self._read(response)
                finally:
                    response.close()
                self.last_raw = raw
                try:
                    payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
                except (ValueError, UnicodeError) as exc:
                    raise CatalogError("TCGDEX_BATCH_JSON_INVALID") from exc
                if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
                    raise CatalogError("TCGDEX_BATCH_GRAPHQL_ERRORS")
                self.last_graphql_errors = payload.get("errors") or []
                if not isinstance(self.last_graphql_errors, list):
                    raise CatalogError("TCGDEX_BATCH_GRAPHQL_ERRORS")
                self.last_evidence = {
                    **purpose, "source_url": ENDPOINT, "method": "POST", "operation": "query",
                    "query_sha256": hashlib.sha256(body).hexdigest(),
                    "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw),
                }
                return payload["data"]
            except HTTPError as exc:
                self.last_http_status = exc.code
                try:
                    if exc.code in {401, 403, 429}:
                        self.blocked_reason = f"TCGDEX_BATCH_HTTP_{exc.code}_BLOCKED"
                        raise NetworkFailure(self.blocked_reason) from exc
                    if exc.code not in {500, 502, 503, 504} or attempt == 2:
                        raise NetworkFailure(f"TCGDEX_BATCH_HTTP_{exc.code}") from exc
                finally:
                    exc.close()
            except (URLError, TimeoutError, socket.timeout, OSError) as exc:
                if attempt == 2:
                    raise NetworkFailure("TCGDEX_BATCH_NETWORK_UNAVAILABLE") from exc
            self.sleep(3 * (attempt + 1))
        raise NetworkFailure("TCGDEX_BATCH_NETWORK_UNAVAILABLE")

    @staticmethod
    def _scope(kind, language):
        if kind not in {"cards", "sets"} or language not in {"en", "fr"}:
            raise CatalogError("TCGDEX_BATCH_SCOPE_INVALID")
        return CARD_FIELDS if kind == "cards" else SET_FIELDS

    def _rest_detail(self, kind, language, entity_id):
        """Repair a known serialization failure, not guess a missing text/name."""
        self._scope(kind, language)
        entity_id = _identifier(entity_id)
        path = f'/{language}/{kind}/{quote(entity_id, safe="!._-")}'
        expected_url = _safe_api_url(path)
        parent = self

        class SharedRest(CatalogApiClient):
            def _reserve_get(self):
                if self.remaining <= 0 or self.body_bytes_read >= self.maximum_body_bytes:
                    raise RequestBudgetExhausted("TCGDEX_BATCH_BODY_OR_REQUEST_BUDGET_EXHAUSTED")
                parent._reserve()
                self.requests_made += 1

        maximum = min(3, self.maximum_requests - self.requests_made)
        available = self.maximum_body_bytes - self.body_bytes_read
        if maximum < 1 or available < 1:
            raise RequestBudgetExhausted("TCGDEX_BATCH_BODY_OR_REQUEST_BUDGET_EXHAUSTED")
        rest = SharedRest(maximum, maximum_body_bytes=available, maximum_attempts=3,
                          stop_on_access_denial=True, opener=self.opener, sleep=self.sleep)
        try:
            payload, url = rest.get_json(path)
            if url != expected_url or not isinstance(payload, dict) or payload.get("id") != entity_id:
                raise CatalogError("TCGDEX_BATCH_REPAIR_ID_MISMATCH")
            from pokemind.cards import _canonical_sha256
            self.last_evidence.setdefault("rest_repairs", []).append({
                "kind": kind, "language": language, "id": entity_id, "source_url": url,
                "method": "GET", "payload_sha256": _canonical_sha256(payload),
            })
            return payload
        finally:
            self.body_bytes_read += rest.body_bytes_read
            self.last_http_status = rest.last_http_status
            if rest.blocked_reason:
                self.blocked_reason = rest.blocked_reason
            self._save()

    def page(self, kind, language, page):
        fields = self._scope(kind, language)
        if type(page) is not int or not 1 <= page <= 10_000:
            raise CatalogError("TCGDEX_BATCH_PAGE_INVALID")
        # filters:{} avoids an upstream parser bug with object-valued arguments.
        query = (f'query {{ {kind}(filters: {{}}, pagination: {{page: {page}, itemsPerPage: {PAGE_SIZE}}}, '
                 f'sort: {{field: "id", order: "ASC"}}) @locale(lang: "{language}") {{ {fields} }} }}')
        data = self._query(query, purpose={"kind": kind, "language": language, "page": page})
        rows = data.get(kind)
        if not isinstance(rows, list) or len(rows) > PAGE_SIZE or any(not isinstance(row, dict) for row in rows):
            raise CatalogError("TCGDEX_BATCH_PAGE_INVALID")
        repairs = set()
        for error in self.last_graphql_errors:
            path = error.get("path") if isinstance(error, dict) else None
            if (not isinstance(path, list) or len(path) < 3 or path[0] != kind
                    or type(path[1]) is not int or not 0 <= path[1] < len(rows)
                    or not isinstance(rows[path[1]].get("id"), str)):
                raise CatalogError("TCGDEX_BATCH_GRAPHQL_ERRORS")
            repairs.add(path[1])
        for index in sorted(repairs):
            rows[index] = self._rest_detail(kind, language, rows[index]["id"])
        return rows

    def missing(self, kind, language, ids):
        fields = self._scope(kind, language)
        if not isinstance(ids, list) or not 1 <= len(ids) <= 30 or len(set(ids)) != len(ids):
            raise CatalogError("TCGDEX_BATCH_SELECTION_INVALID")
        identifiers = [_identifier(value) for value in ids]
        if any("," in value or "|" in value for value in identifiers):
            raise CatalogError("TCGDEX_BATCH_QUERY_ID_REJECTED")
        singular = "card" if kind == "cards" else "set"
        query = "query { " + " ".join(
            f'p{n}: {singular}(filters: {{id: {json.dumps("eq:" + value)}}}) @locale(lang: "{language}") {{ {fields} }}'
            for n, value in enumerate(identifiers)) + " }"
        data = self._query(query, purpose={"kind": kind, "language": language, "ids": identifiers})
        if set(data) != {f"p{n}" for n in range(len(ids))}:
            raise CatalogError("TCGDEX_BATCH_SELECTION_RESPONSE_INVALID")
        repairs = set()
        for error in self.last_graphql_errors:
            path = error.get("path") if isinstance(error, dict) else None
            if not isinstance(path, list) or not path or path[0] not in data:
                raise CatalogError("TCGDEX_BATCH_GRAPHQL_ERRORS")
            repairs.add(path[0])
        for alias in sorted(repairs):
            index = int(alias[1:])
            data[alias] = self._rest_detail(kind, language, identifiers[index])
        return {value: data[f"p{n}"] for n, value in enumerate(identifiers)}
