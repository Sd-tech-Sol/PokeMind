"""Offline tournament-list checks against separate, explicitly PUBLIC reference data."""
from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

from pokemind import competitive, rules
from pokemind.database import connect_readonly
from pokemind.public_campaign import public_database_path, require_public_database


STATES = ("legal", "not_legal", "unknown")
SCOPED_PUBLIC_CACHES = (
    "data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3",
    "data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3",
)
MISSING_EVIDENCE = ["explicit_existing_public_competitive_db", "explicit_existing_public_reference_db",
                    "catalog_printing_identity", "dated_official_rules"]


def _scoped_file_stamp(path: Path):
    """Inspect only literal ancestors and this file, never siblings or sidecars."""
    import hashlib
    import stat

    for ancestor in (*reversed(path.parents), path):
        info = ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
            raise ValueError("SCOPED_REDIRECTION_BLOCKED")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("SCOPED_FILE_UNSAFE")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        header = source.read(100)
        # immutable avoids *all* sidecar I/O; refuse WAL-format main files.
        if header[:16] != b"SQLite format 3\x00" or header[18:20] != b"\x01\x01":
            raise ValueError("SCOPED_SQLITE_NOT_STANDALONE")
        digest.update(header)
        while block := source.read(1024 * 1024):
            digest.update(block)
    return (info.st_dev, info.st_ino, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, digest.digest())


def _scoped_observations(lists, reference, *, as_of: str, bridge: dict) -> dict:
    """Cache observations only. Reuse parser/identity rules, never source verifier.

    Neither an unverified list nor a catalog candidate is promoted to a proven
    printing. No complete legality verdict is attempted without the page proof.
    """
    from pokemind.set_code_aliases import alias_sets, collector_key

    groups, matrix = {}, {}
    for row in lists:
        cards = competitive._card_map(row["deck_text"])
        if sum(c["quantity"] for c in cards.values()) != 60:
            raise ValueError("SCOPED_CACHED_LIST_NOT_60")
        key = competitive._composition_id(cards)
        group = groups.setdefault(key, {"cards": cards, "selectors": [], "sources": []})
        group["selectors"].append(f"{row['event_id']}:{row['placement']}")
        group["sources"].append({"url": row["list_url"], "observed_at": row["fetched_at"],
                                 "status": "cache_metadata_not_page_revalidated"})
    row_count = copy_count = resolved_rows = resolved_copies = 0
    all_identities, resolved_identities = set(), set()
    compositions = []
    for group in groups.values():
        missing = []
        gaps = []
        initial_rows, initial_copies = resolved_rows, resolved_copies
        for card in group["cards"].values():
            row_count += 1
            copy_count += card["quantity"]
            entry = {"card_name": card["name"], "set_code": card["set"],
                     "collector_number": card["number"]}
            ident = (card["name"], card["set"], card["number"])
            all_identities.add(ident)
            identity = rules._resolve_structure_identity(reference, entry, set_aliases=bridge)
            if len(identity["ids"]) == 1:
                resolved_rows += 1
                resolved_copies += card["quantity"]
                resolved_identities.add(ident)
                continue
            missing.append(" / ".join(ident))
            gaps.append({"name": ident[0], "code": ident[1], "number": ident[2],
                         "quantity": card["quantity"], "reason": identity["resolution_reason"]})
            item = matrix.setdefault(ident, {"name": ident[0], "code": ident[1], "number": ident[2],
                "reason": identity["resolution_reason"], "identity": "unknown", "rows": 0,
                "copies": 0, "selectors": [], "list_sources": [], "catalog_candidates": [],
                "alias_sources": [{k: v for k, v in e.items() if k in {
                    "set_id", "code", "language", "release_date", "retrieved_at", "source_url", "source_commit"}}
                    for e in identity.get("alias_evidence", [])]})
            item["rows"] += 1
            item["copies"] += card["quantity"]
            item["selectors"].extend(group["selectors"])
            item["list_sources"].extend(group["sources"])
            # Number/set candidates are context, NEVER an identity fallback.
            sets, _ = alias_sets(bridge, card["set"])
            native = [r[0] for r in reference.execute(
                "SELECT tcgdex_id FROM catalog_sets WHERE lower(tcg_online_code)=lower(?)", (card["set"],))]
            item["set_context"] = {"native_sets": native, "alias_sets": sets}
            for set_id in sorted(set(sets + native)):
                for candidate in reference.execute(
                    "SELECT p.tcgdex_id,p.set_id,p.local_id,p.regulation_mark,p.variants_json,"
                    "t.language,t.name,t.source_url,t.retrieved_at FROM catalog_printings p "
                    "LEFT JOIN catalog_translations t ON t.printing_id=p.tcgdex_id AND t.status='present' "
                    "WHERE p.set_id=? ORDER BY p.tcgdex_id,t.language", (set_id,)):
                    if collector_key(candidate["local_id"]) == collector_key(card["number"]):
                        value = dict(candidate)
                        value["variants"] = [{k: v for k, v in variant.items() if k in {"type", "stamp"}}
                            for variant in json.loads(value.pop("variants_json") or "[]")]
                        if value not in item["catalog_candidates"]:
                            item["catalog_candidates"].append(value)
        compositions.append({"selectors": group["selectors"], "sources": group["sources"],
            "cached_cards": 60, "identity_rows": len(group["cards"]), "missing_identities": missing,
            "identity_gaps": gaps,
            "coverage": {"resolved_rows": resolved_rows - initial_rows, "row_denominator": len(group["cards"]),
                         "resolved_copies": resolved_copies - initial_copies, "copy_denominator": 60},
            "in_person": "unknown", "live": "unknown", "source_validation": "BLOCKED_SOURCE_SCOPE"})
    normative = {}
    for platform in ("in_person", "live"):
        rows = reference.execute(
            "SELECT a.*,s.url,s.published_date,s.consulted_at,"
            "s.validation_status AS source_validation_status,"
            "s.effective_from AS source_effective_from,s.effective_to AS source_effective_to "
            "FROM official_rule_assertions a JOIN official_rule_sources s USING(source_id) "
            "WHERE (a.format='standard' OR a.format IS NULL) AND (a.platform=? OR a.platform IS NULL) "
            "ORDER BY a.assertion_id", (platform,)).fetchall()
        active = [dict(r) for r in rows if rules._active(r, as_of) and rules._source_active(r, as_of)
                  and r["validation_status"] == r["source_validation_status"] == "verified"
                  and (not r["published_date"] or r["published_date"] <= as_of)]
        normative[platform] = {"active_verified_assertions": active,
            "cached_assertions": len(rows),
            "cached_assertion_windows": [{k: r[k] for k in ("assertion_id", "assertion_kind", "source_id",
                "effective_from", "effective_to", "source_effective_from", "source_effective_to")} for r in rows],
            "structure": rules._structure_rule_context(reference, format="standard", platform=platform, as_of=as_of),
            "rotation_proven": sum(r["assertion_kind"] == "rotation" for r in active) == 1,
            "printing_live_availability": "unknown"}
    for composition in compositions:
        composition["blockers"] = {}
        for platform, evidence in normative.items():
            reasons = ["BLOCKED_SOURCE_SCOPE"]
            if composition["missing_identities"]:
                reasons.append("PRINTING_IDENTITIES_INCOMPLETE")
            if not evidence["rotation_proven"]:
                reasons.append("NO_UNIQUE_ACTIVE_ROTATION")
            structure = evidence["structure"].get("payload")
            if structure is None or not structure.get("copy_limit_exceptions_complete"):
                reasons.append("COPY_LIMIT_EXCEPTION_REGISTRY_INCOMPLETE")
            if structure is None or not structure.get("special_rule_limits_complete"):
                reasons.append("SPECIAL_CARD_RULE_LIMITS_INCOMPLETE")
            if platform == "live":
                reasons.append("PRINTING_SPECIFIC_LIVE_AVAILABILITY_UNKNOWN")
            composition["blockers"][platform] = reasons
    return {"as_of": as_of, "status": "PARTIAL_WITH_EVIDENCE", "source_validation": "BLOCKED_SOURCE_SCOPE",
        "scope": "unrevalidated_public_cache_observations_only", "placements": len(lists),
        "compositions": compositions, "identity_matrix": sorted(matrix.values(), key=lambda x: (x["code"], x["number"], x["name"])),
        "row_denominator": row_count, "copy_denominator": copy_count,
        "resolved_rows": resolved_rows, "resolved_copies": resolved_copies,
        "unique_listed_identities": len(all_identities), "unique_resolved_identities": len(resolved_identities),
        "normative": normative, "provider_gets": 0, "owner_database_opened": False}


