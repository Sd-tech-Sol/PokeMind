"""Invented PNG and HTTP metadata only; no CDN on CI."""
import base64
import json
from pathlib import Path

import pytest
from urllib.error import HTTPError

from pokemind.desktop.images import ImageCache

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jFyoAAAAASUVORK5CYII=')


class Reply:
    status=200
    def __init__(self,url,raw):self.url,self.raw=url,raw
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def geturl(self):return self.url
    def read(self,n):return self.raw[:n]


class HTTP:
    def __init__(self,base='https://assets.tcgdex.net/en/invented/test/1',raw=PNG):
        self.calls,self.base,self.raw=[],base,raw
    def open(self,request,timeout):
        self.calls.append(request.full_url)
        body=json.dumps({'id':'invented-1','image':self.base}).encode() if request.full_url.startswith('https://api.') else self.raw
        return Reply(request.full_url,body)


def test_real_cache_roundtrip_provenance_and_offline_reuse(local_tmp,monkeypatch):
    monkeypatch.delenv('POKEMIND_TEST_OFFLINE',raising=False)
    http=HTTP();cache=ImageCache(local_tmp,http)
    result=cache.fetch('invented-1','en')
    assert result['data']==PNG and not result['cached'] and len(http.calls)==2
    assert result['terms_url']=='https://tcgdex.dev/assets' and 'Pokémon' in result['notice']
    monkeypatch.setenv('POKEMIND_TEST_OFFLINE','1')
    again=ImageCache(local_tmp,http).fetch('invented-1','en')
    assert again['data']==PNG and again['cached'] and len(http.calls)==2


@pytest.mark.parametrize('base',['file:///private','https://evil.invalid/en/card',
    'https://assets.tcgdex.net.evil.invalid/en/card','https://assets.tcgdex.net/en/../private',
    'https://user:secret@assets.tcgdex.net/en/card','https://assets.tcgdex.net/en/card?private=1'])
def test_image_origins_and_urls_are_closed(local_tmp,monkeypatch,base):
    monkeypatch.delenv('POKEMIND_TEST_OFFLINE',raising=False)
    http=HTTP(base);cache=ImageCache(local_tmp,http)
    assert cache.fetch('invented-1','en')['status']=='UNAVAILABLE'
    assert len(http.calls)==1 and not list(cache.folder.glob('*.png'))


def test_not_permitted_or_unknown_printing_never_fetches(local_tmp):
    http=HTTP();cache=ImageCache(local_tmp,http)
    for identity,permitted in [(None,True),('../private',True),('invented-1',False)]:
        assert cache.fetch(identity,permitted=permitted)['status']=='UNAVAILABLE_OR_NOT_PERMITTED'
    assert not http.calls


def test_invalid_png_is_not_cached_and_session_retry_is_not_automatic(local_tmp,monkeypatch):
    monkeypatch.delenv('POKEMIND_TEST_OFFLINE',raising=False)
    http=HTTP(raw=b'<script>invented</script>');cache=ImageCache(local_tmp,http)
    assert cache.fetch('invented-1','en')['status']=='UNAVAILABLE'
    assert cache.fetch('invented-1','en')['status']=='UNAVAILABLE'
    assert len(http.calls)==2 and not list(cache.folder.glob('*.png'))


def test_cache_tampering_is_not_overwritten(local_tmp,monkeypatch):
    monkeypatch.delenv('POKEMIND_TEST_OFFLINE',raising=False)
    cache=ImageCache(local_tmp,HTTP());cache.fetch('invented-1','en')
    image=next(cache.folder.glob('*.png'));image.write_bytes(b'invented tampered owner file')
    assert cache.fetch('invented-1','en')['status']=='UNAVAILABLE'
    assert image.read_bytes()==b'invented tampered owner file'


def test_source_refusal_closes_automatic_network_attempts(local_tmp,monkeypatch):
    monkeypatch.delenv('POKEMIND_TEST_OFFLINE',raising=False)
    class Refused:
        calls=0
        def open(self,request,timeout):
            self.calls+=1
            raise HTTPError(request.full_url,429,'invented refusal',{},None)
    source=Refused();cache=ImageCache(local_tmp,source)
    assert cache.fetch('invented-1')['status']=='UNAVAILABLE'
    assert cache.fetch('invented-2')['status']=='UNAVAILABLE' and source.calls==1
