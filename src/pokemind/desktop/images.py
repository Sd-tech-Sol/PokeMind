"""Bounded TCGdex image cache, separate from catalog and all personal records."""
from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, quote
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import HTTPError

from pokemind.battle_batch import safe_path

TERMS = 'https://tcgdex.dev/assets'
NOTICE = 'Illustrations © Pokémon / Nintendo / Creatures / GAME FREAK. Affichage personnel local; aucune redistribution ni licence MIT des illustrations présumée.'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ImageCache:
    def __init__(self, root, opener=None):
        self.root = Path(root).absolute()
        self.folder = self.root / 'data/local/card-images'
        self.opener = opener or build_opener(ProxyHandler({}), NoRedirect())
        self.lock = threading.Lock()
        self.cancelled = threading.Event()
        self.failed, self.requests, self.bytes = set(), 0, 0
        self.source_closed = False

    def _get(self, url, maximum):
        if self.source_closed or self.cancelled.is_set() or os.environ.get('POKEMIND_TEST_OFFLINE') == '1':
            raise ValueError('IMAGE_OFFLINE')
        if self.requests >= 500 or self.bytes >= 100 * 1024 * 1024:
            raise ValueError('IMAGE_SESSION_BUDGET')
        self.requests += 1
        try:
            with self.opener.open(Request(url, headers={'User-Agent':'PokeMind-Desktop/0.9; local personal display', 'Accept-Encoding':'identity'}), timeout=6) as response:
                if getattr(response, 'status', 200) != 200 or response.geturl() != url:
                    raise ValueError('IMAGE_SOURCE_REFUSED')
                value = response.read(maximum + 1)
        except HTTPError as error:
            if error.code in {401,403,429} or error.code >= 500:
                self.source_closed = True
            raise
        except OSError:
            self.source_closed = True
            raise
        if len(value) > maximum:
            raise ValueError('IMAGE_SIZE_CAP')
        self.bytes += len(value)
        return value

    def _put(self, path, raw):
        safe_path(self.root, path, exists=False)
        temporary = self.folder / ('.image-' + uuid.uuid4().hex + '.tmp')
        with temporary.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if safe_path(self.root, path).stat().st_nlink != 1 or path.read_bytes() != raw:
                raise ValueError('IMAGE_CACHE_CONFLICT')
        temporary.unlink()

    @staticmethod
    def _png(raw):
        if len(raw) < 24 or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('IMAGE_PNG_REQUIRED')
        width, height = struct.unpack('>II', raw[16:24])
        if not (0 < width <= 4096 and 0 < height <= 4096):
            raise ValueError('IMAGE_DIMENSION_CAP')

    def fetch(self, identity, language='fr', *, permitted=True):
        if not permitted or not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,90}', identity) or '..' in identity:
            return {'status':'UNAVAILABLE_OR_NOT_PERMITTED'}
        if language not in {'fr','en'}:
            language = 'fr'
        with self.lock:
            for lang in dict.fromkeys((language, 'en')):
                key = hashlib.sha256((lang + ':' + identity).encode()).hexdigest()
                safe_path(self.root, self.folder, exists=False).mkdir(parents=True, exist_ok=True)
                path, manifest = self.folder / (key + '.png'), self.folder / (key + '.json')
                try:
                    if path.exists() and manifest.exists():
                        safe_path(self.root, path); safe_path(self.root, manifest)
                        if path.stat().st_nlink != 1 or manifest.stat().st_nlink != 1 or path.stat().st_size > 4*1024*1024 or manifest.stat().st_size > 16000:
                            raise ValueError('IMAGE_CACHE_REFUSED')
                        metadata = json.loads(manifest.read_text(encoding='utf-8'))
                        source = urlsplit(metadata['source_url'])
                        if (metadata.get('tcgdex_id') != identity or metadata.get('language') != lang
                                or metadata.get('terms_url') != TERMS
                                or metadata.get('card_source_url') != 'https://api.tcgdex.net/v2/'+lang+'/cards/'+quote(identity,safe='')
                                or source.scheme != 'https' or source.netloc != 'assets.tcgdex.net'
                                or source.query or source.fragment or '..' in source.path
                                or not source.path.startswith('/'+lang+'/') or not source.path.endswith('/low.png')):
                            raise ValueError('IMAGE_CACHE_PROVENANCE_REFUSED')
                        raw = path.read_bytes()
                        self._png(raw)
                        if hashlib.sha256(raw).hexdigest() != metadata['image_sha256']:
                            raise ValueError('IMAGE_CACHE_CORRUPT')
                        return metadata | {'data':raw,'cached':True,'status':'OK'}
                    if key in self.failed or self.cancelled.is_set():
                        continue
                    source = 'https://api.tcgdex.net/v2/' + lang + '/cards/' + quote(identity, safe='')
                    info = json.loads(self._get(source, 2*1024*1024))
                    base = info.get('image', '')
                    parsed = urlsplit(base)
                    if (info.get('id') != identity or parsed.scheme != 'https' or parsed.netloc != 'assets.tcgdex.net'
                            or parsed.query or parsed.fragment or '..' in parsed.path or not parsed.path.startswith('/'+lang+'/')
                            or not re.fullmatch(r'/[A-Za-z0-9_./-]+', parsed.path)):
                        raise ValueError('IMAGE_SOURCE_NOT_ALLOWED')
                    url = base.rstrip('/') + '/low.png'
                    raw = self._get(url, 4*1024*1024)
                    self._png(raw)
                    metadata = {'source_url':url,'card_source_url':source,'terms_url':TERMS,'notice':NOTICE,
                        'retrieved_at':datetime.now(timezone.utc).isoformat(), 'language':lang,
                        'image_sha256':hashlib.sha256(raw).hexdigest(),'tcgdex_id':identity}
                    self._put(path, raw)
                    self._put(manifest, json.dumps(metadata,sort_keys=True).encode())
                    return metadata | {'data':raw,'cached':False,'status':'OK'}
                except (OSError, ValueError, KeyError, TypeError):
                    self.failed.add(key)
            return {'status':'UNAVAILABLE','notice':NOTICE}
