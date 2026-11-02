"""Read a deliberately small DATA grammar, never execute TypeScript/JavaScript.

Only imports, one typed object declaration and its default export are accepted.
Values are literals/containers or references to declared imports. Calls, property
access, interpolation, spread, additional statements and executable syntax fail.
"""
from __future__ import annotations

import math
import posixpath
import re
from dataclasses import dataclass

from pokemind.cards import CatalogError


@dataclass(frozen=True)
class Reference:
    name: str


@dataclass
class LiteralModule:
    kind: str
    value: dict
    imports: dict[str, str]


class Reader:
    def __init__(self, text):
        if not isinstance(text, str) or len(text.encode("utf-8")) > 131_072:
            raise CatalogError("LITERAL_SOURCE_SIZE_INVALID")
        self.text, self.offset, self.count = text, 0, 0
        self.token = self.next_token()

    def string(self):
        quote = self.text[self.offset]
        self.offset += 1
        result = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
        while self.offset < len(self.text):
            char = self.text[self.offset]
            self.offset += 1
            if char == quote:
                value = "".join(result)
                try:
                    return value.encode("utf-16", "surrogatepass").decode("utf-16")
                except UnicodeError as exc:
                    raise CatalogError("LITERAL_STRING_UNICODE_INVALID") from exc
            if quote == "`" and char == "$" and self.text[self.offset:self.offset + 1] == "{":
                raise CatalogError("LITERAL_INTERPOLATION_REJECTED")
            if char in "\r\n" and quote != "`":
                raise CatalogError("LITERAL_STRING_NEWLINE_REJECTED")
            if char != "\\":
                result.append(char)
                continue
            if self.offset >= len(self.text):
                break
            escape = self.text[self.offset]
            self.offset += 1
            if escape in "\\\"'`/":
                result.append(escape)
            elif escape in escapes:
                if escape == "0" and self.text[self.offset:self.offset + 1].isdigit():
                    raise CatalogError("LITERAL_OCTAL_REJECTED")
                result.append(escapes[escape])
            elif escape in "\r\n":
                if escape == "\r" and self.text[self.offset:self.offset + 1] == "\n":
                    self.offset += 1
            elif escape in {"x", "u"}:
                size = 2 if escape == "x" else 4
                if escape == "u" and self.text[self.offset:self.offset + 1] == "{":
                    end = self.text.find("}", self.offset + 1)
                    value = self.text[self.offset + 1:end] if end >= 0 else ""
                    if not re.fullmatch(r"[0-9a-fA-F]{1,6}", value):
                        raise CatalogError("LITERAL_ESCAPE_REJECTED")
                    self.offset = end + 1
                else:
                    value = self.text[self.offset:self.offset + size]
                    if not re.fullmatch(r"[0-9a-fA-F]{" + str(size) + "}", value):
                        raise CatalogError("LITERAL_ESCAPE_REJECTED")
                    self.offset += size
                codepoint = int(value, 16)
                if codepoint > 0x10FFFF:
                    raise CatalogError("LITERAL_ESCAPE_REJECTED")
                result.append(chr(codepoint))
            else:
                # JS identity escapes (e.g. \é) preserve the following character.
                if escape.isdigit():
                    raise CatalogError("LITERAL_OCTAL_REJECTED")
                result.append(escape)
        raise CatalogError("LITERAL_UNTERMINATED_STRING")

    def next_token(self):
        self.count += 1
        if self.count > 50_000:
            raise CatalogError("LITERAL_TOKEN_CAP")
        text = self.text
        while self.offset < len(text):
            if text[self.offset].isspace() or text[self.offset] == "\ufeff":
                self.offset += 1
            elif text.startswith("//", self.offset):
                end = text.find("\n", self.offset)
                self.offset = len(text) if end < 0 else end + 1
            elif text.startswith("/*", self.offset):
                end = text.find("*/", self.offset + 2)
                if end < 0:
                    raise CatalogError("LITERAL_UNTERMINATED_COMMENT")
                self.offset = end + 2
            else:
                break
        if self.offset == len(text):
            return ("eof", "")
        char = text[self.offset]
        if char in "\"'`":
            return ("string", self.string())
        match = re.match(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", text[self.offset:])
        if match:
            if len(match[0]) > 40:
                raise CatalogError("LITERAL_NUMBER_CAP")
            self.offset += len(match[0])
            number = float(match[0]) if any(c in match[0] for c in ".eE") else int(match[0])
            if not math.isfinite(number):
                raise CatalogError("LITERAL_NON_FINITE_REJECTED")
            return ("number", number)
        match = re.match(r"[A-Za-z_$][A-Za-z0-9_$]*", text[self.offset:])
        if match:
            self.offset += len(match[0])
            return ("word", match[0])
        if char in "{}[]:,;=+":
            self.offset += 1
            return (char, char)
        raise CatalogError("LITERAL_EXECUTABLE_SYNTAX_REJECTED")

    def take(self, kind, value=None):
        token = self.token
        if token[0] != kind or value is not None and token[1] != value:
            raise CatalogError("LITERAL_GRAMMAR_REJECTED")
        self.token = self.next_token()
        return token[1]

    def optional(self, kind, value=None):
        if self.token[0] == kind and (value is None or self.token[1] == value):
            self.take(kind, value)
            return True
        return False

    def value(self, imports, depth=0):
        if depth > 32:
            raise CatalogError("LITERAL_DEPTH_CAP")
        kind, value = self.token
        if kind == "string":
            value = self.take("string")
            # Exactly two upstream data files join adjacent constant strings.
            # Only string+string is folded; no expressions, coercion or calls.
            while self.optional("+"):
                value += self.take("string")
                if len(value) > 32_000:
                    raise CatalogError("LITERAL_STRING_CAP")
            return value
        if kind == "number":
            return self.take(kind)
        if self.optional("{"):
            result = {}
            while self.token[0] != "}":
                if self.token[0] not in {"word", "string", "number"}:
                    raise CatalogError("LITERAL_KEY_REJECTED")
                key = str(self.take(self.token[0]))
                if key in result or key in {"__proto__", "prototype", "constructor"}:
                    raise CatalogError("LITERAL_DUPLICATE_OR_UNSAFE_KEY")
                self.take(":")
                result[key] = self.value(imports, depth + 1)
                if not self.optional(","):
                    break
            self.take("}")
            return result
        if self.optional("["):
            result = []
            while self.token[0] != "]":
                result.append(self.value(imports, depth + 1))
                if not self.optional(","):
                    break
            self.take("]")
            return result
        if kind == "word":
            self.take("word")
            if value in {"true", "false", "null", "undefined"}:
                return {"true": True, "false": False, "null": None, "undefined": None}[value]
            if value in imports:
                return Reference(value)
        raise CatalogError("LITERAL_NON_DATA_VALUE_REJECTED")


def read_module(text):
    reader = Reader(text)
    imports = {}
    while reader.optional("word", "import"):
        reader.optional("word", "type")
        if reader.optional("{"):
            names = [reader.take("word")]
            while reader.optional(","):
                if reader.token[0] == "}":
                    break
                names.append(reader.take("word"))
            reader.take("}")
            reader.take("word", "from")
            path = reader.take("string")
            if set(names) - {"Card", "Set", "Serie"} or not path.endswith("interfaces"):
                raise CatalogError("LITERAL_TYPE_IMPORT_REJECTED")
        else:
            name = reader.take("word")
            reader.take("word", "from")
            path = reader.take("string")
            if name in imports or not path.startswith(".") or "\\" in path or ":" in path:
                raise CatalogError("LITERAL_REFERENCE_IMPORT_REJECTED")
            imports[name] = path
        reader.optional(";")
    reader.take("word", "const")
    binding = reader.take("word")
    reader.take(":")
    kind = reader.take("word")
    if kind not in {"Card", "Set", "Serie"}:
        raise CatalogError("LITERAL_DECLARATION_TYPE_REJECTED")
    reader.take("=")
    value = reader.value(imports)
    if not isinstance(value, dict):
        raise CatalogError("LITERAL_DECLARATION_NOT_OBJECT")
    reader.optional(";")
    reader.take("word", "export")
    reader.take("word", "default")
    reader.take("word", binding)
    reader.optional(";")
    if reader.token[0] != "eof":
        raise CatalogError("LITERAL_ADDITIONAL_STATEMENT_REJECTED")
    return LiteralModule(kind, value, imports)


def reference_path(module_path, import_path):
    path = posixpath.normpath(posixpath.join(posixpath.dirname(module_path), import_path))
    if not path.startswith("data/") or "\\" in path or ":" in path:
        raise CatalogError("LITERAL_REFERENCE_OUTSIDE_DATA")
    return path if path.endswith(".ts") else path + ".ts"
