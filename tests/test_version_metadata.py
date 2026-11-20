"""One version everywhere: app, package metadata, EXE resource, installer, notes (0.9.4 release gate, 0.9.5 published, 0.9.6 current)."""
import importlib.util
import re
import tomllib
from datetime import date
from pathlib import Path

import pokemind

ROOT = Path(__file__).resolve().parents[1]


def load_script():
    spec = importlib.util.spec_from_file_location('make_version_info', ROOT / 'scripts/make_version_info.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_version_is_the_same_in_the_app_the_package_and_the_public_files():
    version = pokemind.__version__
    assert re.fullmatch(r'\d+\.\d+\.\d+', version)
    assert tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version'] == version
    assert f'PokeMind **{version}**' in (ROOT / 'README.md').read_text(encoding='utf-8')
    assert f'PokeMind **{version}**' in (ROOT / 'README.fr.md').read_text(encoding='utf-8')
    assert f'## [{version}]' in (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    assert f'## Exact limits of version {version}' in (ROOT / 'README.md').read_text(encoding='utf-8')
    assert f'## Limites exactes de la version {version}' in (ROOT / 'README.fr.md').read_text(encoding='utf-8')
    assert f'(`v{version}`)' in (ROOT / 'SECURITY.md').read_text(encoding='utf-8')
    notes = (ROOT / f'docs/RELEASE_NOTES_{version}.md').read_text(encoding='utf-8')
    assert notes.startswith(f'# PokeMind {version}') and f'PokeMind-Setup-{version}.exe' in notes
    assert f'# PokeMind {version} — préversion' in notes and f'PokeMind-Setup-{version}.exe.sha256' in notes


def test_the_unpublished_094_candidate_is_folded_into_095_and_never_presented_as_released():
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    headings = [line for line in changelog.splitlines() if line.startswith('## [0.9.5]')]
    assert len(headings) == 1
    heading = headings[0]
    if heading != '## [0.9.5] — unreleased (release candidate)':
        match = re.fullmatch(r'## \[0\.9\.5\] — (\d{4}-\d{2}-\d{2}) \(pre-release\)', heading)
        assert match is not None
        assert date.fromisoformat(match[1]).isoformat() == match[1]
    assert '## [0.9.4] — never published' in changelog
    assert changelog.index('## [0.9.6]') < changelog.index('## [0.9.5]') < changelog.index('## [0.9.4]') < changelog.index('## [0.9.3]')
    notes = (ROOT / 'docs/RELEASE_NOTES_0.9.5.md').read_text(encoding='utf-8')
    assert 'never published' in notes and "jamais été publié" in notes
    assert 'Deck Lab › Statistics' in notes and 'Deck Lab › Statistiques' in notes
    assert 'Never published' in (ROOT / 'docs/RELEASE_NOTES_0.9.4.md').read_text(encoding='utf-8')


def test_the_exe_resource_and_the_installer_carry_that_version():
    module = load_script()
    assert module.version() == pokemind.__version__
    text = module.version_info(pokemind.__version__)
    numbers = tuple(int(p) for p in pokemind.__version__.split('.')) + (0,)
    assert f'filevers={numbers}' in text and f"StringStruct('ProductVersion', '{pokemind.__version__}')" in text
    assert "StringStruct('OriginalFilename', 'PokeMind.exe')" in text
    build = (ROOT / 'scripts/Build-PokeMindDesktop.ps1').read_text(encoding='utf-8')
    assert 'make_version_info.py $versionFile' in build and '--version-file $versionFile' in build
    setup = (ROOT / 'packaging/PokeMind.iss').read_text(encoding='utf-8')
    assert 'VersionInfoVersion={#AppVersion}' in setup and 'OutputBaseFilename=PokeMind-Setup-{#AppVersion}' in setup
