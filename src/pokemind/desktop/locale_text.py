"""Qt-free paired text for app-owned strings; data segments stay identical."""
from pokemind.desktop.translations import english

_language = 'fr'


class Text(str):
    def __new__(cls, fr, en):
        value = super().__new__(cls, en if _language == 'en' else fr)
        value.fr, value.en = fr, en
        return value

    def __getnewargs__(self):
        return self.fr, self.en

    def __add__(self, other):
        return Text(self.fr + variant(other, 'fr'), self.en + variant(other, 'en'))

    def __radd__(self, other):
        return Text(variant(other, 'fr') + self.fr, variant(other, 'en') + self.en)

    def replace(self, old, new, count=-1):
        return Text(self.fr.replace(variant(old, 'fr'), variant(new, 'fr'), count),
                    self.en.replace(variant(old, 'en'), variant(new, 'en'), count))


def variant(value, language):
    return (value.en if language == 'en' else value.fr) if isinstance(value, Text) else str(value)


def display(value):
    return variant(value, _language)


def T(source, *, en=None):
    return source if isinstance(source, Text) and en is None else Text(source, en if en is not None else english(source))


def J(separator, values):
    values = list(values)
    return Text(variant(separator, 'fr').join(variant(v, 'fr') for v in values),
                variant(separator, 'en').join(variant(v, 'en') for v in values))


def set_current_language(language):
    global _language
    _language = 'en' if language == 'en' else 'fr'
