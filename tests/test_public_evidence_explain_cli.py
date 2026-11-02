"""Player-facing CLI over two invented exact SQLite files; no live data."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path

import pytest

from pokemind import cli, public_deck_preflight as preflight, set_code_aliases
from test_public_identity_rules_scoped import AS_OF, TEXT, bridge, fixture_pair, forbid, no_discovery

if os.environ.get('POKEMIND_SYNTHETIC_QA_ROOT'):
    # Import before the journey's stricter fixture restricts all non-pair IO.
    from qa_synthetic_cli import call as synthetic_call
else:
    synthetic_call = None


def two_compositions(root):
    paths = fixture_pair(root)
    second = TEXT.replace("1 Invented Scout", "2 Invented Scout").replace("58 Fire", "57 Fire")
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("INSERT INTO meta_competitive_lists VALUES (?,?,?,?,?)",
                  ("invented", 3, "https://www.limitlesstcg.com/decks/list/999999", "2026-10-22", second))
        c.execute("UPDATE meta_competitive_lists SET list_url='https://www.limitlesstcg.com/decks/list/999999'")
    return paths


def call(root, args, *, guarded=False):
    if synthetic_call is not None:
        return synthetic_call(root, args)
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONDONTWRITEBYTECODE": "1"}
    command = [sys.executable, "-B", "-c", GUARD, *args] if guarded else [sys.executable, "-B", "-m", "pokemind", *args]
    return subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40)


# Install after importing static product code. Subsequent attempts to discover
# filenames, open anything outside the pair, write, access network or use the
# generic root/default-DB routes fail. This is not the real-cache field harness.
GUARD = r'''
from pathlib import Path
import os,sys,sqlite3
from pokemind import cli,public_deck_preflight as p,set_code_aliases
allowed={os.path.normcase(str(Path.cwd()/s)) for s in p.SCOPED_PUBLIC_CACHES}
uris={(Path.cwd()/s).as_uri()+"?mode=ro&immutable=1" for s in p.SCOPED_PUBLIC_CACHES}
def forbid(*a,**k): raise AssertionError("FORBIDDEN_DEPENDENCY")
cli.find_project_root=cli.default_db_path=cli._db_for=forbid
p.competitive._advisor_snapshot=p.require_public_database=forbid
def audit(event,args):
 if event in {"os.listdir","os.scandir","os.walk","pathlib.Path.glob","pathlib.Path.rglob","glob.glob","glob.glob/2"} or event.startswith("socket."):
  raise AssertionError("FORBIDDEN_DISCOVERY_OR_NETWORK")
 if event=="sqlite3.connect" and args[0] not in uris: raise AssertionError("THIRD_DATABASE")
 if event=="open":
  name,mode,flags=args
  if isinstance(name,int) or os.path.normcase(os.path.abspath(name)) not in allowed: raise AssertionError("THIRD_FILE")
  if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND): raise AssertionError("WRITE")
sys.addaudithook(audit)
raise SystemExit(cli.main(sys.argv[1:]))
'''


def test_filtered_view_counts_only_selected_composition(local_tmp, monkeypatch):
    two_compositions(local_tmp)
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    with monkeypatch.context() as m:
        no_discovery(m)
        result = preflight.identity_explain(local_tmp, as_of=AS_OF, selector="invented:2")
    assert result["schema_version"] == 1 and result["model"] == "public-identity-explain-v1"
    assert result["totals"]["placements"] == 3 and result["totals"]["compositions"] == 2
    assert result["selected_totals"] == {"placements": 2, "compositions": 1, "resolved_rows": 1,
        "row_denominator": 3, "resolved_copies": 1, "copy_denominator": 60}
    assert result["compositions"][0]["selectors"] == ["invented:1", "invented:2"]
    mee = next(r for r in result["identity_matrix"] if r["code"] == "MEE")
    assert mee["copies"] == 58 and mee["rows"] == 1
    assert mee["identity"] == "unknown"
    ambiguous = next(r for r in result["identity_matrix"] if r["code"] == "30C")
    assert ambiguous["set_context"] == {"native_sets": ["old30"], "alias_sets": ["new30"]}
    assert all(c["status"] == "descriptive_candidate_not_confirmed_identity" for c in mee["candidates"])
    assert result["compositions"][0]["in_person"] == result["compositions"][0]["live"] == "unknown"


@pytest.mark.parametrize("arguments", [[], ["--json"], ["--selector", "invented:2"],
                                     ["--selector", "invented:2", "--json"]])
def test_real_module_cli_utf8_from_cp1252_and_no_mutation(local_tmp, arguments):
    paths = two_compositions(local_tmp)
    before = [preflight._scoped_file_stamp(p) for p in paths]
    args = ["meta", "public-identity-explain", "--as-of", AS_OF, *arguments]
    first, second = call(local_tmp, args), call(local_tmp, args)
    assert first.returncode == second.returncode == 0, first.stderr.decode("utf-8")
    assert first.stdout == second.stdout and not first.stderr
    text = first.stdout.decode("utf-8", errors="strict")
    count = 1 if "--selector" in arguments else 2
    if "--json" in arguments:
        payload = json.loads(text)
        assert payload["ok"] and payload["source_status"] == "SOURCE_UNREVALIDATED"
        assert payload["source_validation"] == "BLOCKED_SOURCE_SCOPE"
        assert len(payload["compositions"]) == count
        assert payload["exact_sqlite_files_unchanged"] == 2 and not payload["network_used"]
        assert not payload["owner_database_opened"] and not payload["full_legality_preflight_executed"]
        for c in payload["compositions"]:
            assert c["in_person"] == c["live"] == "unknown"
            assert c["next_evidence"]["in_person"] and c["next_evidence"]["live"]
    else:
        assert text.count("\nComposition ") == count
        assert "Identité inconnue" in text and "Prochaine preuve" in text
        assert "SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE" in text
        assert "in_person : unknown" in text and "live : unknown" in text
        assert "https://www.limitlesstcg.com/decks/list/999999" in text
        assert "python -m pokemind meta public-identity-explain" in text
    assert "NOT_RELEASE_READY" in text and str(local_tmp) not in text
    assert before == [preflight._scoped_file_stamp(p) for p in paths]


@pytest.mark.parametrize("arguments", [[], ["--json"], ["--selector", "invented:2", "--json"]])
def test_cli_subprocess_audit_rejects_all_extra_io(local_tmp, arguments):
    paths = two_compositions(local_tmp)
    before = [preflight._scoped_file_stamp(p) for p in paths]
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, *arguments], guarded=True)
    assert result.returncode == 0, result.stderr.decode("utf-8")
    assert b"BLOCKED_SOURCE_SCOPE" in result.stdout and not result.stderr
    assert before == [preflight._scoped_file_stamp(p) for p in paths]


@pytest.mark.parametrize("json_mode", [False, True])
def test_unknown_selector_clear_safe_error(local_tmp, json_mode):
    two_compositions(local_tmp)
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF,
                            "--selector", "invented:999", *(["--json"] if json_mode else [])], guarded=True)
    assert result.returncode == 2
    output = (result.stdout + result.stderr).decode("utf-8")
    assert "PUBLIC_IDENTITY_SELECTOR_UNKNOWN" in output and "Composition inconnue" in output
    assert str(local_tmp) not in output and "Traceback" not in output


@pytest.mark.parametrize("arguments,code", [(["--as-of", "wrong"], "PUBLIC_IDENTITY_DATE_REQUIRED"),
    (["--as-of", AS_OF, "--selector", "../private"], "PUBLIC_IDENTITY_SELECTOR_INVALID")])
def test_invalid_input_before_any_read(local_tmp, monkeypatch, capsys, arguments, code):
    monkeypatch.setattr(preflight, "scoped_identity_rules_observations", forbid)
    monkeypatch.setattr(cli, "find_project_root", forbid)
    assert cli.main(["meta", "public-identity-explain", *arguments, "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["error_code"] == code and not payload["ok"]


def test_missing_cache_no_fallback_or_path_leak(local_tmp):
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, "--json"], guarded=True)
    assert result.returncode == 2
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["error_code"] == "PUBLIC_IDENTITY_CACHE_MISSING"
    assert str(local_tmp) not in str(payload) and not result.stderr


def test_no_arbitrary_database_flag():
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args(["meta", "public-identity-explain", "--as-of", AS_OF, "--db", "unused"])
    assert exc.value.code == 2


@pytest.mark.parametrize("kind", [KeyError, TypeError, AttributeError, IndexError])
def test_malformed_cache_error_is_neutral_without_traceback(monkeypatch, capsys, kind):
    def bad_cache(*a, **kw):
        raise kind(r"C:\Users\invented\private-cache")
    monkeypatch.setattr(preflight, "scoped_identity_rules_observations", bad_cache)
    monkeypatch.setattr(cli, "find_project_root", forbid)
    assert cli.main(["meta", "public-identity-explain", "--as-of", AS_OF, "--json"]) == 2
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload["error_code"] == "PUBLIC_IDENTITY_EXPLAIN_BLOCKED"
    assert "Users" not in output.out and "Traceback" not in output.out and not output.err


@pytest.mark.parametrize("value", [r"C:\Users\invented\private.db", "/home/invented/private", "file:///private",
                                    "https://github.com/invented?secret=synthetic", "https://user:pass@github.com/invented"])
def test_sensitive_or_untrusted_url_not_emitted(value):
    assert preflight._explain_url(value) is None


def test_json_projection_excludes_raw_payloads_private_paths_and_hashes(local_tmp, monkeypatch):
    paths = two_compositions(local_tmp)
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("UPDATE meta_competitive_lists SET list_url='file:///invented-private', fetched_at=?",
                  (r"C:\Users\invented\private",))
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    report = preflight.identity_explain(local_tmp, as_of=AS_OF)
    text = json.dumps(report, ensure_ascii=False)
    assert "file:///" not in text and "C:\\\\Users" not in text
    assert "sha256" not in text and "payload_json" not in text
    assert all(s["url"] is None and s["observed_at"] == "[contenu non affiché]"
               for c in report["compositions"] for s in c["sources"])


def test_cached_selector_cannot_inject_a_copiable_command(local_tmp):
    paths = two_compositions(local_tmp)
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("UPDATE meta_competitive_lists SET event_id='$(invented)' ")
    with pytest.raises(ValueError, match="PUBLIC_IDENTITY_SELECTOR_INVALID"):
        preflight.identity_explain(local_tmp, as_of=AS_OF)


class HtmlView(HTMLParser):
    """Inspect the document a browser receives, including decoded attributes."""
    def __init__(self, document):
        super().__init__(convert_charrefs=True)
        self.elements, self.words, self.tables = [], [], []
        self.row = self.cell = None
        self.feed(document)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        if tag == "table":
            self.tables.append([])
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.cell = []

    def handle_data(self, value):
        self.words.append(value)
        if self.cell is not None:
            self.cell.append(value)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append("".join(self.cell))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None


@pytest.mark.parametrize("selector", [None, "invented:2"])
def test_html_real_module_matches_json_totals_and_blockers(local_tmp, selector):
    paths = two_compositions(local_tmp)
    before = [preflight._scoped_file_stamp(p) for p in paths]
    args = ["meta", "public-identity-explain", "--as-of", AS_OF]
    if selector:
        args.extend(["--selector", selector])
    html = call(local_tmp, [*args, "--html"])
    again = call(local_tmp, [*args, "--html"])
    json_result = call(local_tmp, [*args, "--json"])
    assert html.returncode == again.returncode == json_result.returncode == 0
    assert html.stdout == again.stdout and not html.stderr and not again.stderr
    document = html.stdout.decode("utf-8", errors="strict")
    payload = json.loads(json_result.stdout.decode("utf-8", errors="strict"))
    view = HtmlView(document)
    assert document.startswith("<!doctype html>") and document.rstrip().endswith("</html>")
    assert ("html", {"lang": "fr-CA"}) in view.elements
    assert ("meta", {"charset": "utf-8"}) in view.elements
    assert view.tables[0][1:] == [[label, str(t["placements"]), str(t["compositions"]),
        f'{t["resolved_rows"]}/{t["row_denominator"]}', f'{t["resolved_copies"]}/{t["copy_denominator"]}']
        for label, t in (("Cache complet", payload["totals"]), ("Vue sélectionnée", payload["selected_totals"]))]
    assert len(view.tables[1]) - 1 == len(payload["compositions"])
    words = " ".join(view.words)
    for comp in payload["compositions"]:
        assert [", ".join(comp["selectors"]), f'{comp["coverage"]["resolved_rows"]}/{comp["coverage"]["row_denominator"]}',
            f'{comp["coverage"]["resolved_copies"]}/{comp["coverage"]["copy_denominator"]}', "unknown", "unknown"] in view.tables[1]
        for platform in ("in_person", "live"):
            assert all(code in words for code in comp["blockers"][platform])
            assert all(proof["required"] in words for proof in comp["next_evidence"][platform])
        for source in comp["sources"]:
            assert source["observed_at"] in words
    assert "SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE" in words and "NOT_RELEASE_READY" in words
    assert str(local_tmp) not in document and "sha256" not in document and "payload_json" not in document
    assert before == [preflight._scoped_file_stamp(p) for p in paths]


@pytest.mark.parametrize("arguments", [[], ["--selector", "invented:2"]])
def test_html_guarded_no_discovery_network_writes_or_extra_files(local_tmp, arguments):
    paths = two_compositions(local_tmp)
    before = [preflight._scoped_file_stamp(p) for p in paths]
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, "--html", *arguments], guarded=True)
    assert result.returncode == 0 and not result.stderr
    assert result.stdout.startswith(b"<!doctype html>") and b"BLOCKED_SOURCE_SCOPE" in result.stdout
    assert before == [preflight._scoped_file_stamp(p) for p in paths]


def test_html_keyboard_navigation_csp_and_no_remote_or_active_elements(local_tmp):
    two_compositions(local_tmp)
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, "--html"])
    assert result.returncode == 0
    view = HtmlView(result.stdout.decode("utf-8", errors="strict"))
    ids = [attrs["id"] for _, attrs in view.elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    links = [a["href"] for tag, a in view.elements if tag == "a"]
    assert links and all(href.startswith("#") and href[1:] in ids for href in links)
    assert sum(tag == "details" for tag, _ in view.elements) == sum(tag == "summary" for tag, _ in view.elements) >= 4
    assert all(attrs.get("scope") == "col" for tag, attrs in view.elements if tag == "th")
    assert any(tag == "nav" and attrs.get("aria-label") for tag, attrs in view.elements)
    assert any(tag == "div" and attrs.get("tabindex") == "0" and attrs.get("role") == "region" for tag, attrs in view.elements)
    policy = next(attrs["content"] for tag, attrs in view.elements if tag == "meta" and attrs.get("http-equiv") == "Content-Security-Policy")
    for rule in ("default-src 'none'", "style-src 'unsafe-inline'", "base-uri 'none'", "form-action 'none'"):
        assert rule in policy
    forbidden = {"script", "img", "link", "iframe", "object", "embed", "base", "form", "input", "video", "audio", "svg", "math"}
    assert all(tag not in forbidden for tag, _ in view.elements)
    assert all(not key.lower().startswith("on") and key not in {"src", "srcset", "action", "style"}
               for _, attrs in view.elements for key in attrs)
    document = result.stdout.decode("utf-8")
    assert "url(" not in document and "@import" not in document and ":focus-visible" in document


@pytest.mark.parametrize("payload", ['<script>alert("invented")</script>',
    '\"><img src=x onerror=alert(1)>', "</style><svg onload=alert(1)>",
    "&lt;iframe srcdoc='invented'&gt;", "<a href='javascript:alert(1)'>invented</a>"])
def test_html_cache_markup_is_escaped_as_text(local_tmp, payload):
    paths = two_compositions(local_tmp)
    with closing(sqlite3.connect(paths[1])) as c, c:
        c.execute("UPDATE catalog_translations SET name=?,retrieved_at=? WHERE printing_id='mee-010'", (payload, payload))
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("UPDATE meta_competitive_lists SET fetched_at=?", (payload,))
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, "--html"])
    assert result.returncode == 0 and not result.stderr
    document = result.stdout.decode("utf-8", errors="strict")
    view = HtmlView(document)
    assert payload in " ".join(view.words) and payload not in document
    assert all(tag not in {"script", "img", "svg", "iframe"} for tag, _ in view.elements)
    assert all(not key.startswith("on") for _, attrs in view.elements for key in attrs)


@pytest.mark.parametrize("url", ["https://user:password@github.com/invented", "https://github.com/invented?token=invented",
    'https://github.com/invented?x=\"><img&date=2026-10-23', "file:///invented-private"])
def test_html_sensitive_url_not_in_output(local_tmp, url):
    paths = two_compositions(local_tmp)
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("UPDATE meta_competitive_lists SET list_url=?", (url,))
    with closing(sqlite3.connect(paths[1])) as c, c:
        c.execute("UPDATE catalog_translations SET source_url=?", (url,))
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, "--html"])
    document = result.stdout.decode("utf-8", errors="strict")
    assert result.returncode == 0 and "URL non affichée" in document
    assert url not in document and "password" not in document and "token=invented" not in document


@pytest.mark.parametrize("arguments,fixture,code", [
    ([], False, "PUBLIC_IDENTITY_CACHE_MISSING"),
    (["--selector", "invented:999"], True, "PUBLIC_IDENTITY_SELECTOR_UNKNOWN"),
    (["--selector", "../private"], False, "PUBLIC_IDENTITY_SELECTOR_INVALID"),
    (["--as-of", "bad"], False, "PUBLIC_IDENTITY_DATE_REQUIRED"),
])
def test_html_errors_are_complete_neutral_pages(local_tmp, arguments, fixture, code):
    if fixture:
        two_compositions(local_tmp)
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, "--html", *arguments], guarded=True)
    document = result.stdout.decode("utf-8", errors="strict")
    assert result.returncode == 2 and not result.stderr
    assert document.startswith("<!doctype html>") and document.rstrip().endswith("</html>")
    assert code in document and "SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE" in document
    assert "in_person = unknown" in document and "live = unknown" in document and "NOT_RELEASE_READY" in document
    assert str(local_tmp) not in document and "Traceback" not in document


@pytest.mark.parametrize("arguments", [["--html", "--json"], ["--json", "--html"]])
def test_html_and_json_conflict_before_data_access(local_tmp, arguments):
    result = call(local_tmp, ["meta", "public-identity-explain", "--as-of", AS_OF, *arguments], guarded=True)
    assert result.returncode == 2 and not result.stdout
    assert b"not allowed with argument" in result.stderr
    assert b"Traceback" not in result.stderr


@pytest.mark.parametrize("kind", [KeyError, TypeError, AttributeError, IndexError])
def test_html_malformed_cache_keeps_safe_error_labels(monkeypatch, capsys, kind):
    def fail(*a, **kw):
        raise kind(r"C:\Users\invented\private-cache")
    monkeypatch.setattr(preflight, "scoped_identity_rules_observations", fail)
    monkeypatch.setattr(cli, "find_project_root", forbid)
    assert cli.main(["meta", "public-identity-explain", "--as-of", AS_OF, "--html"]) == 2
    output = capsys.readouterr()
    assert "PUBLIC_IDENTITY_EXPLAIN_BLOCKED" in output.out and not output.err
    assert "SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE" in output.out
    assert "Users" not in output.out and "Traceback" not in output.out


def test_html_empty_view_never_removes_source_block():
    document = preflight.html_identity_explain()
    assert "SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE" in document
    assert "in_person = unknown" in document and "live = unknown" in document
    assert "Aucun contenu disponible" in document and "NOT_RELEASE_READY" in document


@pytest.mark.parametrize("payload", ['\"><svg onload="invented()">', '</summary><script>invented()</script>',
                                     'https://github.com/invented/\"><img src=x>'])
def test_html_all_projected_text_fields_are_inert_even_with_candidates(local_tmp, monkeypatch, payload):
    two_compositions(local_tmp)
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    report = preflight.identity_explain(local_tmp, as_of=AS_OF)
    assert any(row["candidates"] for row in report["identity_matrix"])
    def hostile(value):
        if isinstance(value, dict):
            return {key: hostile(item) for key, item in value.items()}
        if isinstance(value, list):
            return [hostile(item) for item in value]
        return payload if isinstance(value, str) else value
    report = hostile(report)
    report["raw_payload"] = "UNPROJECTED_SYNTHETIC_PRIVATE_FIELD"
    with monkeypatch.context() as m:
        no_discovery(m)
        document = preflight.html_identity_explain(report)
    view = HtmlView(document)
    assert payload in " ".join(view.words) and payload not in document
    assert "UNPROJECTED_SYNTHETIC_PRIVATE_FIELD" not in document
    assert all(tag not in {"svg", "script", "img"} for tag, _ in view.elements)
    assert all(not key.startswith("on") for _, attrs in view.elements for key in attrs)
    assert all(attrs["href"].startswith("#") for tag, attrs in view.elements if tag == "a")


def test_html_empty_composition_projection_preserves_warning(local_tmp):
    two_compositions(local_tmp)
    report = preflight.identity_explain(local_tmp, as_of=AS_OF)
    report["compositions"] = []
    report["identity_matrix"] = []
    document = preflight.html_identity_explain(report)
    assert "Aucune composition à afficher" in document
    assert "SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE" in document
    assert "in_person = unknown" in document and "live = unknown" in document
