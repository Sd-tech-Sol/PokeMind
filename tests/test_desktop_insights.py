"""Statistical honesty and UI journeys on entirely invented content."""
import copy
import json
from pathlib import Path
import pytest

pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QEvent, QTimer, QBuffer, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton
from test_desktop_qt import app, ui, wait_until
from pokemind.desktop.insights import project_statistics, recent_matches, timeline_html, favorite_key
from pokemind.desktop.theme import colors
from pokemind.desktop.card_art import ZoomImage
from pokemind.assistant.sessions import Store


def report():
    return {'coverage': {'valid': 6}, 'outcomes': {'wins': 2, 'losses': 3, 'unknown': 1},
            'groups': [{'archetype':'Invented A','wins':2,'losses':2,'unknown':0,'n':4},
                       {'archetype':'unknown','wins':0,'losses':1,'unknown':1,'n':2}],
            'matches': [dict(match='SYN-A',outcome='wins',max_observed_turn=4,battle_date='unknown',
                             opponent={'label':'Invented A'}, evidence=[{'type':'prize','turn':4,'text':'Fictif'}]),
                        dict(match='SYN-B',outcome='losses',max_observed_turn=None,battle_date='unknown',
                             opponent={'label':'unknown'}, evidence=[{'type':'knockout','turn':None,'text':'Fictif'}])]}


@pytest.mark.parametrize('scope,expected,details', [('all',6,2),('wins',2,1),('losses',3,1),('unknown',1,0)])
def test_statistical_scope_preserves_aggregate_vs_detail_coverage(scope,expected,details):
    data=report(); before=copy.deepcopy(data)
    model=project_statistics(data,scope)
    assert model['total']==6 and model['scope_n']==expected and model['details_n']==details
    assert sum(sum(g['values']) for g in model['groups'])==expected
    assert sum(sum(g['values']) for g in model['turns'])==details
    assert data==before


def test_unknown_turns_and_event_occurrences_do_not_invent_duration_or_prizes():
    data=report(); data['matches'][0]['evidence'] *= 2
    model=project_statistics(data)
    assert model['turns'][0]['values']==[1] and model['turns'][-1]['values']==[1]
    assert model['event_count']==3
    prizes=next(row for row in model['events'] if 'Récompenses' in row['label'])
    assert prizes['values']==[2]  # two events, never a count of cards taken
    assert 'win_rate' not in model and 'dates' not in model
    assert project_statistics(None)['details_n']==0


def test_recent_entries_only_claim_chronology_with_complete_attested_dates():
    data=report(); rows,basis=recent_matches(data)
    assert rows[0]['match']=='SYN-B' and 'non attestée' in basis
    data['matches'][0]['battle_date']='2026-10-25'
    data['matches'][1]['battle_date']='2026-10-20'
    rows,basis=recent_matches(data)
    assert rows[0]['match']=='SYN-A' and 'datés' in basis
    data['matches'][1]['battle_date']='2026-99-99'
    assert 'non attestée' in recent_matches(data)[1]


def test_timeline_escapes_untrusted_trace_and_keeps_unknowns():
    match=report()['matches'][1]
    match['evidence'][0]['text']='<img src="file:///invented"><script>bad</script>'
    rendered=timeline_html(match,colors('light'))
    assert '<img src=' not in rendered and '&lt;img' in rendered
    assert 'Tour ?' in rendered and 'Cause de la défaite inconnue' in rendered
    assert 'dernière victoire' not in rendered


@pytest.mark.parametrize('invalid', [True,['bad'],['a'*64,'a'*64],['a'*64]*101])
def test_ui_favorites_reject_invalid_preferences(local_tmp,invalid):
    store=Store(local_tmp)
    store.write('preferences.json',{'favorite_decks':invalid})
    with pytest.raises(ValueError,match='CHAT_PREFERENCES_INVALID'):
        store.preferences()


def test_new_ui_preferences_keep_old_settings_and_favorite_exact_export(local_tmp):
    store=Store(local_tmp)
    store.write('preferences.json',{'theme':'light'})
    assert store.preferences()['favorite_decks']==[] and not store.preferences()['sidebar_collapsed']
    assert store.preferences()['theme']=='light'
    assert favorite_key({'export':'invented list','label':'A'})==favorite_key({'export':'invented list','label':'B'})
    assert favorite_key({'export':'invented list'})!=favorite_key({'export':'other invented list'})