def scoped_identity_rules_observations(root: Path, *, as_of: str) -> dict:
    """Manual, fixed two-file inspection; no marker, ledger, page or discovery.

    This cannot replace competitive_preflight's full source validation. SQLite
    immutable reads exclude sidecars and assume no concurrent writer; byte and
    metadata comparison is an observation, not a filesystem isolation guarantee.
    """
    import sqlite3
    from contextlib import ExitStack, closing
    from datetime import date
    from pokemind.set_code_aliases import build_aliases

    if date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("SCOPED_DATE_REQUIRED")
    if ".." in root.parts:
        raise ValueError("SCOPED_ROOT_INVALID")
    paths = [root.absolute() / relative for relative in SCOPED_PUBLIC_CACHES]
    before = [_scoped_file_stamp(p) for p in paths]
    with ExitStack() as stack:
        connections = []
        for path in paths:
            connection = stack.enter_context(closing(sqlite3.connect(
                path.as_uri() + "?mode=ro&immutable=1", uri=True)))
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            connections.append(connection)
        lists = connections[0].execute(
            "SELECT event_id,placement,list_url,fetched_at,deck_text FROM meta_competitive_lists "
            "ORDER BY event_id,placement LIMIT 501").fetchall()
        if not lists or len(lists) > 500:
            raise ValueError("SCOPED_SAMPLE_EMPTY_OR_OVER_CAP")
        reference = connections[1]
        report = _scoped_observations(lists, reference, as_of=as_of,
                                      bridge=build_aliases(reference, as_of=as_of))
    if before != [_scoped_file_stamp(p) for p in paths]:
        raise ValueError("SCOPED_SOURCE_CHANGED")
    return {**report, "exact_sqlite_files_unchanged": 2,
            "concurrent_writer_exclusion": "not_proven", "full_legality_preflight_executed": False}


