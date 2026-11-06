"""Card updates from the app: invented TCGdex versions only, never the network."""
import io
import json

import pytest

from pokemind import catalog_download, catalog_update
from pokemind.cards import browse_cards
from test_catalog_download import FILES, archive, tree

NEWER = 'c' * 40
NEW_SET = {
    'data/Test/Delta.ts': "import serie from '../Test'; const set: Set = {id:'dlt',name:{en:'Invented Delta',fr:'Delta inventé'},"
                          "serie:serie,cardCount:{official:1}}; export default set",
    'data/Test/Delta/1.ts': "import set from '../Delta'; const card: Card = {set:set,name:{en:'Invented Delta Flame',"
                            "fr:'Flamme delta inventée'},category:'Pokemon',hp:120}; export default card",
}


def tcgdex(newest=NEWER, newer_files=None, calls=None, sets=None):
    """A fake TCGdex: the pinned commit, a newer one, the newest commit id and the API set list."""
    files = {**FILES, **NEW_SET} if newer_files is None else newer_files
    newer_tree, newer_archive = catalog_download.urls(NEWER)

    def fetch(url):
        if calls is not None:
            calls.append(url)
        if url == catalog_download.LATEST_URL:
            return io.BytesIO(newest.encode())
        if url == catalog_download.TREE_URL:
            return io.BytesIO(tree())
        if url == catalog_download.ARCHIVE_URL:
            return io.BytesIO(archive())
        if url == newer_tree:
            return io.BytesIO(tree(files))
        if url == newer_archive:
            return io.BytesIO(archive(files, prefix='cards-database-' + NEWER + '/'))
        if url == catalog_update.SETS_URL:
            return io.BytesIO(json.dumps(sets if sets is not None else [
                {'id': 'inv', 'name': 'Invented', 'cardCount': {'total': 2}},
                {'id': 'dlt', 'name': 'Invented Delta', 'cardCount': {'total': 1}}]).encode())
        raise AssertionError('unexpected URL ' + url)
    return fetch


def names(root):
    db = catalog_download.campaign_folder(root) / 'public.sqlite3'
    return sorted(c['name'] for c in browse_cards(db, language='fr', offset=0, limit=20)['cards'])


def first_catalogue(root):
    assert catalog_download.download(root, fetch=tcgdex())['status'] == 'COMPLETE'  # the pinned one
    assert catalog_download.installed(root)['commit'] == catalog_download.COMMIT


def test_check_says_what_is_new_without_downloading_the_catalogue(local_tmp):
    assert catalog_update.check(local_tmp, fetch=tcgdex())['status'] == 'MISSING'
    first_catalogue(local_tmp)
    calls = []
    fake = tcgdex(calls=calls)
    result = catalog_update.check(local_tmp, fetch=fake, fetch_api=fake)
    assert result['status'] == 'AVAILABLE' and result['commit'] == NEWER and result['notable']
    assert result['new_sets'] == [{'id': 'dlt', 'name': 'Invented Delta', 'cards': 1}] and result['grown_sets'] == []
    assert calls == [catalog_download.LATEST_URL, catalog_update.SETS_URL]  # two small requests, no archive
    same = tcgdex(newest=catalog_download.COMMIT)
    assert catalog_update.check(local_tmp, fetch=same, fetch_api=same)['status'] == 'CURRENT'

    def no_api(url):
        raise OSError('offline')
    quiet = catalog_update.check(local_tmp, fetch=fake, fetch_api=no_api)
    assert quiet['status'] == 'AVAILABLE' and not quiet['notable'] and quiet['detail_error']


def test_only_new_sets_and_recent_sets_with_more_cards_are_news():
    sets = [{'id': 'old%d' % n, 'name': 'Old %d' % n, 'cardCount': {'total': 50}} for n in range(30)]
    sets += [{'id': 'recent', 'name': 'Recent', 'cardCount': {'total': 90}},
             {'id': 'brand', 'name': 'Brand new', 'cardCount': {'total': 33}}]
    counts = {**{'old%d' % n: 50 for n in range(30)}, 'old0': 40, 'recent': 33}  # an old special set counted differently
    new, grown = catalog_update.compare(sets, counts)
    assert new == [{'id': 'brand', 'name': 'Brand new', 'cards': 33}]
    assert grown == [{'id': 'recent', 'name': 'Recent', 'added': 57}]