def test_chart_filter_and_click_open_matching_battles(ui,app):
    panel=ui.statistics
    panel.tabs.setCurrentIndex(1)
    panel.scope_filter.setCurrentIndex(panel.scope_filter.findData('losses'))
    app.processEvents()
    assert panel.model['scope_n']==4 and panel.model['details_n']==1
    assert 'détails disponibles : 1' in panel.summary.text()
    wait_until(app,lambda:bool(panel.matchups.regions))
    QTest.mouseClick(panel.matchups,Qt.MouseButton.LeftButton,pos=panel.matchups.regions[0].center().toPoint())
    assert ui.stack.currentIndex()==1 and ui.matchup_filter.text()=='Invented Family'
    assert ui.games.currentData()['match']=='M0001'


def test_favorites_home_and_navigation_do_not_change_deck(ui,app):
    export=(Path(__file__).parent/'fixtures/decks/valid_en.txt').read_text(encoding='utf-8')
    row={'label':'Invented favorite','selector':'SYN','export':export,'source':{},'kind':'Référence fictive',
         'legality':'Inconnue','total':60}
    ui.loaded_decks([row]);wait_until(app,lambda:not ui.jobs)
    ui.favorite_button.click()
    assert Store(ui.root).preferences()['favorite_decks']==[favorite_key(row)]
    button=ui.home_favorites.itemAt(0).widget()
    assert isinstance(button,QPushButton)
    button.click()
    assert ui.stack.currentIndex()==2 and ui.deck_text.toPlainText()==export
    ui.favorite_button.click()
    assert Store(ui.root).preferences()['favorite_decks']==[]
    assert row['export']==export


def test_collapsed_sidebar_keeps_icons_keyboard_labels_and_saved_choice(ui,app):
    ui.sidebar_toggle.click()
    assert Store(ui.root).preferences()['sidebar_collapsed'] is True
    for index in range(7):
        item=ui.navigation.item(index)
        assert not item.icon().isNull() and item.text()=='' and item.toolTip()
        assert item.data(Qt.ItemDataRole.AccessibleTextRole)
    ui.navigation.setFocus();QTest.keyClick(ui.navigation,Qt.Key.Key_Down)
    assert ui.stack.currentIndex()==1
    ui.sidebar_toggle.click()
    assert ui.navigation.item(1).text()=='Combats'


def test_chat_bubbles_keep_receipt_and_group_only_safe_sources(ui,app):
    text='2 faits ajoutés · 2 non vérifiés. [Source](https://example.invalid/source) https://example.invalid/source <img src="file:///invented">'
    ui.conversation['messages']=[{'role':'assistant','content':text},
                                 {'role':'user','content':'<script>texte brut</script>'}]
    ui.render_chat();app.processEvents()
    assert '2 faits ajoutés' in ui.transcript.toPlainText()
    assert '<script>texte brut</script>' in ui.transcript.toPlainText()
    assert '<img src=' not in ui.transcript.toHtml()
    assert ui.source_toggle.text()=='Sources regroupées (1)'
    ui.source_toggle.click()
    assert ui.source_drawer.isVisible() and 'https://example.invalid/source' in ui.source_drawer.toPlainText()


def test_home_match_opens_factual_timeline_without_provider(ui,app):
    ui.open_match('M0001')
    assert 'Défaite' in ui.battle_badge.text()
    assert 'Frise des événements connus' in ui.battle_details.toPlainText()
    assert 'Cause de la défaite inconnue' in ui.battle_details.toPlainText()
    assert ui.adapter is None


def test_card_holographic_hover_zoom_and_reduced_motion(ui,app):
    card={'name':'Invented art','quantity':1,'category':'pokemon','printing':'SYN 1'}
    ui.gallery.populate([card]);tile=ui.gallery.tiles[0]
    image=QImage(150,210,QImage.Format.Format_RGB32);image.fill(Qt.GlobalColor.blue)
    buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
    tile.set_image({'data':bytes(buffer.data()),'source_url':'https://example.invalid/art'})
    ui.navigation.setCurrentRow(2)
    try:
        wait_until(app,lambda:not ui.stack.transition.isVisible())
    except AssertionError:
        animation=ui.stack.transition.animation
        pytest.fail('Transition did not finish: ' + str((animation.state(),animation.currentTime(),animation.duration(),ui.stack.transition.progress)))
    QApplication.sendEvent(tile.art,QEvent(QEvent.Type.Enter))
    wait_until(app,lambda:tile.art.hover>0)
    proof=[]
    def close_zoom():
        dialog=QApplication.activeModalWidget()
        zoom=dialog.findChild(ZoomImage)
        proof.append(zoom is not None and not zoom.picture.isNull())
        dialog.accept()
    QTimer.singleShot(100,close_zoom)
    tile.enlarge()
    assert proof==[True]
    ui.reduced_motion.setChecked(True)
    assert tile.art.hover==0 and not tile.art.motion_enabled