NEXT_IDENTITY_EVIDENCE = {
    "BLOCKED_SOURCE_SCOPE": "Revalider les listes contre leurs sources complètes dans un mandat distinct.",
    "PRINTING_IDENTITIES_INCOMPLETE": "Prouver le nom, le code, l’édition et le numéro de chaque identité inconnue.",
    "NO_UNIQUE_ACTIVE_ROTATION": "Obtenir une rotation officielle vérifiée qui couvre la date évaluée.",
    "COPY_LIMIT_EXCEPTION_REGISTRY_INCOMPLETE": "Compléter les exceptions officielles au quota de copies.",
    "SPECIAL_CARD_RULE_LIMITS_INCOMPLETE": "Compléter les limites officielles des cartes à règle spéciale.",
    "PRINTING_SPECIFIC_LIVE_AVAILABILITY_UNKNOWN": "Prouver la disponibilité Live de chaque impression séparément.",
}


def _explain_text(value) -> str:
    import re
    text = str(value or "")
    if re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/(?:Users|home|tmp)/", text, re.I):
        return "[contenu non affiché]"
    return " ".join("".join(c for c in text if c.isprintable()).split())[:512]


def _explain_url(value) -> str | None:
    from urllib.parse import urlsplit
    if not isinstance(value, str) or any(not c.isprintable() for c in value):
        return None
    try:
        url = urlsplit(value)
        if (url.scheme == "https" and url.hostname in {
                "github.com", "api.tcgdex.net", "www.limitlesstcg.com", "www.pokemon.com",
                "play.pokemon.com", "assets.pokemon.com"}
                and not url.username and not url.password and not url.query and not url.fragment
                and url.port in (None, 443)):
            return value
    except ValueError:
        pass
    return None


def identity_explain(root: Path, *, as_of: str, selector: str | None = None) -> dict:
    """Project the existing observations into a versioned, non-certifying player view."""
    import re
    from datetime import date
    try:
        if date.fromisoformat(as_of).isoformat() != as_of:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("PUBLIC_IDENTITY_DATE_REQUIRED") from None
    if selector is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}:[1-9][0-9]{0,5}", selector):
        raise ValueError("PUBLIC_IDENTITY_SELECTOR_INVALID")
    raw = scoped_identity_rules_observations(root, as_of=as_of)
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}:[1-9][0-9]{0,5}", s)
           for c in raw["compositions"] for s in c["selectors"]):
        raise ValueError("PUBLIC_IDENTITY_SELECTOR_INVALID")
    selected = [c for c in raw["compositions"] if selector is None or selector in c["selectors"]]
    if not selected:
        raise ValueError("PUBLIC_IDENTITY_SELECTOR_UNKNOWN")
    compositions = []
    for comp in selected:
        compositions.append({"selectors": [_explain_text(s) for s in comp["selectors"]],
            "coverage": comp["coverage"], "in_person": "unknown", "live": "unknown",
            "source_status": "SOURCE_UNREVALIDATED", "source_validation": "BLOCKED_SOURCE_SCOPE",
            "identity_gaps": [{k: v if k == "quantity" else _explain_text(v) for k, v in gap.items()}
                              for gap in comp["identity_gaps"]],
            "sources": [{"url": _explain_url(s["url"]), "observed_at": _explain_text(s["observed_at"]),
                         "status": "cache_metadata_not_page_revalidated"} for s in comp["sources"]],
            "blockers": comp["blockers"],
            "next_evidence": {p: [{"code": code, "required": NEXT_IDENTITY_EVIDENCE[code]}
                                  for code in comp["blockers"][p]] for p in ("in_person", "live")},
            "inspect_command": f"python -m pokemind meta public-identity-explain --as-of {as_of} "
                               f"--selector {_explain_text(comp['selectors'][0])} --json"})
    matrix = []
    for item in raw["identity_matrix"]:
        matches = [(c, g) for c in selected for g in c["identity_gaps"]
                   if (g["name"], g["code"], g["number"]) == (item["name"], item["code"], item["number"])]
        if not matches:
            continue
        matrix.append({k: _explain_text(item[k]) for k in ("name", "code", "number", "reason")})
        matrix[-1].update(identity="unknown", rows=len(matches), copies=sum(g["quantity"] for _, g in matches),
            selectors=sorted({_explain_text(s) for c, _ in matches for s in c["selectors"]}),
            set_context={k: [_explain_text(s) for s in item["set_context"][k]]
                         for k in ("native_sets", "alias_sets")},
            candidates=[{**{k: _explain_text(c[k]) for k in ("tcgdex_id", "set_id", "local_id", "language", "name")},
                         "source_url": _explain_url(c["source_url"]), "retrieved_at": _explain_text(c["retrieved_at"]),
                         "status": "descriptive_candidate_not_confirmed_identity"} for c in item["catalog_candidates"]],
            next_evidence=("Désambiguïser les éditions du code avec une preuve publique directe."
                           if item["reason"] == "SET_CODE_ALIAS_AMBIGUOUS" else
                           "Prouver l’identité exacte et l’équivalence des noms sans les supposer."))
    return {"schema_version": 1, "model": "public-identity-explain-v1", "as_of": as_of,
        "status": "PARTIAL_WITH_EVIDENCE", "source_status": "SOURCE_UNREVALIDATED",
        "source_validation": "BLOCKED_SOURCE_SCOPE", "legality": "unknown", "selector": selector,
        "totals": {"placements": raw["placements"], "compositions": len(raw["compositions"]),
                   **{k: raw[k] for k in ("unique_listed_identities", "unique_resolved_identities",
                       "resolved_rows", "row_denominator", "resolved_copies", "copy_denominator")}},
        "selected_totals": {"placements": sum(len(c["selectors"]) for c in selected),
                            "compositions": len(selected),
                            **{k: sum(c["coverage"][k] for c in selected) for k in (
                                "resolved_rows", "row_denominator", "resolved_copies", "copy_denominator")}},
        "compositions": compositions, "identity_matrix": matrix,
        "normative": {p: {"active_verified_assertions": len(raw["normative"][p]["active_verified_assertions"]),
                          "rotation_status": "available_in_cache" if raw["normative"][p]["rotation_proven"] else "unknown",
                          "printing_live_availability": "unknown"} for p in ("in_person", "live")},
        "exact_sqlite_files_unchanged": raw["exact_sqlite_files_unchanged"], "network_used": False,
        "owner_database_opened": False, "full_legality_preflight_executed": False,
        "concurrent_writer_exclusion": "not_proven", "release_status": "NOT_RELEASE_READY"}


