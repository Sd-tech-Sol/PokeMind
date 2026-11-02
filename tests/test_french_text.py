"""Synthetic wiki data only: exact printing and safe French field extraction."""
import pytest

from pokemind.cards import CatalogError
from pokemind.french_text import article_parameters, extract_fields, number, plain


def target():
    return {"set_id": "syn", "local_id": "001", "set_en": "Synthetic", "set_fr": "Fictif",
        "en_name": "Synthetic Flame", "fr_name": None, "lookup_name_fr": "Flamme fictive",
        "known_french_names": ["Flamme fictive"],
        "missing": ["name", "description", "attacks.0.name", "attacks.0.effect", "abilities.0.name", "abilities.0.effect"]}


EN = {"name": "Synthetic Flame", "hp": 70, "description": "Synthetic English description.",
      "attacks": [{"name": "Strike", "damage": "20+", "cost": ["Fire", "Colorless"], "effect": "Flip a coin."}],
      "abilities": [{"name": "Synthetic Power", "effect": "Draw a card."}]}
WIKI = """{{Article carte
| nom=Synthetic Flame
| nom-trad=Flamme fictive
| extension=Synthetic
| numerocarte=1
| pv=70
| description=Synthetic English description.
| description-trad=Une description française fictive.
| attaque-nom=Strike
| attaque-nom-trad=Frappe
| attaque-type={{type|feu|jcc}}{{type|incolore|jcc}}
| attaque-dégâts=20+
| attaque-description-trad=Lancez une [[Jeton (JCC)|pièce]].<ref>Une référence.</ref>
| poké-power-nom=Synthetic Power
| poké-power-nom-trad=Pouvoir fictif
| poké-power-description-trad=Piochez une carte.
}}"""


def test_published_translation_preserves_provenance_and_cleans_markup():
    fields = extract_fields(WIKI, target(), EN, {})
    assert len(fields) == 6
    assert fields["attacks.0.effect"]["value"] == "Lancez une pièce."
    assert fields["name"]["text_kind"] == "published_community_translation"
    assert not fields["name"]["official_text_verified"]
    assert fields["abilities.0.effect"]["wiki_parameter"] == "poké-power-description-trad"


@pytest.mark.parametrize("before,after,code", [("extension=Synthetic", "extension=Other", "SET_MISMATCH"),
    ("numerocarte=1", "numerocarte=2", "NUMBER_MISMATCH"),
    ("nom=Synthetic Flame", "nom=Other", "NAME_MISMATCH"),
    ("pv=70", "pv=80", "HP_MISMATCH")])
def test_wrong_printing_cannot_supply_a_translation(before, after, code):
    text = WIKI.replace(before, after)
    if code == "NAME_MISMATCH":
        text = text.replace("nom-trad=Flamme fictive", "nom-trad=Autre")
    with pytest.raises(CatalogError, match=code):
        extract_fields(text, target(), EN, {})


def test_ambiguous_attack_signature_is_not_an_ordinal_guess():
    en = {**EN, "attacks": [EN["attacks"][0], {**EN["attacks"][0], "name": "Other"}]}
    fields = extract_fields(WIKI.replace("attaque-nom=Strike", "attaque-nom=Unknown"), target(), en, {})
    assert "attacks.0.name" not in fields
    assert "attacks.0.effect" not in fields


def test_missing_published_translation_does_not_fall_back_to_english():
    text = WIKI.replace("| description-trad=Une description française fictive.\n", "")
    assert "description" not in extract_fields(text, target(), EN, {})
    text = WIKI.replace("-trad", "-unused").replace("nom=Synthetic Flame", "nom=Flamme fictive")
    assert "description" not in extract_fields(text, target(), EN, {})


def test_unknown_template_or_unsafe_markup_is_never_executed_or_silently_removed():
    with pytest.raises(CatalogError):
        plain("Une valeur {{#invoke:external|execute}}")
    assert plain("<script>execute()</script>") is None
    assert plain("Une {{type|feu|jcc}} visible.") == "Une Feu visible."


