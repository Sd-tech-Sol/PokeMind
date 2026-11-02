"""Local ingress boundary. Raw battle text never becomes an assistant prompt."""
from __future__ import annotations

import hashlib
import os
import re
import threading
import uuid
from contextlib import contextmanager, closing
from pathlib import Path
from datetime import date

from pokemind import battle_batch as batch, battle_coach as coach, battle_logs as logs
from pokemind.database import connect_readonly

_MUTEX = threading.RLock()


def match_index(root):
    """Private lookup over the validated immutable snapshot, never cloud context."""
    folder = Path(root) / coach.REPORT_DIR
    if not folder.exists():
        return {}
    path, _ = coach._discover(root, folder)
    if path is None:
        return {}
    from pokemind import legacy_bridge
    value, _ = legacy_bridge._json(root, path)
    if path.name != 'analysis-' + batch.digest(value) + '.json':
        raise ValueError('INGEST_SNAPSHOT_CHANGED')
    return {m['semantic_identity']:m['match'] for m in value['matches'] if m.get('semantic_identity')}


def folder_revision(root, cancelled=None):
    """Private content fingerprint, not statistics or a second factual store."""
    folder = Path(root) / coach.LOG_DIR
    paths, refused, _ = batch.files_in_folder(root, folder)
    if refused:
        raise ValueError('INGEST_HISTORY_UNREADABLE')
    rows = []
    for path in paths:
        if cancelled and cancelled():
            raise ValueError('DESKTOP_CANCELLED')
        value, _ = batch.read_selected(folder, path)
        rows.append((str(path.relative_to(folder)), hashlib.sha256(value.encode()).hexdigest()))
    references = []
    for relative in batch.SCOPED_PUBLIC_CACHES:
        path = Path(root) / relative
        if path.exists():
            batch.safe_path(root, path)
            info = path.stat()
            references.append((relative, info.st_size, info.st_mtime_ns))
    return batch.digest({'logs':rows,'references':references,'as_of':date.today().isoformat(),
                         'engine':batch.VERSION,'parser':logs.PARSER_VERSION,
                         'ingress':'desktop-ingress-v1','complete_only':True})


def refresh(root, *, cancelled=None, progress=None, player=None, locked=False):
    """Validate freshness before invoking the single existing analysis engine."""
    root = Path(root).absolute()
    folder, _ = coach._directory(root, coach.LOG_DIR)
    if not locked:
        with _MUTEX, exclusive(root, folder):
            return refresh(root, cancelled=cancelled, progress=progress, player=player, locked=True)
    target, _ = coach._directory(root, coach.REPORT_DIR)
    fingerprint = folder_revision(root, cancelled)
    control = target / 'desktop-refresh.json'
    remembered, stamp = coach._control(root, control)
    selected, _ = coach._discover(root, target)
    if selected and remembered == {'schema_version':1,'fingerprint':fingerprint,'snapshot':selected.name}:
        result = coach.coach(root, player=player, cancelled=cancelled)
        return result | {'refresh_no_changes':True}
    result = coach.coach(root, player=player, update=True, complete_only=True,
                         cancelled=cancelled, progress=progress)
    if result.get('report') and folder_revision(root, cancelled) == fingerprint:
        selected, _ = coach._discover(root, target)
        pointer, _ = coach._control(root, target / 'latest.json')
        if selected and pointer and pointer.get('snapshot') == selected.name:
            coach._atomic_control(root, control, {'schema_version':1,'fingerprint':fingerprint,'snapshot':selected.name}, stamp)
    return result | {'refresh_no_changes':False}


def classify(text):
    """Cheap bounded routing only; acceptance always requires the real parser."""
    lines = text.splitlines()
    turns = any(logs._match_turn(line.strip()) or logs._match_unnumbered_turn(line.strip()) for line in lines)
    reference = any(p.match(line.strip()) for line in lines for p in logs.REFERENCE_PATTERNS)
    if turns or reference:
        return 'log'
    actions = any(logs._event_from_line(line.strip(), 1, None) for line in lines if line.strip())
    setup = any(re.fullmatch(r'(?:Setup|Préparation|Fin de partie)\s*:?', line.strip(), re.I) for line in lines)
    if actions or setup or '\x00' in text or (len(lines) > 3 and re.search(r'(?:Pokémon TCG Live|Pok.mon TCG Live|main de départ|opening hand)', text, re.I)):
        return 'ambiguous'
    return 'question'