def human_identity_explain(report: dict) -> None:
    print(f"Preuves PUBLIC au {report['as_of']} — SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE")
    total, selected = report["totals"], report["selected_totals"]
    print(f"Cache : {total['placements']} placements / {total['compositions']} compositions; "
          f"identités listées de catalogue {total['unique_resolved_identities']}/{total['unique_listed_identities']}.")
    print(f"Vue : {selected['compositions']} compositions; lignes {selected['resolved_rows']}/{selected['row_denominator']}; "
          f"copies {selected['resolved_copies']}/{selected['copy_denominator']}.")
    print("Listes non revalidées; candidats descriptifs, légalité et disponibilité Live inconnues.")
    for comp in report["compositions"]:
        coverage = comp["coverage"]
        print(f"\nComposition {', '.join(comp['selectors'])} — lignes {coverage['resolved_rows']}/"
              f"{coverage['row_denominator']}; copies {coverage['resolved_copies']}/{coverage['copy_denominator']}.")
        for gap in comp["identity_gaps"]:
            print(f"  Identité inconnue : {gap['quantity']} × {gap['name']} {gap['code']} {gap['number']} ({gap['reason']}).")
        for platform in ("in_person", "live"):
            print(f"  {platform} : unknown; blocages : {', '.join(comp['blockers'][platform])}.")
            for proof in comp["next_evidence"][platform]:
                print(f"    Prochaine preuve : {proof['required']}")
        for source in comp["sources"]:
            print(f"  Source cache non revalidée : {source['url'] or 'URL non affichée'}; observée {source['observed_at']}.")
        print(f"  Relire : {comp['inspect_command']}")
    for gap in report["identity_matrix"]:
        print(f"\n{gap['name']} {gap['code']} {gap['number']} : identité unknown; {gap['rows']} lignes / {gap['copies']} copies.")
        editions = sorted(set(gap["set_context"]["native_sets"] + gap["set_context"]["alias_sets"]))
        print(f"  Éditions candidates de ce code : {', '.join(editions) or 'inconnues'}; identité non confirmée.")
        for candidate in gap["candidates"]:
            print(f"  Candidat descriptif, identité non confirmée : {candidate['name']} / {candidate['tcgdex_id']} "
                  f"({candidate['language']}); {candidate['source_url'] or 'URL non affichée'}; {candidate['retrieved_at']}.")
        print(f"  Prochaine preuve : {gap['next_evidence']}")
    print("\nV1 NOT_RELEASE_READY. Lecture seule; aucune certification des règles externes ni exclusion d’écrivain concurrent.")


