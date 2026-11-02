"""Read published French card text from attributed wiki data, never execute it."""
from __future__ import annotations

import html
import re
import unicodedata

from pokemind.cards import CatalogError

LICENSE = "CC-BY-NC-SA-3.0-FR"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/3.0/fr/"
TYPES = {"plante": "Grass", "feu": "Fire", "eau": "Water", "electrique": "Lightning",
         "psy": "Psychic", "combat": "Fighting", "obscurite": "Darkness", "metal": "Metal",
         "incolore": "Colorless", "dragon": "Dragon", "fee": "Fairy", "gratuite": "Free"}


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = value.replace("♀", "female").replace("♂", "male").replace("&", "et")
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def number(value, set_id):
    value = re.sub(r"\s", "", str(value)).upper()
    prefix = {"smp": "SM", "swshp": "SWSH", "bwp": "BW", "dpp": "DP", "xyp": "XY", "hsp": "HGSS"}.get(set_id)
    if prefix and value.startswith(prefix):
        value = value[len(prefix):]
    return re.sub(r"(?<!\d)0+(?=\d)", "", value)


def normalized_set(value):
    return normalized(re.sub(r"\b(?:et|and)\b|&", "", str(value or ""), flags=re.I))


def article_parameters(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 2 * 1024 * 1024:
        raise CatalogError("FRENCH_WIKI_SOURCE_SIZE_INVALID")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<ref\b[^>]*?/>|<ref\b[^>]*>.*?</ref\s*>", "", text, flags=re.I | re.S)
    match = re.search(r"\{\{\s*Article carte\s*(?=\||\n)", text, re.I)
    if not match:
        raise CatalogError("FRENCH_WIKI_CARD_TEMPLATE_REQUIRED")
    start, i, braces, links, pieces = match.start() + 2, match.start() + 2, 1, 0, []
    while i < len(text):
        pair = text[i:i + 2]
        if pair == "[[":
            links += 1; i += 2
        elif pair == "]]":
            links -= 1; i += 2
        elif pair == "{{":
            braces += 1; i += 2
        elif pair == "}}":
            braces -= 1
            if braces == 0:
                pieces.append(text[start:i]); break
            i += 2
        elif text[i] == "|" and braces == 1 and links == 0:
            pieces.append(text[start:i]); start = i + 1; i += 1
        else:
            i += 1
        if braces > 32 or not 0 <= links <= 32:
            raise CatalogError("FRENCH_WIKI_NESTING_REJECTED")
    if braces or links:
        raise CatalogError("FRENCH_WIKI_UNBALANCED_TEMPLATE")
    result = {}
    for piece in pieces[1:]:
        if not piece.strip():
            continue
        if "=" not in piece:
            # Article carte has named data fields. An unused positional value
            # is ignored by the template; never execute or interpret its text.
            continue
        key, value = piece.split("=", 1)
        key = unicodedata.normalize("NFC", key.strip().casefold())
        if not key or key in result or len(key) > 100:
            raise CatalogError("FRENCH_WIKI_DUPLICATE_FIELD")
        result[key] = value.strip()
    return result


def plain(value):
    """Whitelist simple text formatting; unknown templates remain unavailable."""
    if not value:
        return None
    value = re.sub(r"<ref\b[^>]*?/>|<ref\b[^>]*>.*?</ref\s*>", "", value, flags=re.I | re.S)
    def template(match):
        args = [p.strip() for p in match.group(1).split("|")]
        if len(args) in {2, 3} and normalized(args[0]) == "type" and normalized(args[1]) in TYPES:
            return args[1].capitalize()
        if normalized(args[0]) == "requetejcc":
            # Display label already published in the source, no semantic query.
            labels = [arg.split("=",1)[1] for arg in args[1:] if arg.startswith("texte=")]
            if len(labels) == 1 and labels[0]:
                return labels[0]
        if normalized(args[0]) == "symbolejcc" and (len(args) == 2 or len(args) == 3 and args[2] == "small"):
            # Static textual rendering of the published suffix icon, no code.
            label = {"ex":"ex","exjccp":"ex","exmega":"ex","exteracristal":"ex","gx":"GX","v":"V",
                     "vmax":"VMAX","vstar":"VSTAR","turbo":"TURBO","vunion":"V-UNION",
                     "gl":"GL","4":"4","c":"C","fb":"FB","g":"G","m":"M","mega":"M-",
                     "legende":"LÉGENDE","legend":"LEGEND","star":"☆","etoile":"☆","prismeetoile":"◇"}.get(normalized(args[1]))
            if args[1] == "EX":
                label = "EX"
            if label:
                return " " + label
        raise CatalogError("FRENCH_WIKI_UNKNOWN_TEXT_TEMPLATE")
    for _ in range(10):
        if "{{" not in value:
            break
        changed = re.sub(r"\{\{([^{}]*)\}\}", template, value)
        if changed == value:
            return None
        value = changed
    if "{{" in value or "}}" in value:
        return None
    def link(match):
        parts = match.group(1).split("|")
        if parts[0].casefold().startswith(("fichier:", "file:", "image:", "catégorie:")):
            raise CatalogError("FRENCH_WIKI_NON_TEXT_LINK")
        return parts[-1].split("#", 1)[0]
    value = re.sub(r"\[\[([^\[\]]+)\]\]", link, value)
    value = re.sub(r"\[(?:https?://)[^\s\]]+\s+([^\]]+)\]", r"\1", value)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</?(?:small|sup|sub|span|b|i)(?:\s[^>]*)?>", "", value, flags=re.I)
    value = re.sub(r"'{2,5}", "", value)
    value = unicodedata.normalize("NFC", html.unescape(value)).strip()
    if (not value or len(value) > 20_000 or re.search(r"[<>\[\]{}]", value)
            or any(ord(c) < 32 and c not in "\n\t" for c in value)):
        return None
    return re.sub(r"[ \t]+", " ", value)


def _safe_plain(value):
    try:
        return plain(value)
    except CatalogError:
        return None


def _damage(value):
    return re.sub(r"\s", "", html.unescape(str(value if value is not None else ""))).replace("×", "x").casefold()


def _cost(value):
    values = re.findall(r"\{\{\s*type\s*\|([^|}]+)(?:\|[^}]*)?\}\}", value or "", re.I)
    if not values:
        return None
    mapped = [TYPES.get(normalized(v)) for v in values]
    if any(v is None for v in mapped):
        return None
    return sorted([] if mapped == ["Free"] else mapped)


def extract_fields(text, target, english, french):
    """Exact printing identity, then safe missing-field supplements only.

    Community translations never establish a French printing or legal text.
    Attack slot correspondence needs original name, known French name, or an
    exact unique cost+damage signature; ordinal position alone is insufficient.
    """
    p = article_parameters(text)
    expected_sets = {normalized_set(target.get(k)) for k in ("set_en", "set_fr") if target.get(k)}
    expected_sets.update(normalized_set(v) for v in target.get("wiki_set_aliases", []))
    if normalized_set(_safe_plain(p.get("extension"))) not in expected_sets:
        raise CatalogError("FRENCH_WIKI_SET_MISMATCH")
    if number(p.get("numerocarte", ""), target["set_id"]) != number(target["local_id"], target["set_id"]):
        raise CatalogError("FRENCH_WIKI_NUMBER_MISMATCH")
    expected_names = {normalized(target.get(k)) for k in ("en_name", "fr_name", "lookup_name_fr") if target.get(k)}
    expected_names.update(normalized(v) for v in target.get("known_french_names", []))
    suffix = english.get("suffix")
    if suffix in {"ex","EX","GX","V","VMAX","VSTAR"}:
        expected_names.update(normalized(str(target.get(k) or "") + " " + suffix) for k in ("en_name","fr_name") if target.get(k))
    for key in ("en_name","fr_name"):
        value = target.get(key)
        if value and re.search(r"\((?:Professor|Professeur|Professeure)\b[^()]*\)$",value):
            expected_names.add(normalized(re.sub(r"\s*\([^()]*\)$","",value)))
    names = {normalized(_safe_plain(p.get(k))) for k in ("nom", "nom-trad", "nomen", "nomformaté") if p.get(k)}
    if not expected_names.intersection(names):
        raise CatalogError("FRENCH_WIKI_NAME_MISMATCH")
    if english.get("hp") is not None and p.get("pv") and str(english["hp"]) != p["pv"].strip():
        raise CatalogError("FRENCH_WIKI_HP_MISMATCH")
    translated = any(k.endswith("-trad") for k in p)
    french_context = bool(p.get("nomen") and any(re.search(
        r"\b(?:vous|votre|adversaire|dégâts|cette|chaque|énergie|une|son|ses)\b", value, re.I)
        for key,value in p.items() if "description" in key and not key.endswith("-ref")))
    result = {}
    def take(field, key):
        if field not in target["missing"]:
            return
        key = key + "-trad" if translated else key
        value = _safe_plain(p.get(key))
        baseline = english
        for part in field.split("."):
            baseline = (baseline[int(part)] if isinstance(baseline, list) and part.isdigit()
                        and int(part) < len(baseline) else baseline.get(part) if isinstance(baseline, dict) else None)
        if not translated and value and normalized(value) == normalized(baseline):
            # No silent English fallback, including sentences whose punctuation
            # differs. Shared French names require an already attested FR alias.
            shared_name = field == "name" and value in target.get("known_french_names", [])
            shared_action = field.endswith(".name") and french_context
            if not (shared_name or shared_action):
                return
        if value:
            result[field] = {"value": value, "wiki_parameter": key,
                "text_kind": "published_community_translation" if translated else "published_french_transcription",
                "official_text_verified": False}
    take("name", "nom")
    take("description", "description")
    # Trainer/Energy templates use description as card effect rather than flavor.
    if normalized(p.get("catégorie")) in {"dresseur", "energie", "carteenergie", "supporter", "stade"}:
        keys = [key for key in ("faculté-description", "effet", "description")
                if (key + "-trad" if translated else key) in p]
        if keys:
            take("effect", keys[0])
    attacks = []
    for n in range(1, 5):
        key = "attaque" + (str(n) if n > 1 else "")
        if key + "-nom" in p or key + "-nom-trad" in p:
            attacks.append(key)
    for key in attacks:
        original = _safe_plain(p.get(key + "-nom"))
        named_matches, signature_matches = [], []
        for i, attack in enumerate(english.get("attacks", [])):
            native = french.get("attacks", [])[i] if i < len(french.get("attacks", [])) else {}
            named = (translated and original and normalized(original) == normalized(attack.get("name"))) or (
                not translated and original and native.get("name") and normalized(original) == normalized(native["name"]))
            cost, damage = _cost(p.get(key + "-type")), p.get(key + "-dégâts")
            expected_cost = sorted(v for v in attack.get("cost", []) if v != "Free")
            signature = (cost is not None and isinstance(attack.get("cost"), list) and cost == expected_cost
                         and _damage(damage) == _damage(attack.get("damage")))
            contradictory = (cost is not None and "cost" in attack and cost != expected_cost or
                             damage is not None and attack.get("damage") is not None and _damage(damage) != _damage(attack["damage"]))
            if named and not contradictory:
                named_matches.append(i)
            if signature:
                signature_matches.append(i)
        matches = named_matches if named_matches else signature_matches
        if len(matches) == 1:
            i = matches[0]
            take(f"attacks.{i}.name", key + "-nom")
            take(f"attacks.{i}.effect", key + "-description")
    abilities = []
    for stem in ("talent", "pouvoir-pokémon", "poké-power", "poké-body", "capacité-spéciale"):
        for n in range(1, 4):
            key = stem + (str(n) if n > 1 else "")
            if key + "-nom" in p or key + "-nom-trad" in p:
                abilities.append(key)
    for key in abilities:
        original = _safe_plain(p.get(key + "-nom"))
        matches = [i for i, ability in enumerate(english.get("abilities", [])) if translated and original and
                   normalized(original) == normalized(ability.get("name"))]
        if not matches:
            type_names = {"talent":{"ability"},"pouvoir-pokémon":{"pokemonpower"},
                          "poké-power":{"pokepower"},"poké-body":{"pokebody"}}
            stem = re.sub(r"[0-9]+$", "", key)
            matches = [i for i, ability in enumerate(english.get("abilities", [])) if
                       normalized(ability.get("type")) in type_names.get(stem,set())]
        if not matches and len(abilities) == len(english.get("abilities", [])) == 1:
            matches = [0]
        if len(matches) == 1:
            i = matches[0]
            take(f"abilities.{i}.name", key + "-nom")
            take(f"abilities.{i}.effect", key + "-description")
    return result
