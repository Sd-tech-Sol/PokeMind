"""Live bilingual UI, with opaque original-language content and no reload."""
import copy
import html
import json
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt, QTimer, QCoreApplication
from PySide6 import QtWidgets as Native
from test_desktop_qt import app, ui, wait_until, dispose_window
from pokemind.desktop import window
from pokemind.desktop.i18n import T, J, Text, display, set_language, QLabel, QMessageBox, QFileDialog


@pytest.fixture(autouse=True)
def restore_language():
    set_language('fr')
    yield
    set_language('fr')


def select(ui, language):
    ui.language.setCurrentIndex(ui.language.findData(language))


def test_paired_text_escaping_and_join_preserve_opaque_data():
    original='Réglages <img src="file:///invented">'
    text=T('Sources regroupées')+' : '+html.escape(original)+' '+J(' / ',[T('Thème clair'),original])
    assert isinstance(text,Text)
    set_language('en')
    assert display(text).startswith('Grouped sources')
    assert 'Light theme' in display(text) and 'Réglages &lt;img' in display(text)
    assert display(copy.deepcopy(text))==display(text)
    set_language('fr')
    assert display(text).startswith('Sources regroupées')


def test_live_language_covers_pages_settings_headers_and_late_status(ui,app):
    select(ui,'en');app.processEvents()
    assert ui.navigation.item(5).text()=='Settings'
    assert ui.theme.itemText(0)=='Dark theme' and ui.theme.currentData()=='dark'
    assert ui.reduced_motion.text().startswith('Reduce motion')
    assert 'I allow my questions' in ui.cloud_consent.text()
    assert ui.permission_mode.itemText(1)=='Full access (--yolo)'
    assert 'Watch for new logs' in ui.watch_logs.text()
    assert 'Show public TCGdex' in ui.card_images.text()
    labels=[label.text() for label in ui.findChildren(Native.QLabel)]
    assert any('Verified external isolation' in text for text in labels)
    assert ui.matchups.horizontalHeaderItem(0).text()=='Family / signature'
    assert ui.matchups.horizontalHeaderItem(1).text()=='W'
    assert ui.statistics.tabs.tabText(0)=='Summary'
    assert [ui.card_results.horizontalHeaderItem(i).text() for i in range(3)]==['Printing','Language','Name']
    assert ui.language.accessibleName()=='Application language'
    assert 'Analysis saved as of' in ui.overview.text()
    ui.failed('SYNTHETIC_CODE')
    assert ui.statusBar().currentMessage()=='Service unavailable · SYNTHETIC_CODE'
    select(ui,'fr')
    assert ui.navigation.item(5).text()=='Réglages'
    assert ui.theme.itemText(0)=='Thème sombre'
    assert ui.card_results.horizontalHeaderItem(2).text()=='Nom'
    assert ui.statusBar().currentMessage()=='Service indisponible · SYNTHETIC_CODE'


def test_hot_switch_preserves_draft_history_filters_session_and_no_requests(ui,app,monkeypatch):
    ui.statistics.tabs.setCurrentIndex(2)
    ui.statistics.scope_filter.setCurrentIndex(ui.statistics.scope_filter.findData('losses'))
    ui.chat_input.setPlainText(T('Dans mes combats, quelles situations travailler contre '))
    ui.chat_input.insertPlainText('Réglages : source originale et brouillon')
    draft=ui.chat_input.toPlainText()
    ui.conversation['messages']=[{'role':'user','content':'Ne pas traduire Réglages.'},
                                  {'role':'assistant','content':('Source originale : Thème sombre.\n\n'*80)}]
    ui.conversation['session']='invented-locale-thread'
    ui.render_chat();app.processEvents()
    scrollbar=ui.transcript.verticalScrollBar()
    assert scrollbar.maximum()>100
    scrollbar.setValue(100)
    previous=json.dumps(ui.conversation,ensure_ascii=False)
    report=copy.deepcopy(ui.services.report)
    identity=int(ui.winId());pages=[ui.stack.widget(i) for i in range(6)]
    def forbidden(*args,**kwargs):raise AssertionError('Language switch must not reload data or start a provider')
    monkeypatch.setattr(ui.services,'load',forbidden)
    monkeypatch.setattr(ui.services,'deck_options',forbidden)
    monkeypatch.setattr(ui,'get_adapter',forbidden)
    for language in ('en','fr','en','fr'):
        select(ui,language);app.processEvents()
        assert int(ui.winId())==identity and [ui.stack.widget(i) for i in range(6)]==pages
        assert ui.chat_input.toPlainText()==draft
        assert json.dumps(ui.conversation,ensure_ascii=False)==previous
        assert scrollbar.value()==100
        assert ui.services.report==report and not ui.jobs
        assert ui.statistics.tabs.currentIndex()==2 and ui.statistics.scope_filter.currentData()=='losses'
        assert [m.text() for m in ui.metrics]==['6','2','4']


