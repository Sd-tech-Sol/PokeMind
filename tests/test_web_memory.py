"""Local web memory: the coach looks here first and saves what a web search found (owner, 2026-11-03)."""
from __future__ import annotations

import pytest

from pokemind import web_memory
from pokemind.assistant import tools

pytest.importorskip('PySide6')
from pokemind.desktop.services import Services  # noqa: E402

SUMMARY = 'Règle inventée du 2031-05-01 : la Carte Imaginaire est limitée à une copie par deck.'
SOURCE = 'https://www.pokemon.com/invented-rule-page'


def test_remember_then_search_returns_the_note_with_its_date_and_sources(local_tmp):
    assert web_memory.search(local_tmp, 'Carte Imaginaire') == {
        'status': 'NONE', 'notes': [], 'source': 'PokeMind · mémoire web locale'}
    assert not (local_tmp / web_memory.DB).exists()  # a search never creates the database
    saved = web_memory.remember(local_tmp, 'Limite Carte Imaginaire', SUMMARY, SOURCE + ' http://plain.invalid/x',
                                as_of='2031-05-02')
    assert saved['status'] == 'SAVED' and saved['sources'] == [SOURCE]  # https only
    found = web_memory.search(local_tmp, 'combien de copies de la carte imaginaire?', as_of='2031-05-12')
    assert found['status'] == 'FOUND' and found['notes'][0]['summary'] == SUMMARY
    assert found['notes'][0]['retrieved'] == '2031-05-02' and found['notes'][0]['age_days'] == 10
    assert found['notes'][0]['sources'] == [SOURCE] and 'vérifier la date' in found['note']
    assert web_memory.search(local_tmp, 'Dragon inventé sans rapport')['status'] == 'NONE'


def test_same_topic_is_refreshed_not_duplicated(local_tmp):
    web_memory.remember(local_tmp, 'Limite Carte Imaginaire', SUMMARY, SOURCE, as_of='2031-05-02')
    again = web_memory.remember(local_tmp, 'limite carte  IMAGINAIRE', SUMMARY, SOURCE, as_of='2031-05-03')
    assert again['status'] == 'ALREADY_KNOWN'
    newer = SUMMARY.replace('une copie', 'deux copies')
    assert web_memory.remember(local_tmp, 'Limite Carte Imaginaire', newer, SOURCE, as_of='2031-06-01')['status'] == 'UPDATED'
    notes = web_memory.search(local_tmp, 'Carte Imaginaire', as_of='2031-06-01')['notes']
    assert len(notes) == 1 and 'deux copies' in notes[0]['summary'] and notes[0]['retrieved'] == '2031-06-01'


@pytest.mark.parametrize('topic,summary,sources,error', [
    ('', SUMMARY, SOURCE, 'WEB_MEMORY_TOPIC_INVALID'),
    ('Sujet inventé', 'trop court', SOURCE, 'WEB_MEMORY_SUMMARY_INVALID'),
    ('Sujet inventé', SUMMARY, 'http://plain.invalid/x https://user:secret@example.invalid/', 'WEB_MEMORY_SOURCES_REQUIRED'),
])
def test_invalid_notes_are_refused_without_writing(local_tmp, topic, summary, sources, error):
    assert web_memory.remember(local_tmp, topic, summary, sources)['error'] == error
    assert not (local_tmp / web_memory.DB).exists()


def test_coach_tools_save_and_find_and_the_next_question_gets_the_note_first(local_tmp):
    assert {'web_memory', 'remember_web'} <= set(tools.OPERATIONS)
    properties = tools.TOOL['inputSchema']['properties']
    assert properties['summary']['maxLength'] == 4000 and properties['sources']['type'] == 'string'
    services = Services(local_tmp)
    saved = services.tool_call({'operation': 'remember_web', 'query': 'Limite Carte Imaginaire',
                                'summary': SUMMARY, 'sources': SOURCE})
    assert saved['status'] == 'SAVED'
    assert services.tool_call({'operation': 'web_memory', 'query': 'Carte Imaginaire'})['notes'][0]['summary'] == SUMMARY
    assert services.tool_call({'operation': 'remember_web', 'query': 'x' * 10, 'summary': 's' * 4001})['error'] == (
        'POKEMIND_TOOL_ARGUMENTS_INVALID')
    context = services.prepare_question('Combien de copies de la Carte Imaginaire?', 'public')
    assert context['web_memory']['notes'][0]['sources'] == [SOURCE]
    assert 'web_memory' not in services.prepare_question('Question inventée sans rapport aucun', 'public')