def html_identity_explain(report: dict | None = None, *, error: dict | None = None) -> str:
    """Render the same safe projection, without I/O, executable markup or remote links.

    Every cache-derived value is a text node. Fragment IDs and attributes belong
    to this renderer only; URLs remain descriptive text, never href/src values.
    Build the entire document before stdout, so an error cannot leave half a page.
    """
    def text(value) -> str:
        return escape(_explain_text(value), quote=True)

    def table(caption, headings, rows) -> str:
        # Cells supplied by callers contain either escaped text or a fixed,
        # generated fragment link. Never pass cache text as HTML.
        head = "".join(f'<th scope="col">{text(h)}</th>' for h in headings)
        body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
        return (f'<div class="table-scroll" role="region" aria-label="{text(caption)}" tabindex="0">'
                f'<table><caption>{text(caption)}</caption><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table></div>')

    def source(value) -> str:
        return text(_explain_url(value) or "URL non affichée")

    page = ['<!doctype html><html lang="fr-CA"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'style-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">',
        '<title>PokeMind — preuves PUBLIC non revalidées</title>',
        '<style>'
        ':root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f5f4f0;color:#232c30;'
        'font:1rem/1.6 system-ui,sans-serif}header,main,footer{max-width:76rem;margin:auto;padding:1.5rem}'
        'header{padding-top:2.5rem}h1{font-size:clamp(1.8rem,4vw,2.7rem);line-height:1.15;max-width:24ch}'
        'h2{margin-top:2rem;line-height:1.3}h3{line-height:1.4}a{color:#125268;text-underline-offset:.2em}'
        'a:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid #125268;outline-offset:4px}'
        '.notice{padding:1rem 1.25rem;border:2px solid #806018;background:#fff4ce;border-radius:.4rem}'
        '.notice p{margin:.4rem 0}.eyebrow{letter-spacing:.1em;font-size:.8rem;font-weight:700}'
        '.muted{color:#4a575d}.table-scroll{overflow-x:auto;margin:1.2rem 0}'
        'table{border-collapse:collapse;width:100%;background:#fff}caption{text-align:left;font-weight:700;padding:.5rem 0}'
        'th,td{text-align:left;vertical-align:top;border-bottom:1px solid #c6cdce;padding:.7rem}'
        'thead{background:#e6eceb}td,li,p,summary,code{overflow-wrap:anywhere}'
        'nav ul{display:flex;flex-wrap:wrap;gap:.6rem 1.4rem;padding-left:1.3rem}'
        'article{margin:1rem 0;padding:1.2rem;border:1px solid #bcc8c8;border-radius:.5rem;background:#fff}'
        'summary{cursor:pointer;font-weight:700;padding:.5rem 0}details[open]>summary{margin-bottom:.6rem}'
        'code{font-family:ui-monospace,monospace}.skip{position:absolute;left:-10000px}.skip:focus{left:1rem;top:1rem}'
        'footer{border-top:1px solid #bcc8c8}.platform{border-left:3px solid #9baead;padding-left:1rem}'
        '@media(max-width:40rem){header,main,footer{padding:1rem}th,td{padding:.5rem}article{padding:.8rem}}'
        '@media(forced-colors:active){.notice,article,th,td{border-color:CanvasText}}'
        '@media print{details{break-inside:avoid}.skip{display:none}}'
        '</style></head><body id="top">',
        '<a class="skip" href="#main">Aller au rapport</a>',
        '<header><p class="eyebrow">POKEMIND · PREUVES PUBLIC</p>'
        '<h1>Ce que le cache permet d’observer</h1>'
        '<div class="notice"><p><strong>SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE</strong></p>'
        '<p>Listes non revalidées. Légalité Standard : <strong>in_person = unknown · live = unknown</strong>.</p>'
        '<p>Les candidats du catalogue ne prouvent pas une identité. Aucune certification de légalité.</p></div></header>',
        '<main id="main" tabindex="-1">']
    if error is not None:
        page.append('<section aria-labelledby="error"><h2 id="error">Lecture arrêtée</h2>'
                    f'<p>BLOCKED_WITH_REASON [{text(error["error_code"])}]</p><p>{text(error["error"])}</p>'
                    '<p>Aucun contenu disponible dans cette vue; aucune source supplémentaire recherchée.</p></section>')
    elif report is not None:
        total, selected = report["totals"], report["selected_totals"]
        page.append(f'<p>Évaluation au <strong>{text(report["as_of"])}</strong>. '
                    f'Sélection : <strong>{text(report["selector"] or "toutes les compositions")}</strong>.</p>')
        page.append('<section aria-labelledby="overview"><h2 id="overview">Couverture observée</h2>')
        page.append(table("Cache complet et vue sélectionnée", ["Portée", "Placements", "Compositions", "Lignes résolues / total", "Copies résolues / total"],
            [[text(label), text(t["placements"]), text(t["compositions"]),
              text(f'{t["resolved_rows"]}/{t["row_denominator"]}'),
              text(f'{t["resolved_copies"]}/{t["copy_denominator"]}')]
             for label, t in (("Cache complet", total), ("Vue sélectionnée", selected))]))
        page.append(f'<p>Identités listées uniques résolues selon le catalogue (cache complet) : '
                    f'{text(total["unique_resolved_identities"])}/{text(total["unique_listed_identities"])}. '
                    'Cette couverture ne prouve ni la provenance ni la légalité.</p></section>')
        page.append('<nav aria-label="Compositions de cette vue"><h2>Aller à une composition</h2><ul>')
        for index, comp in enumerate(report["compositions"], 1):
            for selector in comp["selectors"]:
                page.append(f'<li><a href="#composition-{index}">{text(selector)}</a></li>')
        page.append('</ul></nav><section aria-labelledby="compositions"><h2 id="compositions">Compositions</h2>')
        page.append(table("Couverture et légalité par composition", ["Sélecteurs", "Lignes résolues / total", "Copies résolues / total", "in_person", "live"],
            [[f'<a href="#composition-{index}">{text(", ".join(comp["selectors"]))}</a>',
              text(f'{comp["coverage"]["resolved_rows"]}/{comp["coverage"]["row_denominator"]}'),
              text(f'{comp["coverage"]["resolved_copies"]}/{comp["coverage"]["copy_denominator"]}'),
              "unknown", "unknown"] for index, comp in enumerate(report["compositions"], 1)]))
        if not report["compositions"]:
            page.append('<p>Aucune composition à afficher. La provenance reste non revalidée et la légalité unknown.</p>')
        for index, comp in enumerate(report["compositions"], 1):
            page.append(f'<article id="composition-{index}"><h3>Composition {text(", ".join(comp["selectors"]))}</h3>'
                        '<p>SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE · in_person : unknown · live : unknown</p>'
                        '<details><summary>Consulter les identités, sources et prochaines preuves</summary>'
                        '<h4>Identités inconnues de cette composition</h4><ul>')
            for gap in comp["identity_gaps"]:
                page.append(f'<li>{text(gap["quantity"])} × {text(gap["name"])} {text(gap["code"])} '
                            f'{text(gap["number"])} — {text(gap["reason"])}</li>')
            page.append('</ul><h4>Sources datées du cache — non revalidées</h4><ul>')
            for entry in comp["sources"]:
                page.append(f'<li>{source(entry["url"])}; observée : {text(entry["observed_at"])}. '
                            'SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE.</li>')
            page.append('</ul>')
            for platform, label in (("in_person", "Présentiel — in_person"), ("live", "Pokémon TCG Live — live")):
                page.append(f'<section class="platform"><h4>{label} : unknown</h4><p>Blocages :</p><ul>')
                page.extend(f'<li>{text(code)}</li>' for code in comp["blockers"][platform])
                page.append('</ul><p>Prochaines preuves nécessaires :</p><ul>')
                page.extend(f'<li><strong>{text(proof["code"])}</strong> : {text(proof["required"])}</li>'
                            for proof in comp["next_evidence"][platform])
                page.append('</ul></section>')
            page.append(f'<p>Consulter en JSON à la main : <code>{text(comp["inspect_command"])}</code></p>'
                        '</details><p><a href="#top">Retour au début</a></p></article>')
        page.append('</section><section aria-labelledby="identities"><h2 id="identities">Matrice des identités inconnues</h2>'
                    f'<p>{text(len(report["identity_matrix"]))} identités inconnues dans la vue sélectionnée. '
                    'Candidats descriptifs seulement; aucune édition choisie automatiquement.</p>')
        for gap in report["identity_matrix"]:
            page.append(f'<details><summary>{text(gap["name"])} {text(gap["code"])} {text(gap["number"])} — identité unknown</summary>'
                        f'<p>{text(gap["reason"])}; {text(gap["rows"])} lignes / {text(gap["copies"])} copies. '
                        f'Sélecteurs : {text(", ".join(gap["selectors"]))}.</p>'
                        f'<p>Éditions natives candidates : {text(", ".join(gap["set_context"]["native_sets"]) or "inconnues")}. '
                        f'Éditions d’alias candidates : {text(", ".join(gap["set_context"]["alias_sets"]) or "inconnues")}.</p><ul>')
            for candidate in gap["candidates"]:
                page.append(f'<li>Candidat descriptif, identité non confirmée : {text(candidate["name"])} / '
                            f'{text(candidate["tcgdex_id"])}; édition {text(candidate["set_id"])}, '
                            f'numéro {text(candidate["local_id"])}, langue {text(candidate["language"])}; '
                            f'{source(candidate["source_url"])}; observé : {text(candidate["retrieved_at"])}.</li>')
            page.append(f'</ul><p>Prochaine preuve : {text(gap["next_evidence"])}</p></details>')
        page.append('</section>')
    else:
        page.append('<h2>Aucun contenu disponible</h2><p>Provenance non revalidée; légalité unknown.</p>')
    page.append('</main><footer><p><strong>V1 NOT_RELEASE_READY</strong>. Rapport statique hors ligne; '
                'sources mentionnées comme texte seulement. Aucun accès réseau ni écriture de rapport. '
                'Aucune certification des règles externes ni exclusion d’écrivain concurrent.</p></footer></body></html>')
    return "\n".join(page)


