"""A narrow data reader, not eval, JS execution or an upstream script loader."""
import pytest

from pokemind.cards import CatalogError
from pokemind.literal_dataset import Reference, read_module, reference_path


def module(body, after=""):
    return "import { Card } from '../../../interfaces'\nimport Set from '../Synthetic'\nconst card: Card = " + body + ";export default card;" + after


def test_literals_unicode_escapes_comments_and_references_are_data():
    result = read_module(module(r'''{name:{en:"Synthetic // data",fr:'Fictif\u00e9'},
        // allowed comment, no commands
        set:Set, hp:100, variants:[true,false,null,], text:"a\n" + 'b',
        quote:"\uD83D\uDE00", absent:undefined, negative:-2.5}'''))
    assert result.kind == "Card" and result.value["set"] == Reference("Set")
    assert result.value["name"]["fr"] == "Fictifé"
    assert result.value["text"] == "a\nb" and result.value["quote"] == "😀"
    assert result.value["variants"] == [True, False, None]
    assert result.value["negative"] == -2.5 and result.value["absent"] is None
    assert reference_path("data/Series/Set/1.ts", result.imports["Set"]) == "data/Series/Synthetic.ts"


@pytest.mark.parametrize("body", [
    "{name: process.env}", "{name: fetch('https://example.invalid')}",
    "{...Set}", "{name: `data ${process.env}`}", "{name: (()=>1)()}",
    "{name: 'text' + Set}", "{hp: 1 + 2}", "{hp: Infinity}",
    "{__proto__: {name:'bad'}}", "{name:'one',name:'two'}", "{hp: 1e999}",
    r"{name:'\077'}", "{name: new Date()}",
])
def test_executable_or_ambiguous_grammar_is_rejected(body):
    with pytest.raises(CatalogError):
        read_module(module(body))


def test_trailing_statements_and_import_escape_are_rejected():
    with pytest.raises(CatalogError):
        read_module(module("{name:'data'}", "console.log('must not execute')"))
    with pytest.raises(CatalogError, match="OUTSIDE_DATA"):
        reference_path("data/Series/Set.ts", "../../../private")


def test_depth_and_size_are_bounded():
    with pytest.raises(CatalogError, match="DEPTH_CAP"):
        read_module(module("{name:" + "[" * 40 + "1" + "]" * 40 + "}"))
    with pytest.raises(CatalogError, match="SIZE_INVALID"):
        read_module(module("{name:'" + "x" * 140_000 + "'}"))
