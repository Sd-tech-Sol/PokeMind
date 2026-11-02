from __future__ import annotations

from pathlib import Path

from pokemind.markdown import parse_markdown, read_markdown
from pokemind.paths import SEED_FILES


ROOT = Path(__file__).resolve().parents[1]


def test_reads_all_seed_markdown_as_utf8_with_provenance() -> None:
    for filename in SEED_FILES:
        document = read_markdown(ROOT / "source_material" / "markdown" / filename)
        assert document.title.startswith("VOLUME")
        assert document.source_date == "2026-10-09"
        assert len(document.sections) >= 10
        assert len(document.content_sha256) == 64
        assert "Pokémon" in document.text
        for section in document.sections:
            assert section.start_line <= section.end_line
            assert section.char_start < section.char_end
            assert len(section.content_sha256) == 64


def test_semantic_heading_hierarchy_and_positions() -> None:
    text = "# Titre\n\nPréface.\n\n## Section\nTexte accentué.\n\n### Sous-section\nSuite.\n"
    document = parse_markdown(text)
    assert [section.heading for section in document.sections] == ["Titre", "Section", "Sous-section"]
    assert document.sections[-1].heading_path == "Titre > Section > Sous-section"
    assert document.sections[-1].start_line == 8
    assert document.sections[-1].end_line == 9
    assert document.sections[-1].content == "Suite."


def test_rejects_markdown_without_headings() -> None:
    try:
        parse_markdown("texte seulement")
    except ValueError as exc:
        assert "sans titre" in str(exc)
    else:
        raise AssertionError("Le Markdown sans structure aurait dû être refusé")