def identity_explain_error(exc: Exception) -> dict:
    messages = {
        "PUBLIC_IDENTITY_DATE_REQUIRED": "La date doit être au format YYYY-MM-DD.",
        "PUBLIC_IDENTITY_SELECTOR_INVALID": "Le sélecteur doit être au format événement:rang.",
        "PUBLIC_IDENTITY_SELECTOR_UNKNOWN": "Composition inconnue dans les deux caches fixes.",
        "SCOPED_SOURCE_CHANGED": "Cache modifié pendant la lecture; résultat abandonné.",
        "SCOPED_SQLITE_NOT_STANDALONE": "Format SQLite non admissible sans accès à des fichiers supplémentaires.",
        "SCOPED_REDIRECTION_BLOCKED": "Redirection de chemin refusée.",
        "SCOPED_FILE_UNSAFE": "Fichier PUBLIC non admissible à cette lecture.",
    }
    code = str(exc)
    if isinstance(exc, FileNotFoundError):
        code, message = "PUBLIC_IDENTITY_CACHE_MISSING", "Un des deux caches fixes est absent; aucun remplacement recherché."
    elif code in messages:
        message = messages[code]
    else:
        code, message = "PUBLIC_IDENTITY_EXPLAIN_BLOCKED", "Lecture PUBLIC arrêtée; aucune source supplémentaire consultée."
    return {"error_code": code, "error": message, "source_validation": "BLOCKED_SOURCE_SCOPE"}


def _reference_schema(db: Path) -> None:
    required = {
        "catalog_sets": {"tcgdex_id", "tcg_online_code"},
        "catalog_printings": {"tcgdex_id", "set_id", "local_id", "regulation_mark", "category", "stage",
                               "brief_source_url", "brief_retrieved_at"},
        "catalog_translations": {"printing_id", "status", "language", "name", "source_url", "retrieved_at",
                                 "category", "energy_type", "description", "effect", "abilities_json", "attacks_json"},
        "official_rule_sources": {"source_id", "title", "url", "consulted_at", "published_date",
                                  "validation_status", "effective_from", "effective_to"},
        "official_rule_assertions": {"assertion_id", "source_id", "subject_id", "assertion_kind", "payload_json",
                                     "format", "platform", "effective_from", "effective_to", "validation_status"},
        "official_deck_structure_rules": {"rule_id", "source_id", "payload_json", "format", "platform",
                                        "effective_from", "effective_to", "validation_status"},
    }
    connection = connect_readonly(db)
    try:
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 6 or any(
            not columns.issubset({row[1] for row in connection.execute(f"PRAGMA table_info({table})")})
            for table, columns in required.items()
        ):
            raise ValueError("PUBLIC_PREFLIGHT_REFERENCE_SCHEMA_MISSING_NO_MIGRATION")
    finally:
        connection.close()


