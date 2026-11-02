"""Manual real-provider QA on an exclusively invented workspace under build/."""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from pokemind.assistant.codex_app_server import CodexAppServer
from pokemind.assistant.provider import ClaudeCode
from pokemind.batch_public_research import research
from pokemind.battle_batch import safe_path
from datetime import date


def main():
    root = Path.cwd().absolute()
    target = safe_path(root, root / ('build/unified-qa-' + uuid.uuid4().hex), exists=False)
    target.mkdir()
    client = CodexAppServer(target)
    proof = {'scope': 'INVENTED_WORKSPACE_PUBLIC_CLOUD_ONLY', 'private_data_sent': False}
    events = []
    try:
        status = client.status()
        print('QA: official status read', flush=True)
        proof['official_status'] = status['account'].get('authenticated', False)
        proof['official_rate_limits'] = status['limits'].get('status') != 'unavailable'
        proof['official_usage'] = status['usage'].get('status') != 'unavailable'
        client.configure(development=True, cwd=target, permission_mode='workspace', privacy_acknowledged=True)
        def event(value):
            events.append(value)
            item = value['params'].get('item', {})
            print('QA tool:', item.get('type'), item.get('status'), flush=True)
        client.on_event = event
        client.start()
        print('QA: standard unisolated synthetic thread started', flush=True)
        output = []
        client.ask_stream('Utilise exclusivement pokemind_project : operation write pour le fichier, puis operation exec '
            'pour lancer powershell.exe -NoProfile -NonInteractive -Command et la verification Python. '
            'Dans ce repertoire de QA entierement invente, cree uniquement proof.txt avec le texte EXACT INVENTED_OK. '
            'Puis lance une commande Python qui lit proof.txt et verifie par assert que son contenu vaut INVENTED_OK '
            '(un saut de ligne final est permis). N utilise pas de donnees personnelles, pas de reseau, '
            'pas de delegation et ne supprime rien. Reponds brievement en francais.', [], output.append)
        print('QA: Codex turn completed', flush=True)
        proof['codex_real_edit'] = (target / 'proof.txt').read_text(encoding='utf-8').strip() == 'INVENTED_OK'
        proof['codex_real_test_exit_zero'] = (client.last_command_result or {}).get('exitCode') == 0 and 'assert' in ' '.join(client.last_command_argv or [])
        proof['command_events'] = sum(e['params'].get('item', {}).get('type') in {'commandExecution','dynamicToolCall'} for e in events)
        proof['codex_stream'] = bool(output)
        proof['mode'] = 'workspace_profile_no_full_access'
    except Exception:
        if client.process:
            print(''.join(list(client.process._pokemind_errors)[-10:]), flush=True)
        print(json.dumps({'qa_failed': True, 'provider_error': client.last_error}), flush=True)
        raise
    finally:
        client.close()
    if '--claude' in sys.argv:
        client = ClaudeCode(target)
        try:
            client.configure(development=True, cwd=target, permission_mode='workspace', privacy_acknowledged=True)
            client.start()
            client.ask_stream('Ce repertoire de QA est entierement invente. Cree uniquement claude-proof.txt contenant INVENTED_CLAUDE. '
                'Execute une commande Python qui verifie ce contenu. Aucun autre fichier, aucune suppression ou delegation.', [], lambda text: None)
            proof['claude_real_edit'] = (target / 'claude-proof.txt').read_text(encoding='utf-8').strip() == 'INVENTED_CLAUDE'
        finally:
            client.close()
    if '--public' in sys.argv:
        first = research(target, as_of=date.today().isoformat(), topic='card', identity='swsh1-1')
        second = research(target, as_of=date.today().isoformat(), topic='card', identity='swsh1-1', offline=True)
        proof['public_gets'] = first['gets']
        proof['public_facts_saved'] = first['added']
        proof['public_offline_reuse'] = second['gets'] == 0 and bool(second['facts'])
    (target / 'qa-result.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps(proof), flush=True)
    return 0 if proof.get('codex_real_edit') and proof.get('codex_real_test_exit_zero') else 2


if __name__ == '__main__':
    raise SystemExit(main())
