"""Release QA cannot select an ordinary project or an aliased marker."""
import importlib.util
import os
import shutil
from pathlib import Path
import uuid

import pytest

from pokemind.desktop.app import synthetic_release_root


def make_marker(root):
    selected = root / 'build' / ('synthetic-release-' + uuid.uuid4().hex)
    selected.mkdir(parents=True)
    marker = selected / '.orchestrator/SYNTHETIC_QA_ONLY'
    marker.parent.mkdir()
    marker.write_bytes(b'POKEMIND_SYNTHETIC_RELEASE_QA_V1\n')
    return selected, marker


def test_release_qa_rejects_ordinary_root_before_opening_any_data(local_tmp, monkeypatch):
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('no file read outside a marked fixture'))
    with pytest.raises(ValueError, match='SYNTHETIC_RELEASE_ROOT_REQUIRED'):
        synthetic_release_root(local_tmp)


def test_release_qa_requires_exact_marker_and_rejects_file_alias(local_tmp):
    selected, marker = make_marker(local_tmp)
    assert synthetic_release_root(selected) == selected
    marker.write_bytes(b'not a synthetic fixture')
    with pytest.raises(ValueError, match='SYNTHETIC_RELEASE_MARKER_REQUIRED'):
        synthetic_release_root(selected)
    marker.write_bytes(b'POKEMIND_SYNTHETIC_RELEASE_QA_V1\n')
    os.link(marker, selected / 'marker-alias')
    with pytest.raises(ValueError, match='SYNTHETIC_RELEASE_MARKER_REQUIRED'):
        synthetic_release_root(selected)


def test_qa_public_memory_uses_invented_responses_and_keeps_unknown(local_tmp):
    pytest.importorskip('PySide6')
    path = Path(__file__).parents[1] / 'scripts/qa_unified_desktop.py'
    spec = importlib.util.spec_from_file_location('release_qa_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Use the actual dedicated-build layout. Nesting another build tree under
    # test-runs exceeds legacy Windows path limits for indexed source pages.
    repo = Path(__file__).parents[1].absolute()
    fixture = module.prepare_release(repo)
    try:
        opener = module.InventedOfficialOpener()
        from pokemind.batch_public_research import research
        from datetime import date
        options = {'as_of':date.today().isoformat(), 'topic':'rules', 'opener':opener}
        receipt = research(fixture, **options)
        calls = opener.calls
        assert receipt['persisted'] and len(receipt['facts']) == 2 and calls == 3
        assert all(f['validation'] == 'unverified' and f['legality'] == 'unknown' for f in receipt['facts'])
        reopened = research(fixture, **options, offline=True)
        assert reopened['gets'] == 0 and opener.calls == calls and len(reopened['facts']) == 2
    finally:
        from pokemind.battle_batch import safe_path
        from pokemind.synthetic_qa import optional
        context = optional()
        checked = safe_path(repo, fixture)
        assert checked.parent == (context.root if context else repo) / 'build' and checked.name.startswith('synthetic-release-')
        if context is None:
            shutil.rmtree(checked)


@pytest.mark.parametrize('provider_text', ["Rien n'a été mémorisé.",
    "Je n’ai pas enregistré de nouvelles données.", 'Nothing was saved.'])
def test_release_memory_gate_rejects_model_denial_even_with_a_positive_receipt(provider_text):
    pytest.importorskip('PySide6')
    path = Path(__file__).parents[1] / 'scripts/qa_unified_desktop.py'
    spec = importlib.util.spec_from_file_location('release_qa_gate', path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    receipt = {'status':'SAVED','persisted':True,'added':2,'updated':0,
        'already_known':0,'unverified':2,'facts':[]}
    record = module.public_memory_record(receipt)
    canonical = module.public_memory_message(record)
    message = {'role':'assistant','content':canonical,'memory_receipt':record}
    assert module.memory_consistency_gate(receipt,message,canonical,dict(message),'Résultat reçu par PokeMind.')
    assert not module.memory_consistency_gate(receipt,message,canonical,dict(message),provider_text)
    old = {'role':'assistant','content':provider_text+'\n2 faits ajoutés'}
    assert not module.memory_consistency_gate(receipt,old,old['content'],dict(old))
    assert not module.memory_consistency_gate(receipt,message,canonical,old)


def test_release_usefulness_gate_rejects_a_perfect_receipt_only_answer():
    pytest.importorskip('PySide6')
    path=Path(__file__).parents[1]/'scripts/qa_unified_desktop.py'
    spec=importlib.util.spec_from_file_location('release_qa_usefulness',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    receipt={'status':'SAVED','persisted':True,'added':2,'updated':0,'already_known':0,'unverified':2,'facts':[]}
    record=module.public_memory_record(receipt)
    old={'content':module.public_memory_message(record),'memory_receipt':record}
    question='Cherche les règles puis explique leurs implications'
    assert module.memory_consistency_gate(receipt,old,old['content'],dict(old))
    assert not module.research_answer_gate(receipt,question,old,old['content'],dict(old))
    message=old | {'content':module.public_research_message(receipt,question)}
    assert module.research_answer_gate(receipt,question,message,message['content'],dict(message))
    assert not module.research_answer_gate(receipt,question,message,old['content'],dict(message))
    assert not module.research_answer_gate(receipt,question,message,message['content'],old)


def test_source_depth_gate_rejects_metadata_only_even_when_receipt_and_usefulness_pass(local_tmp):
    pytest.importorskip('PySide6')
    from datetime import date
    from pokemind.batch_public_research import research
    from test_public_source_depth import POLICY, URL
    path=Path(__file__).parents[1]/'scripts/qa_unified_desktop.py'
    spec=importlib.util.spec_from_file_location('source_depth_qa',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    receipt=research(local_tmp,as_of=date.today().isoformat(),topic='rules',opener=module.InventedOfficialOpener(),
        official_policy={URL:POLICY,
            'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources':POLICY})
    message={'content':module.public_research_message(receipt,'règles')}
    assert module.source_depth_gate(receipt,message,message['content'],dict(message))
    for f in receipt['facts']:
        f.pop('rule_evidence',None)
    old={'content':module.public_research_message(receipt,'règles')}
    assert not module.source_depth_gate(receipt,old,old['content'],dict(old))
