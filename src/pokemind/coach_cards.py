"""Card lookup for the coach: current TCG printings first, compact and dated.

The public catalog also holds TCG Pocket and every historical printing. Ranking
by text relevance alone answered "Dracaufeu" with 2003-2014 cards, so the coach
could not build a current deck. This view drops Pocket, ranks printings by
presumed Standard status then release date, and carries the set code and number
that a TCG Live export needs.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from pokemind import rules
from pokemind.database import connect_readonly

# Words of a request that never name a card ("crée-moi un deck puissant avec ...").
STOPWORDS = frozenset("""
avec ajoute ajouter aussi build card cards carte cartes contre cree creer construis construire deck decks
donne donner dans des est fais faire fort forte inclus inclut inclure jeu joue jouer liste meilleur
meilleure mes moi mon oublie pas plus pour propose proposer puissant puissante quel quelle sans suis
une veux the and with best strong francais french english anglais pokemon standard live tcg format
""".split())
NOT_TOURNAMENT_SERIES = {"tcgp", "mc"}  # TCG Pocket, McDonald's collections
MARKS_INTRODUCED = "2020-02-01"  # Sword & Shield; older unmarked printings rotated long ago
# Short words that still tell two cards apart ("Méga-Dracaufeu X-ex" vs "Y-ex").
SHORT_NOISE = frozenset("ex de du la le les un et en je tu il au a".split())
_RANK = {"presumed_legal": 0, "unknown": 1, "presumed_not_legal": 2}
# Main expansions import cleanly in TCG Live; promos and special collections come after.
MAIN_SET = re.compile(r"^(?:me|sv|swsh|sm|xy)\d+(?:\.\d+)?$")
_INDEX: dict[tuple, list] = {}
_BY_ID: dict[str, dict] = {}


def normalize(text: str | None) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "").casefold()
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def tokens(query: str) -> list[str]:
    words = re.findall(r"\w+", normalize(query))
    return list(dict.fromkeys(w for w in words if len(w) >= 3 and w not in STOPWORDS))[:8]


def short_tokens(query: str) -> list[str]:
    return [w for w in dict.fromkeys(re.findall(r"\w+", normalize(query))) if len(w) < 3 and w not in SHORT_NOISE]


def _index(db_path: Path) -> list:
    info = db_path.stat()
    key = (str(db_path), info.st_mtime_ns, info.st_size)
    if key not in _INDEX:
        connection = connect_readonly(db_path)
        try:
            rows = connection.execute(
                """SELECT p.tcgdex_id, p.set_id, p.local_id, p.category, p.stage, p.hp, p.regulation_mark,
                          s.series_id, s.release_date, s.name_fr AS set_fr, s.name_en AS set_en,
                          COALESCE(s.abbreviation_official, s.tcg_online_code) AS code,
                          fr.name AS name_fr, en.name AS name_en, en.energy_type
                   FROM catalog_printings p JOIN catalog_sets s ON s.tcgdex_id=p.set_id
                   LEFT JOIN catalog_translations fr ON fr.printing_id=p.tcgdex_id AND fr.language='fr'
                   LEFT JOIN catalog_translations en ON en.printing_id=p.tcgdex_id AND en.language='en'
                   WHERE s.series_id IS NULL OR s.series_id != 'tcgp'""").fetchall()
        finally:
            connection.close()
        _INDEX.clear()
        _INDEX[key] = [(dict(row), set(re.findall(r"\w+", normalize(f"{row['name_fr']} {row['name_en']}"))))
                       for row in rows]
        _BY_ID.clear()
        _BY_ID.update((row["tcgdex_id"], row) for row, _ in _INDEX[key])
    return _INDEX[key]


def presume(row: dict[str, Any], rotation: dict[str, Any] | None) -> dict[str, Any]:
    if row.get("series_id") in NOT_TOURNAMENT_SERIES:
        return {"status": "unknown", "confidence": "low", "reason": "COLLECTION_NOT_TOURNAMENT_PLAY"}
    if not row.get("regulation_mark") and rotation is not None:
        if row.get("category") == "energy" and row.get("energy_type") == "Normal":  # TCGdex: basic energy
            return {"status": "presumed_legal", "confidence": "medium", "reason": "BASIC_ENERGY"}
        if (row.get("release_date") or "9999") < MARKS_INTRODUCED:
            return {"status": "presumed_not_legal", "confidence": "medium", "reason": "PRINTED_BEFORE_REGULATION_MARKS"}
    return rules.presume_mark(row.get("regulation_mark"), rotation)


def presume_printing(db_path: Path, tcgdex_id: str, *, as_of: str, platform: str = "live",
                     strict: dict[str, Any] | None = None) -> dict[str, Any]:
    """An explicit official verdict wins; otherwise the dated presumption."""
    if strict and strict.get("status") in {"legal", "not_legal"}:
        return {"status": strict["status"], "confidence": strict.get("confidence", "high"), "reason": "OFFICIAL_VERDICT"}
    _index(db_path)
    row = _BY_ID.get(tcgdex_id)
    if row is None:
        return {"status": "unknown", "confidence": "low", "reason": "PRINTING_NOT_IN_TCG_CATALOG"}
    rotation = rules.latest_verified_rotation(db_path, format="standard", platform=platform, as_of=as_of)
    return presume(row, rotation)


def playable_printing(db_path: Path, name_en: str, *, as_of: str, platform: str = "live") -> str | None:
    """Export line of a presumed-legal printing with the same English name.

    Same name is not proof of functional identity; callers label it a lead.
    """
    rotation = rules.latest_verified_rotation(db_path, format="standard", platform=platform, as_of=as_of)
    wanted = normalize(name_en)
    rows = [row for row, _ in _index(db_path) if row["name_en"] and normalize(row["name_en"]) == wanted
            and row["code"] and presume(row, rotation)["status"] == "presumed_legal"]
    if not rows:
        return None
    best = max(rows, key=lambda r: (r["release_date"] or "", r["tcgdex_id"]))
    return f"{best['name_en']} {best['code']} {best['local_id']}"


def find_cards(db_path: Path, query: str, *, as_of: str, platform: str = "live", limit: int = 12) -> dict[str, Any]:
    wanted, short = tokens(query), short_tokens(query)
    result: dict[str, Any] = {"query": query[:200], "as_of": as_of, "platform": platform, "cards": []}
    if not wanted:
        result["hint"] = "Donne le nom de la carte (français ou anglais)."
        return result
    rotation = rules.latest_verified_rotation(db_path, format="standard", platform=platform, as_of=as_of)
    scored = []
    for row, words in _index(db_path):
        hits = sum(1 for token in wanted if token in words)
        if hits:
            scored.append((hits, row, sum(1 for token in short if token in words)))
    if not scored:
        result["hint"] = "Aucun nom de carte trouvé; vérifie l'orthographe ou essaie le nom anglais."
        return result
    best = max(hits for hits, _, _ in scored)
    rows = [dict(row, presumed=presume(row, rotation), detail=extra) for hits, row, extra in scored if hits == best]
    exact = normalize(query).strip()
    for r in rows:
        r["exact"] = exact in {normalize(r["name_fr"]), normalize(r["name_en"])}
    # A playable exact name first, then playable printings, then the rest.
    rows.sort(key=lambda r: (-r["detail"], not (r["exact"] and r["presumed"]["status"] == "presumed_legal"),
                             _RANK[r["presumed"]["status"]], not r["exact"], not MAIN_SET.match(r["set_id"]),
                             -int((r["release_date"] or "0").replace("-", "") or 0), r["tcgdex_id"]))
    result["matches"] = len(rows)
    result["standard_basis"] = rules.presume_mark("?", rotation)["basis"] if rotation else "Aucune rotation officielle vérifiée."
    result["cards"] = [{
        "tcgdex_id": r["tcgdex_id"], "nom": r["name_fr"] or r["name_en"], "name_en": r["name_en"],
        "extension": r["set_fr"] or r["set_en"], "code": r["code"], "numero": r["local_id"],
        "sortie": r["release_date"], "marque": r["regulation_mark"], "categorie": r["category"],
        "stade": r["stage"], "pv": r["hp"], "standard": r["presumed"]["status"],
        **({"export": f"{r['name_en']} {r['code']} {r['local_id']}"} if r["code"] and r["name_en"] else {}),
    } for r in rows[:limit]]
    return result