def test_update_puts_the_newer_catalogue_in_place_and_keeps_the_previous_once(local_tmp):
    first_catalogue(local_tmp)
    phases = []
    result = catalog_update.update(local_tmp, fetch=tcgdex(), progress=lambda phase, done, total: phases.append(phase))
    assert result['status'] == 'UPDATED' and result['printings'] == 3 and phases[-1] == 'import'
    assert catalog_download.installed(local_tmp)['commit'] == NEWER
    assert 'Flamme delta inventée' in names(local_tmp)
    previous = local_tmp / 'data/local' / catalog_update.PREVIOUS / catalog_download.campaign_folder(local_tmp).name
    assert (previous / 'public.sqlite3').is_file()
    assert not list((local_tmp / 'data/local').glob(catalog_update.STAGING + '*'))
    assert catalog_update.update(local_tmp, fetch=tcgdex())['status'] == 'CURRENT'
    newest = 'd' * 40  # a third version: still exactly one previous catalogue
    newer_tree, newer_archive = catalog_download.urls(newest)
    files = {**FILES, **NEW_SET}

    def third(url):
        if url == catalog_download.LATEST_URL:
            return io.BytesIO(newest.encode())
        if url == newer_tree:
            return io.BytesIO(tree(files))
        if url == newer_archive:
            return io.BytesIO(archive(files, prefix='cards-database-' + newest + '/'))
        raise AssertionError(url)
    assert catalog_update.update(local_tmp, fetch=third)['status'] == 'UPDATED'
    kept = list((local_tmp / 'data/local' / catalog_update.PREVIOUS).iterdir())
    assert len(kept) == 1 and not list((local_tmp / 'data/local').glob(catalog_update.PREVIOUS + '.old-*'))


def test_a_catalogue_in_use_is_replaced_at_the_next_launch(local_tmp, monkeypatch):
    first_catalogue(local_tmp)
    real = catalog_update._move
    target = catalog_download.campaign_folder(local_tmp)
    monkeypatch.setattr(catalog_update, '_move',
                        lambda source, dest, attempts, wait: False if source == target else real(source, dest, attempts, wait))
    result = catalog_update.update(local_tmp, fetch=tcgdex(), attempts=1, wait=0)
    assert result['status'] == 'READY_NEXT_LAUNCH'
    assert catalog_download.installed(local_tmp)['commit'] == catalog_download.COMMIT  # still the one in use
    monkeypatch.setattr(catalog_update, '_move', real)
    unfinished = local_tmp / 'data/local' / (catalog_update.STAGING + '20000101-000000')
    unfinished.mkdir()
    assert catalog_update.apply_pending(local_tmp)['status'] == 'UPDATED'
    assert catalog_download.installed(local_tmp)['commit'] == NEWER and not unfinished.exists()
    assert catalog_update.apply_pending(local_tmp) is None


def test_a_smaller_or_broken_newer_catalogue_never_replaces_the_one_in_use(local_tmp):
    first_catalogue(local_tmp)
    smaller = {k: v for k, v in FILES.items() if k != 'data/Test/Invented/2.ts'}
    result = catalog_update.update(local_tmp, fetch=tcgdex(newer_files=smaller))
    assert result['status'] == 'STOPPED' and result['error'] == 'CATALOG_UPDATE_SMALLER'
    broken = {**FILES, 'data/Test/Invented/2.ts': 'not a card'}
    assert catalog_update.update(local_tmp, fetch=tcgdex(newer_files=broken))['status'] == 'STOPPED'
    assert catalog_download.installed(local_tmp)['commit'] == catalog_download.COMMIT
    assert not list((local_tmp / 'data/local').glob(catalog_update.STAGING + '*'))
    assert not (local_tmp / 'data/local' / catalog_update.PREVIOUS).exists()


def test_the_first_catalogue_takes_the_newest_version_or_falls_back_to_the_tested_one(local_tmp):
    newest = catalog_download.download(local_tmp, latest=True, fetch=tcgdex())
    assert newest['status'] == 'COMPLETE' and newest['commit'] == NEWER and 'Flamme delta inventée' in names(local_tmp)
    other = local_tmp / 'autre'
    broken = {**FILES, 'data/Test/Invented/2.ts': 'not a card'}
    fallback = catalog_download.download(other, latest=True, fetch=tcgdex(newer_files=broken))
    assert fallback['status'] == 'COMPLETE' and fallback['commit'] == catalog_download.COMMIT
    assert catalog_download.state(other) == 'present'


@pytest.mark.parametrize('body', [b'not a commit', b'<html>', b'g' * 40])
def test_an_unreadable_newest_commit_is_refused(body):
    with pytest.raises(catalog_download.CatalogError, match='CATALOG_LATEST_COMMIT_INVALID'):
        catalog_download.latest_commit(lambda url: io.BytesIO(body))
