"""Native technical reception of the manual launcher; never owner acceptance."""
import json
from datetime import date


def exercise(app, widget, runtime, *, phase):
    from PySide6.QtCore import Qt, QTimer, QUrl, QThread
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QMessageBox
    from test_desktop_qt import wait_until, dispose_window
    from pokemind import batch_public_research as research
    from qa_unified_desktop import (LOG, memory_consistency_gate, research_answer_gate, source_depth_gate)

    root, fixture = runtime.context.root, runtime.fixture
    proof = {'phase': phase, 'native_windows': app.platformName() == 'windows', 'gates': {}}
    gates = proof['gates']
    database = fixture / 'data/local/pokemind.sqlite3'
    database_before = database.read_bytes()  # exclusively freshly invented schema7

    def gate(name, value):
        gates[name] = bool(value)
        assert value, name

    def idle():
        wait_until(app, lambda: not widget.jobs and not widget.chat_busy and not widget.data_busy
                   and not widget._startup_pending and bool(widget.services.report)
                   and widget.metrics[0].text() == str(widget.services.report['coverage']['valid']), 15000)

    def send(text, *, button=False):
        widget.chat_input.setPlainText(text)
        assert widget.chat_input.isEnabled(), 'chat_input_enabled'
        if button:
            widget.send_button.click()
        else:
            QTest.keyClick(widget.chat_input, Qt.Key.Key_Return)
        idle()

    try:
        idle()
        gate('native_application_event_loop_running', QThread.currentThread().loopLevel() > 0)
        gate('seven_pages_one_chat', widget.isVisible() and widget.stack.count() == 7
             and len(widget.findChildren(type(widget.chat_input))) == 1)
        gate('offline_banner_visible', widget.qa_banner.isVisible() and 'DONNÉES FICTIVES' in widget.qa_banner.text())
        gate('offline_labels_persist', 'fournisseurs réels désactivés' in widget.permission_badge.text()
             and 'aucun envoi' in widget.context_status.text() and 'fictifs' in widget.chat_input.placeholderText())
        for index in range(6):
            widget.navigation.setCurrentRow(index)
            app.processEvents()
            gate('page_' + str(index), widget.stack.currentIndex() == index)
        widget.navigation.setCurrentRow(0)
        app.processEvents()
        if phase == 'first':
            gate('fresh_fixture_n1', widget.services.report['coverage']['valid'] == 1)
            send('Explique les Récompenses dans cette QA inventée.', button=True)
            gate('fixed_fake_answer', 'Réponse inventée' in widget.conversation['messages'][-1]['content'] and runtime.calls == 1)
            deck = (fixture / 'qa-inputs/deck60.txt').read_text(encoding='utf-8')
            send('Voici uniquement mon deck fictif de QA :\n' + deck)
            gate('deck60_pasted_saved', deck.strip() in widget.conversation['messages'][-2]['content'])
            validation = widget.services.validate_deck(deck)
            gate('real_deck_validator_60_unknown_collection', validation['total_cards'] == 60
                 and validation['collection'] == 'unknown' and not validation['ready_in_live'])
            send(LOG + '\nPourquoi cette défaite? Reconstruis son deck comme hypothèse et cite tes sources.')
            gate('invented_log_and_followup', widget.services.report['coverage']['valid'] == 2
                 and widget.conversation.get('selected_match') and not widget.chat_failed)
            send(LOG)
            gate('duplicate_does_not_increase_n', widget.services.report['coverage']['valid'] == 2
                 and 'Doublon détecté' in widget.conversation['messages'][-1]['content'])
            send((fixture / 'qa-inputs/journal-partiel.txt').read_text(encoding='utf-8'))
            gate('incomplete_log_refused_without_new_match', widget.services.report['coverage']['valid'] == 2
                 and 'Importation refusée' in widget.conversation['messages'][-1]['content'])
            reconstruction = widget.services.reconstruct()
            gate('sourced_variants_remain_hypotheses', bool(reconstruction['variants']) and all(
                v['total_cards'] == 60 and not v['is_exact_opponent_deck'] and v['probability'] is None
                and v['source']['source_urls'] for v in reconstruction['variants']))
            # Refuse the actual existing dialog, not a substitute consent path.
            prior = json.dumps(widget.conversation)
            question = 'Crée le fichier invented-proof.txt et teste son contenu avec Python.'
            observed = []
            def decline():
                dialog = app.activeModalWidget()
                observed.append(isinstance(dialog, QMessageBox)
                                and dialog.defaultButton() == dialog.button(QMessageBox.StandardButton.No))
                if isinstance(dialog, QMessageBox):
                    QTest.mouseClick(dialog.button(QMessageBox.StandardButton.No), Qt.MouseButton.LeftButton)
            QTimer.singleShot(40, decline)
            send(question)
            gate('consent_default_no_draft_history_preserved', observed == [True]
                 and widget.chat_input.toPlainText() == question and json.dumps(widget.conversation) == prior)
            before_calls = runtime.calls
            send('/status')
            gate('provider_command_blocked_without_inference', widget.chat_failed
                 and runtime.calls == before_calls and runtime.blocked and not runtime.context.denials)
            widget.internal_link(QUrl('https://example.invalid/invented'))
            gate('external_link_refused_before_browser', 'liens externes désactivés' in widget.provider_status.text())
            prior = json.dumps(widget.conversation)
            widget.attach_logs(['INVENTED_ATTACHMENT.txt'])
            gate('attachments_refused_before_read', json.dumps(widget.conversation) == prior
                 and 'fichiers désactivés' in widget.provider_status.text())
            question = 'Cherche les règles pour cette QA fictive puis explique leurs implications; mémorise les sources comme non vérifiées.'
            send(question)
            receipt = runtime.last_receipt
            message = widget.conversation['messages'][-1]
            saved = widget.store.load(widget.conversation['id'])['messages'][-1]
            rendered = widget.transcript.toPlainText()
            gate('host_memory_receipt_saved_rendered', memory_consistency_gate(receipt, message, rendered, saved))
            gate('host_research_answer_saved_rendered', research_answer_gate(receipt, question, message, rendered, saved))
            gate('invented_source_depth_and_unknowns', source_depth_gate(receipt, message, rendered, saved))
            gate('two_invented_unverified_rule_facts', receipt['added'] == 2 and receipt['unverified'] == 2)
            before = runtime.opener.calls
            send('Cherche la méta pour cette QA fictive et explique les limites.')
            gate('missing_meta_remains_offline', runtime.last_receipt['status'] == 'OFFLINE_STALE_OR_EMPTY'
                 and runtime.last_receipt['gets'] == 0 and runtime.opener.calls == before)
            gate('unknown_visible', 'unknown' in widget.transcript.toPlainText()
                 or 'inconnu' in widget.conversation['messages'][-1]['content'].casefold())
            # Save a simple stable sentinel in the same existing conversation.
            send('Message fictif de reprise : INVENTED_OFFLINE_REOPEN_001')
            saved = widget.store.load(widget.conversation['id'])
            (root / 'reopen-local.json').write_text(json.dumps({'id': saved['id'], 'messages': saved['messages']}), encoding='utf-8')
        else:
            saved = json.loads((root / 'reopen-local.json').read_text(encoding='utf-8'))
            gate('same_conversation_reopened', widget.conversation['id'] == saved['id'])
            gate('same_saved_messages', widget.conversation['messages'] == saved['messages'])
            gate('sentinel_visible_after_reopen', 'INVENTED_OFFLINE_REOPEN_001' in widget.transcript.toPlainText())
            gate('same_two_unique_matches', widget.services.report['coverage']['valid'] == 2)
            facts = research.knowledge_view(fixture, as_of=date.today().isoformat(), topic='rules')['facts']
            gate('two_rule_facts_reopened', len(facts) == 2)
            receipt = research.research(fixture, as_of=date.today().isoformat(), topic='rules')
            gate('cache_reuse_zero_source_calls', receipt['added'] == receipt['updated'] == 0
                 and receipt['gets'] == 0 and runtime.opener.calls == 0)
            gate('no_provider_inference_on_reopen', runtime.calls == 0)
        gate('invented_legacy_database_unchanged', database.read_bytes() == database_before)
        gate('no_instrumented_security_denials', not runtime.context.denials and not runtime.context.security_incident)
        gate('window_capture_saved', widget.grab().save(str(root / ('offline-' + phase + '.png'))))
        dispose_window(widget, app)
        gate('window_closed', not app.topLevelWidgets())
        proof['ok'] = True
        return 0
    finally:
        proof.update(runtime.summary())
        (root / ('reception-' + phase + '.json')).write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