def test_new_widgets_graphs_and_local_answer_follow_language_without_translating_facts(ui,app):
    select(ui,'en')
    label=QLabel(T('Réduire les animations et afficher les pages instantanément'),ui)
    assert label.text().startswith('Reduce motion')
    ui.statistics.tabs.setCurrentIndex(2)
    assert 'Turns 1–4' in ui.statistics.turns.accessibleDescription()
    ui.open_match('M0001')
    assert 'Known event timeline' in ui.battle_details.toPlainText()
    assert 'Observed Knock Out' in ui.battle_details.toPlainText()
    assert 'Créature inventée mise K.O.' in ui.battle_details.toPlainText()
    answer=str(ui.services.local_answer('my statistics'))
    assert 'unique games recorded' in answer and 'overall win rate unknown' in answer
    select(ui,'fr')
    assert label.text().startswith('Réduire les animations')
    assert 'Frise des événements connus' in ui.battle_details.toPlainText()
    assert 'K.O. observé' in ui.battle_details.toPlainText()


def test_modal_buttons_and_native_qt_translations_follow_selected_language(ui,app):
    for language,expected in (('en',('Confirm?','Translation test.','Yes','No')),
                              ('fr',('Confirmer?','Test de traduction.','Oui','Non'))):
        select(ui,language);observed=[]
        def decline():
            dialog=Native.QApplication.activeModalWidget()
            observed.append((dialog.windowTitle(),dialog.text(),
                             dialog.button(QMessageBox.StandardButton.Yes).text().replace('&',''),
                             dialog.button(QMessageBox.StandardButton.No).text().replace('&','')))
            dialog.done(int(QMessageBox.StandardButton.No))
        QTimer.singleShot(40,decline)
        result=QMessageBox.question(ui,T('Confirmer?'),T('Test de traduction.'))
        assert result==QMessageBox.StandardButton.No and observed==[expected]
        assert QCoreApplication.translate('QPlatformTheme','Cancel')==('Cancel' if language=='en' else 'Annuler')


def test_file_dialog_caption_filter_and_options_are_localized_without_browsing(ui,app,monkeypatch):
    seen=[]
    monkeypatch.setattr(Native.QFileDialog,'getOpenFileNames',lambda *a,**k:(seen.append((a,k)) or ([],'')))
    select(ui,'en')
    assert QFileDialog.getOpenFileNames(ui,T('Joindre des journaux TCG Live'),str(ui.root),T('Journaux texte (*.txt *.log)'))==([],'')
    args,kwargs=seen[0]
    assert args[1]=='Attach TCG Live logs' and args[3]=='Text logs (*.txt *.log)'
    assert args[2]==str(ui.root)
    assert kwargs['options'] & Native.QFileDialog.Option.DontUseNativeDialog


def test_language_persists_with_other_preferences_on_reopening(ui,app):
    ui.theme.setCurrentIndex(1)
    ui.reduced_motion.setChecked(True)
    ui.sidebar_toggle.click()
    ui.preferences['favorite_decks']=['a'*64]
    select(ui,'en');ui.close()
    reopened=window.MainWindow(ui.root);reopened.show()
    try:
        wait_until(app,lambda:not reopened.jobs and reopened.metrics[0].text()=='6')
        assert reopened.language.currentData()=='en' and reopened.theme.currentData()=='light'
        assert reopened.send_button.text().startswith('Send') and 'Enter' in reopened.send_button.toolTip()
        assert reopened.preferences['favorite_decks']==['a'*64]
        assert reopened.reduced_motion.isChecked() and reopened.preferences['sidebar_collapsed']
        assert reopened.navigation.item(5).toolTip()=='Settings'
    finally:
        dispose_window(reopened,app)


def test_localized_research_receipt_preserves_facts_sources_counts_and_cli_default():
    from test_research_answers import receipt
    from pokemind.assistant.receipts import public_research_message
    value=receipt()
    value['facts'][0]['entries'][0]['archetype']='Réglages'
    value['sources']=['https://www.limitlesstcg.com/decks/1/rapport']
    value['facts'][0]['source_url']=value['sources'][0]
    before=copy.deepcopy(value)
    french=public_research_message(value,'meta')
    set_language('en')
    english=str(public_research_message(value,'meta',text=T,join=J))
    assert 'PokeMind answer — public observations' in english
    assert '1 facts added' in english and 'Local save confirmed' in english
    assert '"Réglages"' in english and value['sources'][0] in english
    assert 'no win rate inferred' in english and 'schema_validated' not in english
    assert value==before and public_research_message(value,'meta')==french
    assert 'Résultat PokeMind — mémoire publique' in french


def test_localized_rule_qualification_preserves_status_and_does_not_certify_source():
    from pokemind.public_source_fields import EXTRACTOR, qualified_rule_fields
    value={'source_url':'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources',
           'rule_evidence':{'extractor':EXTRACTOR,'rights':{'retention':'not_authorized'}}}
    before=copy.deepcopy(value)
    french=qualified_rule_fields(value)
    set_language('en')
    english=[str(row) for row in qualified_rule_fields(value,text=T,join=J)]
    assert english==['Extraction: RETENTION_NOT_AUTHORIZED; current applicability: unknown.']
    assert qualified_rule_fields(value)==french and value==before
