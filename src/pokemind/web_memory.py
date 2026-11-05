"""Local memory of what the coach found on the web (owner, 2026-11-03).

The coach looks in PokeMind first, searches the web only when something is missing or too old, then saves a
short factual summary here with its https sources and date, so a similar question is answered locally next
time. Public information only. A stored summary is content written from public pages, never an instruction,
and its date tells how fresh it is.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from contextlib import closing
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from pokemind import battle_batch

DB = 'data/local/web_memory.sqlite3'
MAX_NOTES = 2000
SCHEMA = """
CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, topic TEXT NOT NULL, topic_key TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL, sources TEXT NOT NULL, retrieved TEXT NOT NULL, digest TEXT NOT NULL);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(topic, summary, content='notes', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, topic, summary) VALUES (new.id, new.topic, new.summary); END;
CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, topic, summary) VALUES ('delete', old.id, old.topic, old.summary); END;
CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, topic, summary) VALUES ('delete', old.id, old.topic, old.summary);
    INSERT INTO notes_fts(rowid, topic, summary) VALUES (new.id, new.topic, new.summary); END;
"""
# Words that say nothing about the subject (accents already removed); a note must share the real ones.
STOPWORDS = frozenset('''les des une un la le de du et ou en au aux est sont pour par sur dans avec sans que qui
quoi quel quelle quels quelles comment pourquoi combien ce cette ces cet mon ma mes ton ta tes son sa ses notre
votre leur leurs je tu il elle on nous vous ils elles me te se ne pas plus moins tres tout tous toute toutes faire
fait peux peut veux dis donne moi toi stp svp the and for with what which how why are was can you your this that
from about pokemon tcg live deck decks carte cartes card cards jeu'''.split())
NOTE = ('Résumés écrits par le coach à partir de pages web publiques; vérifier la date (retrieved) '
        'avant de s’y fier pour la méta, les annonces ou les nouvelles extensions.')


def _key(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().casefold()
    return ' '.join(re.findall(r'[a-z0-9]+', value))


def _sources(value):
    """https links only, without credentials; at most 10."""
    found = []
    for candidate in re.split(r'[\s,;]+', str(value or '')):
        candidate = candidate.strip('<>()[]"\'').rstrip('.')
        if not candidate:
            continue
        try:
            parts = urlsplit(candidate)
        except ValueError:
            continue
        if (parts.scheme == 'https' and parts.hostname and not parts.username and not parts.password
                and len(candidate) <= 500 and candidate not in found):
            found.append(candidate)
    return found[:10]


def _path(root, *, exists):
    return battle_batch.safe_path(root, Path(root) / DB, expected=DB, exists=exists)


def _connect(path):
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def remember(root, topic, summary, sources, *, as_of=None):
    """Save or refresh one note; the same topic replaces its older summary."""
    topic, summary = str(topic or '').strip(), str(summary or '').strip()
    links = _sources(sources)
    if not 3 <= len(topic) <= 300 or not _key(topic):
        return {'error': 'WEB_MEMORY_TOPIC_INVALID', 'hint': 'query = sujet court (3 à 300 caractères).'}
    if not 20 <= len(summary) <= 4000:
        return {'error': 'WEB_MEMORY_SUMMARY_INVALID', 'hint': 'summary = faits utiles avec dates (20 à 4000 caractères).'}
    if not links:
        return {'error': 'WEB_MEMORY_SOURCES_REQUIRED', 'hint': 'sources = URLs https consultées, séparées par des espaces.'}
    retrieved = as_of or date.today().isoformat()
    path = _path(root, exists=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(json.dumps([summary, links], ensure_ascii=False).encode()).hexdigest()
    with closing(_connect(path)) as connection, connection:
        row = connection.execute('SELECT id, digest FROM notes WHERE topic_key = ?', (_key(topic),)).fetchone()
        if row and row['digest'] == digest:
            connection.execute('UPDATE notes SET retrieved = ? WHERE id = ?', (retrieved, row['id']))
            status, identity = 'ALREADY_KNOWN', row['id']
        elif row:
            connection.execute('UPDATE notes SET topic = ?, summary = ?, sources = ?, retrieved = ?, digest = ? WHERE id = ?',
                               (topic, summary, json.dumps(links), retrieved, digest, row['id']))
            status, identity = 'UPDATED', row['id']
        else:
            identity = connection.execute(
                'INSERT INTO notes(topic, topic_key, summary, sources, retrieved, digest) VALUES (?, ?, ?, ?, ?, ?)',
                (topic, _key(topic), summary, json.dumps(links), retrieved, digest)).lastrowid
            status = 'SAVED'
        connection.execute('DELETE FROM notes WHERE id IN (SELECT id FROM notes ORDER BY retrieved DESC, id DESC '
                           'LIMIT -1 OFFSET ?)', (MAX_NOTES,))
    return {'status': status, 'id': identity, 'topic': topic, 'retrieved': retrieved, 'sources': links,
            'source': 'PokeMind · mémoire web locale'}


def search(root, query, *, limit=5, as_of=None):
    """Notes matching the question's words, best first; never creates the database."""
    path = Path(root) / DB
    words = [w for w in dict.fromkeys(_key(str(query or '')).split()) if len(w) >= 3 and w not in STOPWORDS][:12]
    # A plural or feminine ending still finds the note (« copies » → copie*).
    stems = [w[:-1] if len(w) > 4 and w[-1] in 'sxe' else w for w in words]
    if not stems or not path.is_file():
        return {'status': 'NONE', 'notes': [], 'source': 'PokeMind · mémoire web locale'}
    today = date.fromisoformat(as_of) if as_of else date.today()
    limit = max(1, min(int(limit), 10))
    with closing(_connect(_path(root, exists=True))) as connection:
        rows = connection.execute(
            'SELECT n.topic, n.summary, n.sources, n.retrieved FROM notes_fts f JOIN notes n ON n.id = f.rowid '
            'WHERE notes_fts MATCH ? ORDER BY bm25(notes_fts) LIMIT ?',
            (' OR '.join(stem + '*' for stem in stems), limit * 4)).fetchall()
    needed = max(1, (len(stems) + 1) // 2)  # at least half of the question's real words
    notes = []
    for row in rows:
        tokens = set(_key(row['topic'] + ' ' + row['summary']).split())
        if sum(any(token.startswith(stem) for token in tokens) for stem in stems) < needed or len(notes) >= limit:
            continue
        try:
            age = (today - date.fromisoformat(row['retrieved'])).days
        except ValueError:
            age = None
        notes.append({'topic': row['topic'], 'summary': row['summary'], 'sources': json.loads(row['sources']),
                      'retrieved': row['retrieved'], 'age_days': age})
    return {'status': 'FOUND' if notes else 'NONE', 'notes': notes, 'source': 'PokeMind · mémoire web locale',
            'note': NOTE}