def _printing_evidence(connection, printing_id: str, *, format: str, platform: str, as_of: str) -> dict:
    printing = dict(connection.execute(
        "SELECT tcgdex_id,set_id,local_id,regulation_mark,category,stage,brief_source_url,brief_retrieved_at "
        "FROM catalog_printings WHERE tcgdex_id=?", (printing_id,)).fetchone())
    texts = [dict(row) for row in connection.execute(
        "SELECT language,name,category,energy_type,description,effect,abilities_json,attacks_json,source_url,retrieved_at "
        "FROM catalog_translations WHERE printing_id=? AND status='present' ORDER BY language", (printing_id,))]
    rows = connection.execute(
        """SELECT a.*, s.title,s.url,s.published_date,s.consulted_at,
                  s.validation_status AS source_validation_status,
                  s.effective_from AS source_effective_from,s.effective_to AS source_effective_to
           FROM official_rule_assertions a JOIN official_rule_sources s USING(source_id)
           WHERE (a.subject_id=? OR a.subject_id IS NULL)
             AND (a.format=? OR a.format IS NULL) AND (a.platform=? OR a.platform IS NULL)
           ORDER BY a.assertion_id""", (printing_id, format, platform)).fetchall()
    assertions = [{"assertion_id": row["assertion_id"], "kind": row["assertion_kind"],
                   "subject_id": row["subject_id"], "effective_from": row["effective_from"],
                   "effective_to": row["effective_to"], "payload": json.loads(row["payload_json"]),
                   "source": rules._source_refs([row])[0]}
                  for row in rows if rules._active(row, as_of) and rules._source_active(row, as_of)
                  and row["validation_status"] == row["source_validation_status"] == "verified"
                  and (not row["published_date"] or row["published_date"] <= as_of)]
    return {"printing": printing, "catalog_texts": texts, "official_assertions": assertions,
            "text_status": "cached_catalog_text_not_complete_errata_certification",
            "errata_coverage": "unknown", "catalog_time_scope": "cached_observation_not_historical_identity_proof"}