def split_message(text):
    """Split outside a parser-recognized log, without asking a hosted model.

    Only explicit question/request lines before setup or after a recognized
    winner are extracted. Ambiguous text remains local for validation.
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if re.fullmatch(
        r'(?:Setup|Préparation|Mise en place)\s*:?', line.strip(), re.I)
        or any(p.match(line.strip()) for p in logs.REFERENCE_PATTERNS)]
    ends = [i for i, line in enumerate(lines) if any(p.match(line.strip()) for p in logs.WIN_PATTERNS)]
    request = re.compile(r'^(?:[/?]|pourquoi\b|comment\b|reconstrui\w*\b|analys\w*\b|compar\w*\b|explique\b|why\b|reconstruct\b|analy[sz]\w*\b|compare\b)', re.I)
    def owner_text(chunk):
        # What the owner typed around the log, unless a line reads like a log event.
        return all(not line.strip() or request.match(line.strip()) or not (
            logs._match_turn(line.strip()) or logs._match_unnumbered_turn(line.strip())
            or logs._event_from_line(line.strip(), 1, None)) for line in chunk)
    before, after = [], []
    start = min(starts) if starts else 0
    if start and owner_text(lines[:start]):
        before = lines[:start]
    else:
        start = 0
    end = ends[-1] + 1 if ends else len(lines)
    if end < len(lines) and owner_text(lines[end:]):
        after = lines[end:]
    else:
        end = len(lines)
    return '\n'.join(lines[start:end]), '\n'.join(before + after).strip()


def configured_player(root):
    target = Path(root) / coach.REPORT_DIR
    if not target.exists():
        return None
    value, stamp = coach._control(root, target / 'coach-settings.json')
    if value is None:
        if stamp is not None:
            raise ValueError('INGEST_PLAYER_SETTINGS_INVALID')
        return None
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise ValueError('INGEST_PLAYER_SETTINGS_INVALID')
    return coach._player(value.get('player'))


def validate(text, player=None):
    if not isinstance(text, str) or len(text.encode('utf-8')) > logs.MAX_LOG_BYTES:
        return None, ['Journal trop volumineux : limite de 2 Mo par partie.']
    if '\x00' in text:
        return None, ['Le contenu ne correspond pas à un journal texte.']
    try:
        parsed = batch.parse_selected(text, player)
    except ValueError:
        return None, ['Joueur ou participants non résolus, ou plusieurs parties concaténées.']
    reasons = []
    if not parsed.reference_player or not parsed.opponent_name:
        reasons.append('Les deux participants et le joueur de référence doivent être reconnus.')
    if not parsed.max_turn or parsed.max_turn < 1:
        reasons.append('Aucun tour de jeu fiable reconnu.')
    if parsed.outcome not in {'W', 'L'} or not parsed.winner:
        reasons.append('Résultat final absent ou contradictoire : aucune partie comptabilisée.')
    if len({logs._name_key(n) for n in [parsed.reference_player, parsed.opponent_name] if n}) != 2:
        reasons.append('Deux participants distincts sont requis.')
    if any(len(n) > 100 or any(not c.isprintable() for c in n) for n in (parsed.reference_player, parsed.opponent_name) if n):
        reasons.append('Identité de participant invalide.')
    if any('contradictoire' in warning for warning in parsed.warnings):
        reasons.append('Le journal contient des identités ou résultats contradictoires.')
    return (None, reasons) if reasons else (parsed, [])


@contextmanager
def exclusive(root, folder):
    """Serialize publication and batch refresh across processes; no stale-lock purge."""
    lock = batch.safe_path(root, folder / '.pokemind-ingest.lock', exists=False)
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError('INGEST_BUSY_RETRY') from None
    stamp = os.fstat(descriptor)
    try:
        yield
    finally:
        os.close(descriptor)
        current = batch.safe_path(root, lock).stat()
        if (current.st_dev, current.st_ino, current.st_nlink) == (stamp.st_dev, stamp.st_ino, 1):
            lock.unlink()  # Only this invocation's new lock, never a battle log.


def _publish(root, folder, raw):
    pending = batch.safe_path(root, folder / '.pending', exists=False)
    pending.mkdir(exist_ok=True)
    identity = uuid.uuid4().hex
    staged = batch.safe_path(root, pending / (identity + '.tmp'), exists=False)
    destination = batch.safe_path(root, folder / ('pokemind-' + identity + '.log'), exists=False)
    with staged.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    batch.safe_path(root, destination, exists=False)
    os.link(staged, destination)  # Atomic exclusive publication; never replace.
    if not os.path.samestat(staged.stat(), destination.stat()):
        raise ValueError('INGEST_PUBLICATION_REVIEW_REQUIRED')
    staged.unlink()  # Drop our staging alias after publication, final log remains.
    return destination


def ingest(root, text, *, report=None, cancelled=None, notify=lambda value: None):
    root = Path(root).absolute()
    if isinstance(text, str):
        text = text.lstrip('\ufeff')
    player = configured_player(root)
    parsed, reasons = validate(text, player)
    if parsed is None:
        return {'status': 'REFUSED', 'reasons': reasons, 'new_unique': 0, 'stats_updated': False}
    notify('Journal reconnu · validation locale réussie')
    identity = batch.digest(batch.semantic_text(text))
    equivalent = batch.equivalent_text_key(text)
    raw = text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')
    raw_digest = hashlib.sha256(raw).hexdigest()
    if cancelled and cancelled():
        raise ValueError('DESKTOP_CANCELLED')
    with _MUTEX:
        folder, _ = coach._directory(root, coach.LOG_DIR)
        with exclusive(root, folder):
            duplicate = any(m.get('semantic_identity') == identity for m in (report or {}).get('matches', []))
            files, refused, _ = batch.files_in_folder(root, folder)
            # An unreadable historical input cannot silently certify uniqueness.
            if refused:
                raise ValueError('INGEST_HISTORY_UNREADABLE')
            for path in files:
                if cancelled and cancelled():
                    raise ValueError('DESKTOP_CANCELLED')
                existing, _ = batch.read_selected(folder, path)
                for piece in batch.segments(existing):
                    if batch.equivalent_text_key(piece) == equivalent:
                        duplicate = True
                        identity = batch.digest(batch.semantic_text(piece))
                        break
                if duplicate:
                    break
            db = root / coach.DB
            if db.is_file():
                batch.safe_path(root, db)
                if db.stat().st_nlink != 1:
                    raise ValueError('INGEST_DATABASE_ALIAS_REFUSED')
                with closing(connect_readonly(db)) as connection:
                    if connection.execute("SELECT 1 FROM sqlite_master WHERE name='battle_logs'").fetchone():
                        duplicate |= connection.execute('SELECT 1 FROM battle_logs WHERE source_sha256=?', (raw_digest,)).fetchone() is not None
            if cancelled and cancelled():
                raise ValueError('DESKTOP_CANCELLED')
            if not duplicate:
                notify('Enregistrement en cours · fichier local atomique')
                _publish(root, folder, raw)
            else:
                notify('Doublon détecté · journal existant conservé')
            notify('Actualisation des analyses locales et du Learning Loop')
            # Persist the parser-confirmed owner once, without guessing a deck version.
            try:
                result = refresh(root, player=player or parsed.reference_player,
                                 cancelled=cancelled, locked=True)
            except (OSError, ValueError):
                return {'status': 'DUPLICATE' if duplicate else 'SAVED_REFRESH_PENDING',
                    'new_unique': 0, 'stats_updated': False, 'outcome': parsed.outcome,
                    'opponent': parsed.opponent_name, 'reasons': ['Analyse non terminée; fichier conservé, relancer Actualiser.']}
            current = result.get('report') or {}
            identities = match_index(root)
            found = next((m for m in current.get('matches', []) if m.get('match') == identities.get(identity)), None)
            return {'status': 'DUPLICATE' if duplicate else 'SAVED', 'new_unique': int(not duplicate and found is not None),
                'stats_updated': bool(current), 'outcome': parsed.outcome, 'opponent': parsed.opponent_name,
                'match': found, 'result': result if current else None, 'semantic_identity': identity,
                'local_match_index': identities,
                'reasons': [] if current else ['Partie historique reconnue; aucun rapport analytique disponible pour cette entrée.']}


def read_attachment(root, path):
    """Read one explicitly selected file; never discover siblings or write there."""
    path = Path(path).absolute()
    if str(path).startswith(('\\\\', '//')):
        raise ValueError('INGEST_LOCAL_ATTACHMENT_REQUIRED')
    anchor = Path(root).absolute() if path.is_relative_to(Path(root).absolute()) else path.parent
    path = batch.safe_path(anchor, path)
    if path.suffix.casefold() not in {'.txt', '.log'} or not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError('INGEST_ATTACHMENT_REFUSED')
    before = path.stat()
    if before.st_size > logs.MAX_LOG_BYTES:
        raise ValueError('INGEST_ATTACHMENT_SIZE_CAP')
    with path.open('rb') as stream:
        raw = stream.read(logs.MAX_LOG_BYTES + 1)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('INGEST_ATTACHMENT_CHANGED')
    return logs.decode_log_bytes(raw)[0]
