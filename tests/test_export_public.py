import importlib.util
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/export_public.py'
AUTHOR = ('Invented Maintainer', 'maintainer@example.invalid')


def load():
    spec = importlib.util.spec_from_file_location('export_public', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd, *arguments):
    command = ['git', '-c', 'core.autocrlf=false', '-c', 'user.name=Old Invented Name', '-c', 'user.email=old@example.invalid']
    return subprocess.run(command + list(arguments), cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repository(tmp_path):
    source = tmp_path / 'source'
    (source / 'src').mkdir(parents=True)
    (source / 'data/local').mkdir(parents=True)
    (source / 'data/local/.gitkeep').write_bytes(b'')
    (source / 'README.md').write_bytes('# Inventé\r\nLine ending kept exactly.\r\n'.encode('utf-8'))
    (source / 'src/app.py').write_text('print("one")\n', encoding='utf-8')
    git(source, 'init', '-q', '-b', 'work')
    git(source, 'add', '-A')
    git(source, 'commit', '-q', '-m', 'first')
    (source / 'src/app.py').write_text('print("two")\n', encoding='utf-8')
    git(source, 'commit', '-q', '-am', 'second')
    return source


def test_export_is_one_commit_with_the_same_tree_and_the_chosen_author(repository, tmp_path):
    module = load()
    receipt = module.export(repository, tmp_path / 'public', *AUTHOR, terms=set(), message='PokeMind 1.0')
    output = tmp_path / 'public'
    assert receipt['status'] == 'EXPORTED' and receipt['commits'] == 1 and receipt['same_tree_as_head']
    assert receipt['pushed'] is False and git(output, 'remote') == ''
    assert git(output, 'log', '-1', '--format=%an <%ae> %s') == 'Invented Maintainer <maintainer@example.invalid> PokeMind 1.0'
    assert git(output, 'rev-parse', 'HEAD^{tree}') == git(repository, 'rev-parse', 'HEAD^{tree}')
    assert (output / 'README.md').read_bytes() == (repository / 'README.md').read_bytes()
    assert git(repository, 'rev-list', '--count', 'HEAD') == '2'


@pytest.mark.parametrize('relative,content,label', [
    ('data/local/battles.json', b'{}', 'private-path'),
    ('notes.sqlite3', b'invented', 'forbidden-file'),
    ('docs/path.md', b'Voir C:\\Users\\inventee\\Documents', 'personal-name'),
    ('docs/mail.md', b'contact: someone@' + b'gmail.com', 'personal_email'),  # split: the export scans itself
    ('docs/key.md', b'-----BEGIN ' + b'PRIVATE KEY-----', 'private_key'),  # split so the hygiene check passes
    ('docs/name.md', 'Écrit par INVENTEE Personne'.encode('utf-8'), 'personal-name'),
])
def test_private_content_is_refused_before_anything_is_written(repository, tmp_path, relative, content, label):
    module = load()
    target = repository / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    git(repository, 'add', '-f', relative)
    git(repository, 'commit', '-q', '-m', 'planted')
    with pytest.raises(module.ExportRefused, match=label + ':' + relative):
        module.export(repository, tmp_path / 'public', *AUTHOR, terms={'Inventée'})
    assert not (tmp_path / 'public').exists()


def test_the_chosen_public_author_may_carry_a_name_refused_otherwise(repository, tmp_path):
    module = load()
    (repository / 'LICENSE').write_text('Copyright (c) Inventée Personne\n', encoding='utf-8')
    git(repository, 'add', 'LICENSE')
    git(repository, 'commit', '-q', '-m', 'licence')
    with pytest.raises(module.ExportRefused, match='personal-name:LICENSE'):
        module.export(repository, tmp_path / 'refused', *AUTHOR, terms={'Inventée'})
    receipt = module.export(repository, tmp_path / 'public', 'Inventée Personne', 'personne@example.invalid', terms={'Inventée'})
    assert receipt['status'] == 'EXPORTED'


def test_dirty_tree_existing_output_and_output_inside_the_repository_are_refused(repository, tmp_path):
    module = load()
    (tmp_path / 'occupied').mkdir()
    with pytest.raises(module.ExportRefused, match='existe déjà'):
        module.export(repository, tmp_path / 'occupied', *AUTHOR, terms=set())
    with pytest.raises(module.ExportRefused, match='dans le dépôt'):
        module.export(repository, repository / 'public', *AUTHOR, terms=set())
    (repository / 'src/app.py').write_text('print("changed")\n', encoding='utf-8')
    with pytest.raises(module.ExportRefused, match='non validées'):
        module.export(repository, tmp_path / 'public', *AUTHOR, terms=set())
    assert not (tmp_path / 'public').exists()


def test_personal_terms_are_read_from_this_pc_and_never_stored(repository, monkeypatch):
    module = load()
    monkeypatch.setenv('USERNAME', 'invuser')
    subprocess.run(['git', 'config', 'user.name', 'Ab Inventé Longname'], cwd=repository, check=True)
    assert module.personal_terms(repository) == {'invuser', 'Inventé', 'Longname'}