def competitive_preflight(
    root: Path, db: Path, reference_db: Path, *, as_of: str, format: str, platform: str,
    selectors: list[str] | None = None, options: int = 4, use_set_aliases: bool = False,
    source_scope: str = "verified_public_cache",
) -> dict:
    """No default paths, DB imports, migrations, cache writes, or provider calls."""
    if source_scope == "two_sqlite_only":
        # The existing source verifier needs markers, ledger and pages. Refuse
        # BEFORE any path inspection; cached metadata cannot grant permission.
        raise ValueError("BLOCKED_SOURCE_SCOPE")
    if source_scope != "verified_public_cache":
        raise ValueError("PUBLIC_PREFLIGHT_SOURCE_SCOPE_INVALID")
    competitive._advisor_context(as_of)
    if format != "standard" or platform not in {"in_person", "live"}:
        raise ValueError("PUBLIC_PREFLIGHT_STANDARD_AND_PLATFORM_REQUIRED")
    if type(options) is not int or not 2 <= options <= 4:
        raise ValueError("PUBLIC_PREFLIGHT_OPTIONS_2_TO_4")
    if selectors is not None and (not 1 <= len(selectors) <= 4 or len(set(selectors)) != len(selectors)):
        raise ValueError("PUBLIC_PREFLIGHT_DISTINCT_SELECTORS_1_TO_4")
    # Check BOTH lexical namespaces before inspecting either file.
    public_database_path(root, db)
    public_database_path(root, reference_db)
    for path, role in ((db, "COMPETITIVE"), (reference_db, "REFERENCE")):
        require_public_database(root, path)
        if not path.is_file():
            raise ValueError(f"PUBLIC_PREFLIGHT_{role}_CACHE_MISSING_NO_DOWNLOAD")
    _reference_schema(reference_db)
    if selectors is None:
        shortlist = competitive.competitive_shortlist(root, db, as_of=as_of, options=options)
        selectors = [option["export_selector"] for option in shortlist["options"]]
    groups, events, issues, placements = competitive._advisor_snapshot(root, db, as_of)
    selected = [competitive._select_group(groups, selector) for selector in selectors]
    if len({group["composition_id"] for group in selected}) != len(selected):
        raise ValueError("PUBLIC_PREFLIGHT_DUPLICATE_COMPOSITION")
    result = []
    connection = connect_readonly(reference_db)
    try:
        from pokemind.set_code_aliases import build_aliases
        bridge = build_aliases(connection, as_of=as_of) if use_set_aliases else None
        for selector, group in zip(selectors, selected):
            entries = [{"ordinal": index, "quantity": card["quantity"], "card_name": card["name"],
                        "set_code": card["set"], "collector_number": card["number"], "card_type": card["type"]}
                       for index, card in enumerate(group["cards"].values(), 1)]
            report = rules.check_deck_entries(reference_db, entries, total_cards=60, exact_confirmed=True,
                                              format=format, platform=platform, as_of=as_of, set_aliases=bridge)
            for entry, card in zip(entries, report["cards"]):
                card["identity_status"] = ("resolved" if len(card["tcgdex_ids"]) == 1 else
                                           "ambiguous" if card["tcgdex_ids"] or
                                           card["structure_identity"]["resolution_reason"] == "SET_CODE_ALIAS_AMBIGUOUS"
                                           else "unresolved")
                card["catalog_evidence"] = None
                if card["identity_status"] != "resolved":
                    reason = card["structure_identity"]["resolution_reason"]
                    card["verdict"]["reason_codes"].append(reason)
                    card["verdict"]["missing_data"].append(reason.lower())
                if card["identity_status"] == "resolved":
                    evidence = _printing_evidence(connection, card["tcgdex_ids"][0],
                                                  format=format, platform=platform, as_of=as_of)
                    card["catalog_evidence"] = evidence
                    categories = {rules._normalized_name(value) for value in (
                        evidence["printing"]["category"], *(t["category"] for t in evidence["catalog_texts"])) if value}
                    if categories != {entry["card_type"]}:
                        card["verdict"].update(status="unknown", confidence="low",
                                              reason_codes=["CATALOG_CATEGORY_MISSING_OR_CONFLICTING"],
                                              missing_data=["consistent_catalog_category"])
            status_counts = Counter(card["verdict"]["status"] for card in report["cards"])
            if report["structure_validation"]["status"] == "not_legal" or status_counts["not_legal"]:
                report["status"] = "not_legal"
            elif report["structure_validation"]["status"] == "legal" and status_counts["unknown"] == 0:
                report["status"] = "legal"
            else:
                report["status"] = "unknown"
            if status_counts["unknown"] and "DECK_CARD_LEGALITY_UNKNOWN" not in report["reason_codes"]:
                report["reason_codes"].append("DECK_CARD_LEGALITY_UNKNOWN")
            identity_counts = Counter(card["identity_status"] for card in report["cards"])
            identity_reasons = Counter(card["structure_identity"]["resolution_reason"] for card in report["cards"])
            missing = Counter(reason for card in report["cards"] for reason in card["verdict"]["missing_data"])
            blockers = sorted(set([reason for reason in report["reason_codes"] if reason != "DECK_STRUCTURE_FULLY_VERIFIED"]
                                  + report["structure_validation"]["unverified_rules"]
                                  + [reason for card in report["cards"] if card["verdict"]["status"] != "legal"
                                     for reason in card["verdict"]["reason_codes"]]))
            result.append({**report, "selector": selector, "source": competitive._group_public(group, detail=False),
                           "list_observations": group["occurrences"],
                           "counts": {"identity_denominator": len(entries), "copy_denominator": 60,
                                      "identity": {key: identity_counts[key] for key in ("resolved", "ambiguous", "unresolved")},
                                      "identity_reasons": dict(sorted(identity_reasons.items())),
                                      "printing_legality": {key: status_counts[key] for key in STATES},
                                      "copy_legality": {key: sum(card["quantity"] for card in report["cards"]
                                                                 if card["verdict"]["status"] == key) for key in STATES}},
                           "missing_evidence_counts": dict(sorted(missing.items())), "blockers": blockers,
                           "next_evidence": blockers + ["PRINTING_SPECIFIC_LIVE_AVAILABILITY", "OWNER_COLLECTION_IF_REQUESTED"],
                           "export": {"command": "meta competitive-export", "selector": selector,
                                      "format": "PTCGL", "writes": False},
                           "readiness_status": "not_legal" if report["status"] == "not_legal" else "unknown",
                           "live_availability": "unknown", "ownership": "unknown", "credits": "unknown",
                           "craftability": "unknown", "matchups": "unknown"})
    finally:
        connection.close()
    return {"as_of": as_of, "format": format, "platform": platform,
            "status": "PARTIAL_WITH_EVIDENCE" if issues or any(
                option["status"] == "unknown" or option["readiness_status"] == "unknown" for option in result) else "OK",
            "options": result, "deck_status_counts": {key: sum(o["status"] == key for o in result) for key in STATES},
            "sampled_placements": placements, "distinct_compositions": len(groups), "events": len(events),
            "issues": issues, "read_only": True, "network_used": False, "database_mutated": False,
            "owner_database_opened": False, "scope": "offline_public_deck_legality_evidence",
            "set_code_bridge": ({"version": bridge["version"], "sha256": bridge["sha256"],
                                 "as_of": as_of} if bridge else None),
            "limits": ["Tournament publication is not proof of printing legality or Live availability.",
                       "Regulatory legality is separate from Live availability, ownership and import readiness.",
                       "Synthetic CI does not certify a real printing or the PC cache.",
                       "V1 NOT_RELEASE_READY"]}


def human_preflight(report: dict) -> None:
    print(f"Prévol PUBLIC Standard/{report['platform']} au {report['as_of']} : {report['status']}")
    for option in report["options"]:
        counts = option["counts"]
        copies = counts["copy_legality"]
        print(f"{option['selector']} ({', '.join(option['source']['archetypes'])}) : {option['status']}; "
              f"{option['quantity_sum']}/60 cartes; structure={option['structure_validation']['status']}; "
              f"impressions résolues={counts['identity']['resolved']}/{counts['identity_denominator']}.")
        print(f"  Copies legal/not_legal/unknown : {copies['legal']}/{copies['not_legal']}/{copies['unknown']}; "
              "Live/possession/crédits/fabrication : unknown.")
        print("  Preuves manquantes/raisons : " + (", ".join(option["blockers"]) or "aucune réglementaire"))
        print("  Source : " + ", ".join(option["source"]["source_urls"]) +
              f"; export existant : meta competitive-export --event {option['selector'].split(':')[0]} "
              f"--placement {option['selector'].split(':')[1]} (même --db PUBLIC).")
    print("Détails par impression, dates et sources : --json. V1 NOT_RELEASE_READY.")
