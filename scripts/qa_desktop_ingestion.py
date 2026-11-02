"""Explicit visible Windows QA. Private proofs stay local, synthetic corpus isolated."""
from __future__ import annotations

import argparse
import json
import re
import time
import traceback
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QMimeData, QUrl, QPointF
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pokemind.desktop.window import MainWindow
from pokemind.desktop import ingestion
from pokemind.assistant.sessions import Store
from pokemind import battle_batch, battle_coach


def invented(tag=1, *, complete=True, large=False):
    text = ("Reference player: InventedQA\nTurn # 1 - InventedQA's Turn\n"
        f"InventedQA played Invented Creature {tag}.\nTurn # 2 - InventedRival{tag}'s Turn\n"
        f"InventedRival{tag} played Other Invented Creature {tag}.\n")
    if large:
        text += 'Observation inventée sans action.\n' * 3000
    return text + (f'InventedRival{tag} wins.\n' if complete else '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real-windows', action='store_true', required=True)
    parser.add_argument('--owner-codex', action='store_true')
    args = parser.parse_args()
    root = Path.cwd()
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    if app.platformName() != 'windows':
        raise SystemExit('WINDOWS_NATIVE_PLATFORM_REQUIRED')
    proof_folder = root / 'data/local/desktop-dev' / ('correction-' + uuid.uuid4().hex)
    proof_folder.mkdir(parents=True)
    fixture = root / 'data/local/test-runs' / uuid.uuid4().hex
    fixture.mkdir(parents=True)
    store = Store(fixture)
    prefs = store.preferences(); prefs['card_images'] = False
    store.write('preferences.json', prefs)
    original = Store(root).read('preferences.json') if args.owner_codex else None
    state = {'stage':0,'start':time.monotonic(),'proof':{},'windows':[],'chunks':0,'provider_calls':0,'finishing':False}

    class Observed(MainWindow):
        def chat_delta(self, value):
            state['chunks'] += 1
            super().chat_delta(value)

    def create(selected, synthetic=False):
        w = Observed(selected)
        if synthetic:
            w.setWindowTitle('QA — corpus synthétique isolé · PokeMind réel')
        w.show()
        state['window'] = w
        state['windows'].append(w)
        return w

    def paste(value):
        w = state['window']
        app.clipboard().setText(value)
        w.chat_input.clear()
        QTest.keyClick(w.chat_input, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(w.chat_input, Qt.Key.Key_Return)

    def finish(ok, code='OK'):
        state.update(finishing=True,ok=ok,code=code)
        for w in state['windows']:
            if w.chat_busy:w.stop_chat()
            w.data_cancel.set()
            w.close()

    create(fixture, True)

    def tick():
        try:
            step()
        except Exception:
            (proof_folder/'private-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
            finish(False,'QA_LOCAL_EXCEPTION_STAGE_' + str(state['stage']))

    def step():
        w, p, stage = state['window'], state['proof'], state['stage']
        if state['finishing']:
            if any(q.chat_busy or q.data_busy or q.pool.activeThreadCount() or q.image_pool.activeThreadCount() or q.isVisible() for q in state['windows']):
                for q in state['windows']:q.close()
                return
            if args.owner_codex and original is not None:
                Store(root).write('preferences.json', original)
                p['owner_cloud_preferences_preserved'] = Store(root).read('preferences.json') == original
                if not p['owner_cloud_preferences_preserved']:
                    state.update(ok=False,code='OWNER_PREFERENCES_RESTORE_FAILED')
            p.update(ok=state['ok'],code=state['code'],native_windows=True,
                raw_logs_sent_to_provider=False,synthetic_corpus_isolated=True)
            (proof_folder/'proof.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
            print(json.dumps(p),flush=True)
            timer.stop();app.exit(0 if state['ok'] else 2)
            return
        if time.monotonic()-state['start'] > 300:
            finish(False,'QA_TIMEOUT_STAGE_' + str(stage));return
        if stage == 0 and not w.data_busy:
            p['visible_window'] = w.isVisible() and bool(w.winId())
            w.chat_input.setPlainText('Question temporaire')
            QTest.keyClick(w.chat_input,Qt.Key.Key_Return,Qt.KeyboardModifier.ShiftModifier)
            p['shift_enter_newline'] = '\n' in w.chat_input.toPlainText() and not w.chat_busy
            paste(invented())
            state['stage']=1
        elif stage == 1 and not w.ingest_busy:
            p['paste_real_pipeline_saved'] = w.metrics[0].text()=='1' and 'Partie enregistrée' in w.transcript.toPlainText()
            p['visual_recognition_and_publication'] = 'Journal reconnu' in w.transcript.toPlainText() and 'Enregistrement en cours' in w.transcript.toPlainText()
            p['statistics_really_updated'] = w.services.report['outcomes']['losses']==1
            QTest.mouseClick(w.view_import_button,Qt.MouseButton.LeftButton)
            p['open_selected_analysis'] = w.stack.currentIndex()==1 and w.games.currentData() is not None
            w.grab().save(str(proof_folder/'synthetic-saved.png'))
            paste(invented());state['stage']=2
        elif stage == 2 and not w.ingest_busy:
            p['duplicate_no_increment'] = w.metrics[0].text()=='1' and 'Doublon détecté' in w.conversation['messages'][-1]['content']
            paste(invented(complete=False));state['stage']=3
        elif stage == 3 and not w.ingest_busy:
            p['incomplete_refused'] = w.metrics[0].text()=='1' and 'Importation refusée' in w.conversation['messages'][-1]['content']
            paste('InventedQA played Something.\nInventedRival drew a card.');state['stage']=4
        elif stage == 4 and not w.ingest_busy:
            p['ambiguous_kept_local'] = 'Collage ambigu' in w.conversation['messages'][-1]['content'] and w.adapter is None
            paste(invented(2,large=True));state['stage']=5
        elif stage == 5 and not w.ingest_busy:
            p['large_journal_local'] = w.metrics[0].text()=='2' and w.adapter is None
            attached=fixture/'attached.log';attached.write_text(invented(3),encoding='utf-8')
            mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(attached))])
            event=QDropEvent(QPointF(20,20),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
            w.chat_input.dropEvent(event);state['stage']=6
        elif stage == 6 and not w.ingest_busy:
            p['file_drop_ingested'] = w.metrics[0].text()=='3'
            w.startup_refresh.setChecked(True)
            w.close();state['stage']=7
        elif stage == 7 and not w.isVisible():
            (fixture/'data/local/battle_logs/startup-new.log').write_text(invented(4),encoding='utf-8')
            create(fixture,True);state['stage']=8
        elif stage == 8 and not w.data_busy and w.metrics[0].text()=='4':
            p['reopened_startup_ingests_unique'] = '1 nouvelles parties uniques' in w.statusBar().currentMessage()
            w.close();state['stage']=9
        elif stage == 9 and not w.isVisible():
            if not args.owner_codex:
                finish(all(p.values()));return
            create(root);state['stage']=10
        elif stage == 10 and not w.data_busy and w.services.report:
            w.card_images.setChecked(True)
            w.reload(True);state['stage']=11
        elif stage == 11 and not w.data_busy:
            report=w.services.report
            state['expected']=(report['coverage']['valid'],report['outcomes']['wins'],report['outcomes']['losses'])
            player=ingestion.configured_player(root)
            files,_,_=battle_batch.files_in_folder(root,root/battle_coach.LOG_DIR)
            for path in files:
                value,_=battle_batch.read_selected(root/battle_coach.LOG_DIR,path)
                for piece in battle_batch.segments(value):
                    parsed,_=ingestion.validate(piece,player)
                    if parsed and battle_batch.digest(battle_batch.semantic_text(piece)) in w.services.match_index:
                        state['duplicate_text']=piece;break
                if 'duplicate_text' in state:break
            if 'duplicate_text' not in state:finish(False,'NO_COMPLETE_OWNER_LOG');return
            state['owner_files_before']={str(f.relative_to(root)): (f.stat().st_size,f.stat().st_mtime_ns) for f in files}
            w.provider.setCurrentIndex(w.provider.findData('codex'))
            w.cloud_consent.setChecked(True);w.sharing.setCurrentIndex(1)
            w.new_conversation()
            adapter=w.get_adapter();original_ask=adapter.ask_stream
            def observed(prompt,history,emit,tool=None):
                state['provider_calls']+=1
                assert state['duplicate_text'] not in prompt
                assert not any('Reference player:' in m['content'] or 'Joueur de référence :' in m['content'] for m in history)
                return original_ask(prompt,history,emit,tool)
            adapter.ask_stream=observed
            w.chat_input.setPlainText('Dans mes combats conservés, donne exactement le nombre de parties uniques, de victoires et de défaites. Écris ces chiffres en nombres, cite la date du rapport PokeMind et précise que le taux de victoire global est inconnu. La méta publique ne remplace pas ces données.')
            w.send_chat();state['stage']=12
        elif stage == 12 and not w.chat_busy:
            answer=w.conversation['messages'][-1]['content']
            (proof_folder/'private-codex-personal-answer.txt').write_text(answer,encoding='utf-8')
            p['real_codex_personal_grounding']=all(re.search(r'(?<!\d)'+str(n)+r'(?!\d)',answer) for n in state['expected']) and 'inconnu' in answer.casefold() and 'indisponible' not in answer.casefold()
            p['real_codex_streaming']=state['chunks']>1
            w.grab().save(str(proof_folder/'private-owner-codex.png'))
            paste(state['duplicate_text']);state['stage']=13
        elif stage == 13 and not w.ingest_busy:
            p['real_owner_duplicate_local_only']=state['provider_calls']==1 and 'Doublon détecté' in w.conversation['messages'][-1]['content'] and int(w.metrics[0].text())==state['expected'][0]
            files,_,_=battle_batch.files_in_folder(root,root/battle_coach.LOG_DIR)
            p['owner_raw_files_preserved']=state['owner_files_before']=={str(f.relative_to(root)): (f.stat().st_size,f.stat().st_mtime_ns) for f in files}
            w.navigation.setCurrentRow(2)
            selected=next((i for i,r in enumerate(w.deck_rows) if 'Dragapult ex' in r['export'] or 'Lanssorien-ex' in r['export']),0)
            w.deck_picker.setCurrentIndex(selected)
            state['stage']=14
        elif stage == 14 and w.gallery.tiles and any(not t.picture.isNull() for t in w.gallery.tiles):
            p['real_gallery_60_and_images']=sum(t.card['quantity'] for t in w.gallery.tiles)==60
            w.grab().save(str(proof_folder/'private-gallery.png'))
            tile=next(t for t in w.gallery.tiles if not t.picture.isNull())
            state['stage']=15
            def enlarged():
                dialog=QApplication.activeModalWidget();p['real_image_enlarged']=dialog is not None
                if dialog:dialog.grab().save(str(proof_folder/'private-card-enlarged.png'));dialog.accept()
            QTimer.singleShot(250,enlarged)
            tile.enlarge()
            w.sharing.setCurrentIndex(0)
            w.chat_input.setPlainText('Énumère 300 exercices généraux et inventés de raisonnement en jeux de cartes, avec une explication par exercice. Aucun contexte personnel.')
            w.send_chat();state['stage']=16
        elif stage == 16 and w.chat_busy and w.adapter and w.adapter.turn and w.activity.elapsed.elapsed()>100:
            p['real_activity_animated_wait_elapsed']=w.activity.animation.isVisible() and w.activity.timer.isActive() and w.activity.animation.maximum()==0
            w.grab().save(str(proof_folder/'private-activity.png'))
            QTest.mouseClick(w.stop_button,Qt.MouseButton.LeftButton);state['stage']=17
        elif stage == 17 and not w.chat_busy:
            p['real_codex_interrupted']='Interrompu' in w.activity.label.text() and w.adapter.stopped.is_set()
            finish(all(p.values()))

    timer=QTimer();timer.timeout.connect(tick);timer.start(100)
    return app.exec()


if __name__=='__main__':
    raise SystemExit(main())
