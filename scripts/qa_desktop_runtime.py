"""Explicit Windows QA: visible real data locally, public-only Codex prompts.

Run from the project root with the isolated desktop interpreter. Never run on CI.
Private screenshots, conversation IDs and transcripts stay in data/local.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from pokemind.desktop.window import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real-windows-codex', action='store_true', required=True)
    args = parser.parse_args()
    root = Path.cwd()
    target = root / 'data/local/desktop-dev'
    target.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    state = {'stage': 0, 'chunks': 0, 'start': time.monotonic(), 'proof': {}}

    class ObservedWindow(MainWindow):
        def chat_delta(self, text):
            state['chunks'] += 1
            super().chat_delta(text)

    def create():
        widget = ObservedWindow(root)
        widget.show()
        return widget

    state['window'] = create()

    def send(question):
        w = state['window']
        w.cloud_consent.setChecked(True)
        w.sharing.setCurrentIndex(0)  # No owner aggregates or events sent by QA.
        w.chat_input.setPlainText(question)
        w.send_chat()

    def finish(ok, code='OK'):
        state['proof'].update(ok=ok, code=code, provider='codex_app_server_stdio',
            public_only_cloud_context=True, private_raw_sent=False, streaming_chunks=state['chunks'])
        (target/'windows-runtime-qa.json').write_text(json.dumps(state['proof'], indent=2), encoding='utf-8')
        print(json.dumps(state['proof']), flush=True)
        w = state['window']
        w.grab().save(str(target/'windows-runtime-final.png'))
        w.close()
        if not w.chat_busy and not w.data_busy:
            app.exit(0 if ok else 2)

    def tick():
        w = state['window']
        proof, stage = state['proof'], state['stage']
        if time.monotonic()-state['start'] > 240:
            timer.stop();finish(False, 'QA_TIMEOUT');return
        if stage == 0 and w.services.report and w.deck_rows:
            proof.update(visible_window=w.isVisible(), real_saved_report_loaded=True,
                exact60_references_available=all(r['total']==60 for r in w.deck_rows), seven_pages=w.stack.count()==7)
            w.navigation.setCurrentRow(1);w.matchups.selectRow(0)
            proof['selected_match_timeline_visible']=bool(w.battle_details.toPlainText())
            w.navigation.setCurrentRow(2);w.deck_picker.setCurrentIndex(0);w.copy_export()
            from pokemind.decks import parse_deck_export
            proof['deck_copy_verified60']=parse_deck_export(app.clipboard().text()).total_cards==60
            w.navigation.setCurrentRow(3);w.card_query.setText('Lanssorien');w.search_cards()
            state['stage']=1
        elif stage == 1 and w.card_results.rowCount():
            w.card_results.selectRow(0)
            state['stage']=2
        elif stage == 2 and w.card_details.toPlainText():
            proof['card_search_and_detail']=True
            w.navigation.setCurrentRow(0)
            w.new_conversation()
            send('Explique en deux phrases comment PokeMind distingue ses observations, ses hypotheses et ses sources. N utilise aucune statistique personnelle.')
            state['stage']=3
        elif stage == 3 and not w.chat_busy:
            proof['first_real_codex_turn']=bool(w.conversation['messages'][-1]['content']) and '[Réponse indisponible' not in w.conversation['messages'][-1]['content']
            state['thread']=w.conversation['session']
            send('Dans notre discussion, quelle prudence faut-il garder avant de changer une carte apres une defaite? Reponds en deux phrases, sans outil externe.')
            state['stage']=4
        elif stage == 4 and not w.chat_busy:
            proof['second_real_codex_turn']=bool(w.conversation['messages'][-1]['content']) and '[Réponse indisponible' not in w.conversation['messages'][-1]['content']
            proof['same_thread_multiturn']=state['thread']==w.conversation['session']
            state['conversation']=w.conversation['id']
            w.grab().save(str(target/'windows-runtime-two-turns.png'))
            w.close()
            state['window']=create()
            state['stage']=5
        elif stage == 5 and w.services.report:
            proof['history_reopened']=w.conversation['id']==state['conversation'] and len(w.conversation['messages'])>=4
            send('Reprends notre discussion et rappelle en une phrase le conseil de prudence donne juste avant. Aucun contexte personnel.')
            state['stage']=6
        elif stage == 6 and not w.chat_busy:
            proof['provider_thread_resumed']=state['thread']==w.conversation['session'] and '[Réponse indisponible' not in w.conversation['messages'][-1]['content']
            send('Ecris une longue liste de 200 exercices purement generaux et inventes sur le raisonnement en jeux de cartes, sans donnees personnelles.')
            state['stage']=7
        elif stage == 7 and w.adapter and w.adapter.turn:
            w.stop_chat();state['stage']=8
        elif stage == 8 and not w.chat_busy:
            proof['real_turn_cancelled']=w.adapter.stopped.is_set() and 'interrompue' in w.conversation['messages'][-1]['content']
            proof['streaming_observed']=state['chunks']>1
            timer.stop()
            finish(all(proof.values()))

    timer=QTimer();timer.timeout.connect(tick);timer.start(200)
    return app.exec()


if __name__=='__main__':
    raise SystemExit(main())
