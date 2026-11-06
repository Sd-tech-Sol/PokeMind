"""BrainBall themes: the palette file is the source, contrasts hold on the real backgrounds, nothing stays red."""
import json
import re
from pathlib import Path

import pytest
from PySide6.QtGui import QColor

from pokemind.desktop import theme
from pokemind.desktop.theme import OBJECTS, PALETTES, colors, contrast, stylesheet

SOURCE = json.loads((Path(__file__).resolve().parents[1] / 'docs/design/pokemind-brainball/palette.json')
                    .read_text(encoding='utf-8'))
THEMES = ('dark', 'light')


@pytest.mark.parametrize('name', THEMES)
def test_every_palette_file_token_is_used_unchanged_and_the_rest_is_declared_derived(name):
    tokens = {key: value.upper() for key, value in SOURCE['themes'][name].items()}
    ours = {key: value.upper() for key, value in PALETTES[name].items()}
    assert {key: ours[key] for key in tokens} == tokens
    assert set(ours) - set(tokens) == set(theme.DERIVED)
    brand = {('gold' if key == 'or' else key): value.upper() for key, value in SOURCE['brand'].items()}  # « or » is a Python word
    assert {key: value.upper() for key, value in theme.BRAND.items()} == brand


TEXT = 4.5      # WCAG AA, normal text
GRAPHIC = 3.0   # large text and essential non-text elements


def pairs(c):
    surfaces = ('background', 'surface', 'sidebar', 'alternate', 'input')
    for fg in ('text', 'muted'):
        for bg in surfaces:
            yield fg, bg, TEXT
    for fg in ('accent', 'link', 'red', 'blue', 'yellow', 'success'):  # labels, legends, tiles, dock titles
        for bg in ('background', 'surface', 'sidebar'):
            yield fg, bg, TEXT
    for bg in ('primary', 'primary_hover', 'primary_pressed'):
        yield 'on_primary', bg, TEXT
    for bg in ('hero_start', 'hero_end'):
        for fg in ('hero_text', 'hero_muted', 'hero_kicker'):
            yield fg, bg, TEXT
    yield 'selection_text', 'selection', TEXT
    yield 'warning', 'warning_bg', TEXT
    yield 'on_danger', 'danger', TEXT
    yield 'tooltip_text', 'tooltip', TEXT
    yield 'nav_icon_selected', 'primary', GRAPHIC
    for fg in ('focus', 'field_border'):  # focus ring, field outlines, scrollbar handles
        for bg in ('background', 'surface', 'input'):
            yield fg, bg, GRAPHIC
    for fg in ('blue', 'red', 'yellow', 'neutral_chart'):  # chart series and card tops
        yield fg, 'surface', GRAPHIC


@pytest.mark.parametrize('name', THEMES)
def test_contrasts_hold_on_the_real_backgrounds(name):
    c = colors(name)
    low = [(fg, bg, round(contrast(c[fg], c[bg]), 2)) for fg, bg, minimum in pairs(c) if contrast(c[fg], c[bg]) < minimum]
    assert low == []
    for kind in theme.SETTING_ROLES:  # settings glyphs on their rows
        assert contrast(theme.setting_tint(kind, name), c['surface']) >= GRAPHIC, kind
    assert contrast(OBJECTS['terminal_text'], OBJECTS['terminal']) >= TEXT


@pytest.mark.parametrize('name', THEMES)
def test_the_stylesheet_takes_every_colour_from_the_theme(name):
    css = stylesheet(name)
    assert not re.findall(r'@[a-z_]+', css)
    allowed = {value.upper() for value in list(colors(name).values()) + list(OBJECTS.values()) if value.startswith('#')}
    assert {value.upper() for value in re.findall(r'#[0-9A-Fa-f]{6}\b', css)} <= allowed
    c = colors(name)
    primary = re.search(r'QPushButton#primary \{([^}]*)\}', css).group(1)
    assert 'background:' + c['primary'] in primary  # blue, never the old generic red
    assert 'stop:0 ' + c['hero_start'] in css and 'stop:1 ' + c['hero_end'] in css
    selected = re.search(r'QListWidget::item:selected \{([^}]*)\}', css).group(1)
    assert c['primary'] in selected and c['on_primary'] in selected
    for old in ('#C73148', '#BD2C43', '#B92B43', '#D84559', '#BA2440', '#E34450', '#1B2335', '#26334C'):
        assert old not in css.upper()
    chevron = re.search(r'QComboBox::down-arrow \{ image:url\((pokemind-theme:[^)]+)\)', css).group(1)
    assert (Path(theme.tempfile.gettempdir()) / theme.ARROWS / chevron.split(':', 1)[1]).is_file()


def test_both_themes_share_the_result_meaning():
    for name in THEMES:  # wins blue, losses red, unknown gold; charts also label them in words
        c = colors(name)
        assert QColor(c['blue']).hue() in range(195, 230) and QColor(c['red']).hue() in range(340, 360)
        assert QColor(c['yellow']).hue() in range(35, 55) and c['hero_kicker'].upper() == '#FFD54F'
