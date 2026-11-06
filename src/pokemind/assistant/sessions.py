"""Private chat/UI preferences. No auth tokens and no second factual database."""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

from pokemind import battle_batch, legacy_bridge

DEFAULTS = {'provider': 'codex', 'theme': 'dark', 'cloud_consent': False,
            'sharing': 'public', 'ollama_model': '', 'current': None, 'conversations': [],
            'startup_refresh': False, 'card_images': True, 'watch_logs': False,
            'permission_mode': 'workspace', 'project_relative': '.', 'language': None,
            'development_privacy_acknowledgements': [], 'reduced_motion': False,
            'favorite_decks': [], 'sidebar_collapsed': False, 'chat_project': True, 'season_view': 'current',
            'update_check': True}


def system_language():
    """'fr' when Windows (or the environment) speaks French, else 'en': the first-run language."""
    if os.name == 'nt':
        try:
            import ctypes
            return 'fr' if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x0C else 'en'
        except (AttributeError, OSError):
            pass
    import locale
    name = (locale.getlocale()[0] or os.environ.get('LANG') or '').casefold()
    return 'fr' if name.startswith(('fr', 'french')) else 'en'


class Store:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.folder = battle_batch.safe_path(self.root, self.root / 'data/local/chat', exists=False)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.sandbox = self.folder / 'sandbox'
        battle_batch.safe_path(self.root, self.sandbox, exists=False).mkdir(exist_ok=True)

    def path(self, name):
        if not re.fullmatch(r'(?:preferences|conversation-[0-9a-f]{32})\.json', name):
            raise ValueError('CHAT_PATH_REFUSED')
        return battle_batch.safe_path(self.root, self.folder / name, exists=False)

    def read(self, name, default=None):
        path = self.path(name)
        if not path.exists():
            return default
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError('CHAT_HISTORY_SIZE_CAP')
        value, _ = legacy_bridge._json(self.root, path)
        return value

    def write(self, name, value):
        path = self.path(name)
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('CHAT_HISTORY_SIZE_CAP')
        stamp = legacy_bridge._stamp(path) if path.exists() else None
        if stamp and legacy_bridge._bytes(self.root, path, maximum=2*1024*1024)[0] == raw:
            return
        tmp = self.folder / ('.chat-' + uuid.uuid4().hex + '.tmp')
        with battle_batch.safe_path(self.root, tmp, exists=False).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.path(name)
        if (stamp is None and path.exists()) or (stamp is not None and legacy_bridge._stamp(path) != stamp):
            raise ValueError('CHAT_CONCURRENT_CHANGE')
        os.replace(tmp, path)

    def preferences(self):
        value = self.read('preferences.json', {})
        if not isinstance(value, dict):
            raise ValueError('CHAT_PREFERENCES_INVALID')
        result = DEFAULTS | value
        if result['language'] is None:  # never chosen: follow the system, English by default
            result['language'] = system_language()
        favorites = result['favorite_decks']
        if (not isinstance(favorites, list) or len(favorites) > 100
                or any(not isinstance(k, str) or not re.fullmatch('[0-9a-f]{64}', k) for k in favorites)
                or len(set(favorites)) != len(favorites)):
            raise ValueError('CHAT_PREFERENCES_INVALID')
        acknowledgements = result['development_privacy_acknowledgements']
        if (not isinstance(acknowledgements, list) or len(acknowledgements) > 100
                or any(not isinstance(k, str) or len(k) > 256 for k in acknowledgements)):
            raise ValueError('CHAT_PREFERENCES_INVALID')
        if (result['provider'] not in {'codex', 'claude', 'ollama'}
                or result['sharing'] not in {'public', 'aggregates'}
                or type(result['cloud_consent']) is not bool
                or result['permission_mode'] not in {'workspace', 'full'}
                or result['language'] not in {'fr', 'en'}
                or not isinstance(result['project_relative'], str) or len(result['project_relative']) > 160
                or result['theme'] not in {'dark', 'light'}
                or any(type(result[k]) is not bool for k in ('startup_refresh', 'card_images', 'watch_logs', 'reduced_motion', 'sidebar_collapsed', 'chat_project',
                                                     'update_check'))
                or not isinstance(result['conversations'], list) or len(result['conversations']) > 500
                or not isinstance(result['season_view'], str) or not re.fullmatch(r'current|all|before|\d{4}-\d{2}-\d{2}', result['season_view'])):
            raise ValueError('CHAT_PREFERENCES_INVALID')
        return result

    def new(self, provider):
        if provider not in {'codex', 'claude', 'ollama'}:
            raise ValueError('CHAT_PROVIDER_INVALID')
        return {'id': uuid.uuid4().hex, 'provider': provider, 'session': None,
                'title': 'Nouvelle discussion', 'messages': [], 'sessions': {}, 'channel': 'coach', 'tools_version': 2}

    @staticmethod
    def switch(conversation, provider, channel='coach'):
        if provider not in {'codex', 'claude', 'ollama'} or channel not in {
                'coach', 'development:workspace', 'development:full', 'project:workspace', 'project:full'}:
            raise ValueError('CHAT_CHANNEL_INVALID')
        sessions = conversation.setdefault('sessions', {})
        previous = conversation['provider'] + ':' + conversation.get('channel', 'coach')
        sessions[previous] = conversation.get('session')
        conversation.update(provider=provider, channel=channel, session=sessions.get(provider + ':' + channel))

    def save(self, conversation):
        self.write('conversation-' + conversation['id'] + '.json', conversation)

    def delete(self, identity):
        """Erase one conversation file, on the owner's explicit request only."""
        if not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{32}', identity):
            raise ValueError('CHAT_ID_INVALID')
        path = self.path('conversation-' + identity + '.json')
        if not path.exists():
            return False
        path.unlink()
        return True

    def load(self, identity):
        if not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{32}', identity):
            raise ValueError('CHAT_ID_INVALID')
        value = self.read('conversation-' + identity + '.json')
        if (not isinstance(value, dict) or value.get('id') != identity
                or value.get('provider') not in {'codex', 'claude', 'ollama'}
                or not isinstance(value.get('messages'), list) or len(value['messages']) > 500):
            raise ValueError('CHAT_HISTORY_INVALID')
        for message in value['messages']:
            if (not isinstance(message, dict) or message.get('role') not in {'user', 'assistant'}
                    or not isinstance(message.get('content'), str)):
                raise ValueError('CHAT_HISTORY_INVALID')
        if value.get('tools_version') != 2:
            value['legacy_sessions'] = value.get('sessions', {}) | {value['provider']:value.get('session')}
            value.update(session=None, sessions={}, tools_version=2, provider_history_start=len(value['messages']))
        return value
