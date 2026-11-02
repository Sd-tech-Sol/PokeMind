"""Pinned, operator-reviewed PUBLIC text snapshot; no network or TS execution."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from pokemind.cards import (CatalogError, _identifier, _bounded_text, _optional_int,
                            _normalize_category, _json_list, _set_record, _validated_card_detail)
from pokemind.literal_dataset import Reference, read_module, reference_path
from pokemind.recovery import _redirected


def _source_file(path, maximum):
    if (any(_redirected(p) for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_nlink != 1 or not 0 < path.stat().st_size <= maximum):
        raise CatalogError("SNAPSHOT_SOURCE_FILE_REJECTED")
    return path


class Snapshot:
    def __init__(self, root, source):
        root, source = root.absolute(), source.absolute()
        if (source.parent != root / "data/local" or not re.fullmatch(r"catalog-discovery-[a-z0-9-]{1,40}", source.name)
                or any(_redirected(p) for p in (source, *source.parents))):
            raise CatalogError("SNAPSHOT_PUBLIC_SOURCE_REQUIRED")
        marker = json.loads(_source_file(source / "PUBLIC_SOURCE_ONLY.json", 4096).read_text(encoding="utf-8"))
        if (marker.get("schema_version") != 1 or marker.get("kind") != "tcgdex_pinned_public_dataset"
                or marker.get("repository") != "tcgdex/cards-database"
                or not re.fullmatch(r"[0-9a-f]{40}", str(marker.get("commit", "")))
                or not re.fullmatch(r"[0-9a-f]{64}", str(marker.get("tree_sha256", "")))):
            raise CatalogError("SNAPSHOT_ORIGIN_REVIEW_REQUIRED")
        self.commit, self.tree_sha256 = marker["commit"], marker["tree_sha256"]
        tree_body = _source_file(source / "tree.json", 16 * 1024 * 1024).read_bytes()
        if hashlib.sha256(tree_body).hexdigest() != self.tree_sha256:
            raise CatalogError("SNAPSHOT_TREE_HASH_MISMATCH")
        tree = json.loads(tree_body)
        if tree.get("truncated") is not False or not isinstance(tree.get("tree"), list):
            raise CatalogError("SNAPSHOT_TREE_INCOMPLETE")
        expected = {}
        for item in tree["tree"]:
            path = item.get("path", "")
            if item.get("type") == "blob" and (
                    path.startswith("data/") and path.endswith(".ts")
                    or path in {"LICENSE", "meta/translations/fr.json"}):
                if (path in expected or item.get("mode") != "100644"
                        or not 0 < item.get("size", 0) <= 131_072
                        or PurePosixPath(path).is_absolute()
                        or any(p in {".", ".."} or "\\" in p or ":" in p for p in PurePosixPath(path).parts)):
                    raise CatalogError("SNAPSHOT_TREE_ENTRY_REJECTED")
                expected[path] = item
        if not expected or len(expected) > 50_000 or sum(v["size"] for v in expected.values()) > 64 * 1024 * 1024:
            raise CatalogError("SNAPSHOT_SOURCE_VOLUME_REJECTED")
        self.modules, self.blobs, self.references = {}, {}, {}
        self.translations, self.license = None, None
        seen = set()
        dataset = _source_file(source / "literal-source.jsonl", 192 * 1024 * 1024)
        with dataset.open(encoding="utf-8") as stream:
            while True:
                line = stream.readline(400_001)
                if not line:
                    break
                if len(line) > 400_000:
                    raise CatalogError("SNAPSHOT_RECORD_TOO_LARGE")
                record = json.loads(line)
                path = record.get("path")
                if path not in expected or path in seen or not isinstance(record.get("text"), str):
                    raise CatalogError("SNAPSHOT_MEMBERSHIP_MISMATCH")
                body = record["text"].encode("utf-8")
                def git_hash(value):
                    return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()
                actual = git_hash(body)
                if actual != expected[path]["sha"] and git_hash(b"\xef\xbb\xbf" + body) != expected[path]["sha"]:
                    raise CatalogError("SNAPSHOT_GIT_BLOB_MISMATCH")
                seen.add(path)
                self.blobs[path] = expected[path]["sha"]
                if path == "LICENSE":
                    self.license = record["text"]
                elif path == "meta/translations/fr.json":
                    self.translations = json.loads(record["text"])
                else:
                    module = read_module(record["text"])
                    depth = len(PurePosixPath(path).parts)
                    if module.kind != {2: "Serie", 3: "Set", 4: "Card"}.get(depth):
                        raise CatalogError("SNAPSHOT_MODULE_KIND_MISMATCH")
                    self.modules[path] = module
        if seen != set(expected) or not self.license or "MIT License" not in self.license or not isinstance(self.translations, dict):
            raise CatalogError("SNAPSHOT_SOURCE_INCOMPLETE")
        for path, module in self.modules.items():
            parents = {name: reference_path(path, target) for name, target in module.imports.items()}
            for parent in parents.values():
                if parent not in self.modules or self.modules[parent].kind != {"Card": "Set", "Set": "Serie"}.get(module.kind):
                    raise CatalogError("SNAPSHOT_REFERENCE_KIND_REJECTED")
            field = {"Card": "set", "Set": "serie"}.get(module.kind)
            if field:
                value = module.value.get(field)
                if not isinstance(value, Reference) or value.name not in parents:
                    raise CatalogError("SNAPSHOT_PARENT_REFERENCE_REQUIRED")
                self.references[path] = parents[value.name]
            module.imports = parents
        resolved, active = set(), set()
        def resolve(path):
            if path in active:
                raise CatalogError("SNAPSHOT_REFERENCE_CYCLE")
            module = self.modules[path]
            if path in resolved:
                return module.value
            active.add(path)
            def walk(value):
                if isinstance(value, Reference):
                    return resolve(module.imports[value.name])
                if isinstance(value, dict):
                    for key in value:
                        value[key] = walk(value[key])
                elif isinstance(value, list):
                    for i in range(len(value)):
                        value[i] = walk(value[i])
                return value
            walk(module.value)
            active.remove(path)
            resolved.add(path)
            return module.value
        for path in self.modules:
            resolve(path)
        self.sets, self.cards, self.card_sets = {}, {}, defaultdict(list)
        self.card_paths = defaultdict(list)
        casefold_ids = set()
        for path, module in self.modules.items():
            if module.kind == "Set":
                entity_id = _identifier(module.value.get("id"))
                if entity_id in self.sets:
                    raise CatalogError("SNAPSHOT_DUPLICATE_SET_ID")
                self.sets[entity_id] = path
            elif module.kind == "Card":
                entity_id = _identifier(str(module.value["set"].get("id")) + "-" + PurePosixPath(path).stem)
                if entity_id not in self.cards:
                    if entity_id.casefold() in casefold_ids:
                        raise CatalogError("SNAPSHOT_CASE_COLLISION")
                    casefold_ids.add(entity_id.casefold())
                    self.cards[entity_id] = path
                    self.card_sets[module.value["set"]["id"]].append(entity_id)
                self.card_paths[entity_id].append(path)
        self.source_files = len(seen)
        for entity_id in self.cards:
            for language in ("en", "fr"):
                self.path("cards", entity_id, language)  # reject conflicting locale objects

    def path(self, kind, entity_id, language):
        if kind == "sets":
            return self.sets[entity_id]
        candidates = [path for path in self.card_paths[entity_id]
                      if self.text(self.modules[path].value.get("name"), language)
                      and self.text(self.modules[path].value["set"].get("name"), language)]
        if len(candidates) > 1:
            raise CatalogError("SNAPSHOT_DUPLICATE_LOCALE_CARD")
        return candidates[0] if candidates else self.cards[entity_id]

    def url(self, path):
        return f"https://github.com/tcgdex/cards-database/blob/{self.commit}/" + quote(path, safe="/")

    @staticmethod
    def text(value, language):
        # Never substitute an English name/effect into a French translation.
        return value.get(language) if isinstance(value, dict) else None

    def enum(self, kind, value, language):
        if value is None:
            return None
        return self.translations.get(kind, {}).get(value, value) if language == "fr" else value

    def available(self, kind, entity_id, language):
        path = self.path(kind, entity_id, language)
        value = self.modules[path].value
        return bool(self.text(value.get("name"), language) and (
            kind == "sets" or self.text(value["set"].get("name"), language)))

    def set_payload(self, entity_id, language, *, brief=False):
        value = self.modules[self.sets[entity_id]].value
        name = self.text(value.get("name"), language)
        cards = [i for i in sorted(self.card_sets[entity_id]) if self.available("cards", i, language)]
        counts = value.get("cardCount", {})
        official = counts.get("official")
        if type(official) is not int or official < 0:
            raise CatalogError("SNAPSHOT_SET_COUNT_INVALID")
        result = {"id": entity_id, "name": name,
                  "cardCount": {**counts, "total": max(official, len(cards))}}
        if not brief:
            date = value.get("releaseDate")
            result.update(releaseDate=self.text(date, language) if isinstance(date, dict) else date,
                tcgOnline=value.get("tcgOnline"),
                serie={"id": value["serie"].get("id"), "name": self.text(value["serie"].get("name"), language)},
                abbreviation={"official": value.get("abbreviations", {}).get("official"),
                              "localized": self.text(value.get("abbreviations"), language)},
                cards=[{"id": i, "localId": PurePosixPath(self.cards[i]).stem,
                        "name": self.text(self.modules[self.path("cards", i, language)].value.get("name"), language)} for i in cards])
            _set_record(result)
        return result

    def card_payload(self, entity_id, language):
        path = self.path("cards", entity_id, language)
        value = self.modules[path].value
        result = {"id": entity_id, "localId": PurePosixPath(path).stem,
                  "name": self.text(value.get("name"), language),
                  "set": self.set_payload(value["set"]["id"], language, brief=True)}
        for key in ("illustrator", "hp", "regulationMark", "retreat", "level", "weight", "dexId", "cameoDexIds"):
            if key in value:
                result[key] = value[key]
        for key in ("description", "effect", "evolveFrom"):
            if key in value:
                result[key] = self.text(value[key], language)
        for key in ("category", "rarity", "stage", "suffix", "trainerType", "energyType"):
            if key in value:
                result[key] = self.enum(key, value[key], language)
        if "types" in value:
            result["types"] = [self.enum("types", t, language) for t in value["types"]]
        for key, taxonomy in (("attacks", None), ("abilities", "abilityType")):
            if key in value:
                result[key] = []
                for item in value[key]:
                    projected = {k: self.text(item[k], language) for k in ("name", "effect") if k in item}
                    for field in ("damage",):
                        if field in item:
                            projected[field] = item[field]
                    if "cost" in item:
                        projected["cost"] = [self.enum("types", t, language) for t in item["cost"]]
                    if taxonomy and "type" in item:
                        projected["type"] = self.enum(taxonomy, item["type"], language)
                    result[key].append(projected)
        for key in ("weaknesses", "resistances"):
            if key in value:
                result[key] = [{**item, "type": self.enum("types", item["type"], language)} for item in value[key]]
        if "item" in value:
            result["item"] = {k: self.text(value["item"].get(k), language) for k in ("name", "effect")}
        if "variants" in value:
            result["variants"] = value["variants"]
            if isinstance(value["variants"], list):
                result["variants_detailed"] = value["variants"]
        result["source_declared_fields"] = sorted(value)
        _validated_card_detail(result, entity_id)
        return result

    def identity(self, entity_id):
        path = self.cards[entity_id]
        value = self.modules[path].value
        return (entity_id, _identifier(value["set"]["id"]),
                _bounded_text(PurePosixPath(path).stem, "localId", required=True, maximum=80),
                _normalize_category(_bounded_text(value.get("category"), "category")),
                _optional_int(value.get("hp"), "hp"),
                _bounded_text(value.get("stage"), "stage"),
                _bounded_text(value.get("regulationMark"), "regulationMark"),
                _bounded_text(value.get("rarity"), "rarity"),
                _bounded_text(value.get("illustrator"), "illustrator"),
                _json_list(value.get("types"), "types"), self.url(path))
