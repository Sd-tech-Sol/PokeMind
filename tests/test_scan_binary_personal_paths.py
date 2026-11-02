import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/scan_binary_personal_paths.py'


def load():
    spec = importlib.util.spec_from_file_location('scan_binary_personal_paths', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_account_name_and_paths_are_found_in_ascii_and_utf16_without_echoing_them(tmp_path):
    module = load()
    terms = {'account-name': 'InventedUser', 'user-profile': r'C:\Users\InventedUser',
             'repository-path': r'D:\Invented\Repo'}
    program = tmp_path / 'program'
    (program / '_internal').mkdir(parents=True)
    (program / 'clean.dll').write_bytes(b'\x00MZ nothing personal here\x00')
    (program / '_internal' / 'module.pyd').write_bytes('built in d:\\invented\\repo\\src'.encode('ascii'))
    (program / 'notes.txt').write_bytes('Profil : C:\\Users\\inventeduser\\AppData'.encode('utf-16-le'))
    receipt = module.scan(program, terms)
    assert receipt['status'] == 'LEAK' and receipt['files'] == 3
    kinds = {(finding['file'], finding['kind']) for finding in receipt['findings']}
    assert ('_internal/module.pyd', 'repository-path/ascii') in kinds
    assert ('notes.txt', 'account-name/utf-16-le') in kinds and ('notes.txt', 'user-profile/utf-16-le') in kinds
    assert not any(finding['file'] == 'clean.dll' for finding in receipt['findings'])
    assert 'InventedUser' not in str(receipt).replace('account-name', '')


def test_a_clean_folder_passes_and_needles_come_from_this_pc(tmp_path, monkeypatch):
    module = load()
    (tmp_path / 'PokeMind.txt').write_bytes(b'pokemind\\desktop\\window.py')
    assert module.scan(tmp_path, {'account-name': 'InventedUser'})['status'] == 'CLEAN'
    monkeypatch.setenv('USERNAME', 'abc')  # too short to search for
    monkeypatch.setenv('USERPROFILE', r'C:\Users\InventedProfile')
    terms = module.needles(Path(r'D:\Invented\Repo'))
    assert terms == {'user-profile': r'C:\Users\InventedProfile', 'repository-path': r'D:\Invented\Repo'}
