"""Lecture déterministe des volumes Markdown fournis."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
DATE_RE = re.compile(
    r"\b(\d{1,2})\s+"
    r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"
    r"\s+(\d{4})\b",
    re.IGNORECASE,
)
MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}


@dataclass(frozen=True, slots=True)
class MarkdownSection:
    ordinal: int
    heading: str
    heading_path: str
    heading_level: int
    start_line: int
    end_line: int
    char_start: int
    char_end: int
    content: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    title: str
    source_date: str | None
    content_sha256: str
    text: str
    sections: tuple[MarkdownSection, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_date(text: str) -> str | None:
    match = DATE_RE.search(text[:2_000])
    if not match:
        return None
    day, month_name, year = match.groups()
    return date(int(year), MONTHS[month_name.casefold()], int(day)).isoformat()


def parse_markdown(text: str, *, raw_bytes: bytes | None = None) -> MarkdownDocument:
    """Découpe à chaque titre ATX et conserve des positions reproductibles."""
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    headings: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.rstrip("\r\n"))
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    if not headings:
        raise ValueError("Document Markdown sans titre ATX")

    segments: list[tuple[int, int, int, str]] = []
    first_line = headings[0][0]
    if first_line:
        segments.append((0, first_line, 0, "Préambule"))
    for position, (line_index, level, heading) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        segments.append((line_index, end, level, heading))

    stack: list[str] = []
    sections: list[MarkdownSection] = []
    for ordinal, (start, end, level, heading) in enumerate(segments, start=1):
        if level:
            stack = stack[: level - 1]
            while len(stack) < level - 1:
                stack.append("(niveau omis)")
            stack.append(heading)
            body_start = start + 1
            heading_path = " > ".join(stack)
        else:
            body_start = start
            heading_path = heading
        raw_segment = "".join(lines[start:end])
        content = "".join(lines[body_start:end]).strip()
        sections.append(
            MarkdownSection(
                ordinal=ordinal,
                heading=heading,
                heading_path=heading_path,
                heading_level=level,
                start_line=start + 1,
                end_line=max(start + 1, end),
                char_start=offsets[start],
                char_end=offsets[end],
                content=content,
                content_sha256=_sha256(raw_segment.encode("utf-8")),
            )
        )

    title = headings[0][2]
    source_bytes = raw_bytes if raw_bytes is not None else text.encode("utf-8")
    return MarkdownDocument(
        title=title,
        source_date=_source_date(text),
        content_sha256=_sha256(source_bytes),
        text=text,
        sections=tuple(sections),
    )


def read_markdown(path: Path) -> MarkdownDocument:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig", errors="strict")
    return parse_markdown(text, raw_bytes=raw)
