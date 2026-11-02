"""First catalogue download: an invented archive and tree, never the network."""
import hashlib
import io
import json
import tarfile

import pytest

from pokemind import catalog_download
from pokemind.cards import browse_cards
from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES

PREFIX = 'cards-database-' + catalog_download.COMMIT + '/'
FILES = {
    'LICENSE': 'MIT License\nInvented permission notice for a synthetic archive.',
    'meta/translations/fr.json': json.dumps({'category': {'Pokemon': 'Pokémon'}}),
    'data/Test.ts': "const serie: Serie = {id:'test',name:{en:'Test',fr:'Essai'}}; export default serie",
    'data/Test/Invented.ts': "import serie from '../Test'; const set: Set = {id:'inv',name:{en:'Invented',fr:'Inventé'},"
                             "serie:serie,cardCount:{official:2}}; export default set",
    'data/Test/Invented/1.ts': "import set from '../Invented'; const card: Card = {set:set,name:{en:'Invented Flame',"
                               "fr:'Flamme inventée'},category:'Pokemon',hp:90}; export default card",
    'data/Test/Invented/2.ts': "import set from '../Invented'; const card: Card = {set:set,name:{en:'Invented Tool'},"
                               "category:'Trainer'}; export default card",
}
EXTRA = {'README.md': 'Not part of the catalogue.', 'server/code.ts': 'never read'}


def blob(body):
    return hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()


def tree(files=FILES, truncated=False):
    entries = [{'path': name, 'type': 'blob', 'mode': '100644', 'sha': blob(text.encode()), 'size': len(text.encode())}
               for name, text in {**files, **EXTRA}.items()]
    return json.dumps({'sha': 'b' * 40, 'truncated': truncated, 'tree': entries}).encode()


def archive(files=FILES, prefix=PREFIX):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        folder = tarfile.TarInfo(prefix.rstrip('/'))
        folder.type = tarfile.DIRTYPE
        tar.addfile(folder)
        for name, text in {**files, **EXTRA}.items():
            body = text.encode()
            info = tarfile.TarInfo(prefix + name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
    return buffer.getvalue()


def fetcher(tree_body=None, archive_body=None, calls=None):
    def fetch(url):
        if calls is not None:
            calls.append(url)
        if url == catalog_download.TREE_URL:
            return io.BytesIO(tree() if tree_body is None else tree_body)
        if url == catalog_download.ARCHIVE_URL:
            return io.BytesIO(archive() if archive_body is None else archive_body)
        raise AssertionError('unexpected URL')
    return fetch


def test_download_imports_the_catalogue_where_the_app_reads_it_and_cleans_up(local_tmp):
    phases, calls = [], []
    receipt = catalog_download.download(local_tmp, fetch=fetcher(calls=calls),
                                        progress=lambda phase, done, total: phases.append(phase))
    assert receipt['status'] == 'COMPLETE' and receipt['printings'] == 2 and receipt['sets'] == 1
    assert calls == [catalog_download.TREE_URL, catalog_download.ARCHIVE_URL]
    assert phases[0] == 'download' and phases[-1] == 'import'
    db = local_tmp / SCOPED_PUBLIC_CACHES[1]
    assert db == catalog_download.campaign_folder(local_tmp) / 'public.sqlite3'
    assert catalog_download.state(local_tmp) == 'present'
    assert [c['name'] for c in browse_cards(db, language='fr', offset=0, limit=5)['cards']] == ['Flamme inventée']
    assert not list((local_tmp / 'data/local').glob('catalog-discovery-*'))  # temporary download removed
    again = catalog_download.download(local_tmp, fetch=lambda url: pytest.fail('a present catalogue is never fetched'))
    assert again == {'status': 'PRESENT', 'network_used': False}


@pytest.mark.parametrize('tree_body, archive_body, code', [
    (tree(truncated=True), None, 'CATALOG_DOWNLOAD_TREE_INCOMPLETE'),
    (None, archive({**FILES, 'data/Test.ts': FILES['data/Test.ts'].replace('Essai', 'Falsifié')}), 'CATALOG_DOWNLOAD_ARCHIVE_ENTRY_REJECTED'),
    (None, archive({**FILES, 'data/Test.ts': FILES['data/Test.ts'].replace('Test', 'Tset')}), 'CATALOG_DOWNLOAD_BLOB_MISMATCH'),
    (None, archive(prefix='cards-database-other/'), 'CATALOG_DOWNLOAD_ARCHIVE_ROOT_REJECTED'),
    (None, archive({k: v for k, v in FILES.items() if k != 'LICENSE'}), 'CATALOG_DOWNLOAD_ARCHIVE_INCOMPLETE'),
])
def test_a_tampered_or_incomplete_source_stops_before_any_catalogue_exists(local_tmp, tree_body, archive_body, code):
    receipt = catalog_download.download(local_tmp, fetch=fetcher(tree_body, archive_body))
    assert receipt['status'] == 'STOPPED' and receipt['error'] == code
    assert catalog_download.state(local_tmp) == 'missing'
    assert not list((local_tmp / 'data/local').glob('catalog-discovery-*'))


def test_cancelling_stops_the_download_and_a_cut_short_import_is_set_aside(local_tmp):
    receipt = catalog_download.download(local_tmp, fetch=fetcher(), cancelled=lambda: True)
    assert receipt['error'] == 'CATALOG_DOWNLOAD_CANCELLED' and catalog_download.state(local_tmp) == 'missing'
    folder = catalog_download.campaign_folder(local_tmp)
    folder.mkdir(parents=True)
    (folder / 'snapshot-report.json').write_text(json.dumps({'status': 'IN_PROGRESS'}), encoding='utf-8')
    leftover = local_tmp / 'data/local/catalog-discovery-app-20261101-120000'
    leftover.mkdir()
    keep = local_tmp / 'data/local/catalog-discovery-owner'
    keep.mkdir()
    assert catalog_download.state(local_tmp) == 'stopped'
    assert catalog_download.download(local_tmp, fetch=fetcher())['status'] == 'COMPLETE'
    aside = list((local_tmp / 'data/local/public-campaigns').glob('stopped-catalog-*'))
    assert len(aside) == 1 and (aside[0] / 'snapshot-report.json').is_file()  # never deleted
    assert not leftover.exists() and keep.is_dir()


def test_an_existing_catalogue_with_another_report_is_never_replaced(local_tmp):
    folder = catalog_download.campaign_folder(local_tmp)
    folder.mkdir(parents=True)
    (folder / 'public.sqlite3').write_bytes(b'')
    (folder / 'snapshot-report.json').write_text(json.dumps({'status': 'ENRICHED_ELSEWHERE'}), encoding='utf-8')
    assert catalog_download.ready(local_tmp)
    assert catalog_download.download(local_tmp, fetch=lambda url: pytest.fail('no network'))['status'] == 'PRESENT'


def test_only_github_https_sources_are_opened():
    with pytest.raises(catalog_download.CatalogError, match='CATALOG_DOWNLOAD_URL_REFUSED'):
        catalog_download._open('http://example.invalid/archive.tar.gz')