def test_nested_pipes_comments_and_duplicate_parameter_guard():
    fields = article_parameters(WIKI)
    assert "[[Jeton (JCC)|pièce]]" in fields["attaque-description-trad"]
    with pytest.raises(CatalogError, match="DUPLICATE"):
        article_parameters(WIKI.replace("| pv=70", "| pv=70\n| pv=71"))
    with pytest.raises(CatalogError, match="UNBALANCED"):
        article_parameters(WIKI[:-2])


def test_promotional_prefix_is_scoped_to_its_actual_set():
    assert number("SM01", "smp") == number("01", "smp")
    assert number("SM01", "syn") != number("01", "syn")
    assert number("TG01", "syn") != number("01", "syn")


def test_published_trainer_effect_and_static_query_label_do_not_execute_queries():
    text = """{{Article carte|nom=Objet fictif|nomen=Synthetic Item|extension=Fictif|numerocarte=1|
    catégorie=Dresseur|faculté-description=Piochez {{Requête JCC|[[Nom::Fictif]]|texte=une carte|jeu=JCC}}.|}}"""
    expected = {**target(), "en_name":"Synthetic Item", "missing":["effect"], "local_id":"1"}
    fields = extract_fields(text,expected,{"effect":"Draw a card."},{})
    assert fields["effect"]["value"] == "Piochez une carte."
    assert fields["effect"]["wiki_parameter"] == "faculté-description"


def test_suffix_icon_and_reference_pipes_are_static_published_formatting():
    assert plain("Nom{{Symbole JCC|ex JCCP}}") == "Nom ex"
    assert plain("Nom{{Symbole JCC|EX|small}}") == "Nom EX"
    assert article_parameters("{{Article carte|nom=Fictif<ref>|bogus=other</ref>|numerocarte=1|}}") == {
        "nom":"Fictif","numerocarte":"1"}


def test_declared_suffix_can_qualify_a_name_but_is_never_dropped_to_force_a_match():
    text = WIKI.replace("nom=Synthetic Flame", "nom=Synthetic Flame{{Symbole JCC|EX}}")
    text = text.replace("nom-trad=Flamme fictive", "nom-trad=Flamme fictive{{Symbole JCC|EX}}")
    assert extract_fields(text,target(),{**EN,"suffix":"EX"},{})["name"]["value"] == "Flamme fictive EX"
    with pytest.raises(CatalogError,match="NAME_MISMATCH"):
        extract_fields(text,target(),EN,{})


def test_free_effect_only_attack_uses_a_unique_structural_signature():
    text = """{{Article carte|nom=Flamme fictive|nomen=Synthetic Flame|extension=Fictif|numerocarte=1|pv=70
    |attaque-nom=Repère fictif|attaque-type={{type|gratuite|jcc}}|attaque-description=Piochez une carte.}}"""
    en={**EN,"attacks":[{"name":"Synthetic action","effect":"Draw a card.","cost":["Free"]}]}
    fields=extract_fields(text,target(),en,{})
    assert fields["attacks.0.name"]["value"] == "Repère fictif"
    assert fields["attacks.0.effect"]["value"] == "Piochez une carte."


def test_unused_positional_content_is_ignored_as_data_not_instructions():
    fields=article_parameters("{{Article carte|ignored content|nom=Fictif|numerocarte=1}}")
    assert fields == {"nom":"Fictif","numerocarte":"1"}


def test_unique_original_attack_name_precedes_a_coincidental_numeric_signature():
    en = {**EN,"attacks":[EN["attacks"][0],{**EN["attacks"][0],"name":"Other"}]}
    assert extract_fields(WIKI,target(),en,{})["attacks.0.name"]["value"] == "Frappe"


def test_unknown_original_cost_cannot_be_assumed_to_be_free():
    text = """{{Article carte|nom=Flamme fictive|nomen=Synthetic Flame|extension=Fictif|numerocarte=1|pv=70
    |attaque-nom=Repère fictif|attaque-type={{type|gratuite|jcc}}|attaque-description=Piochez une carte.}}"""
    en={**EN,"attacks":[{"name":"Unknown action","effect":"Draw a card."}]}
    fields=extract_fields(text,target(),en,{})
    assert "attacks.0.name" not in fields and "attacks.0.effect" not in fields
