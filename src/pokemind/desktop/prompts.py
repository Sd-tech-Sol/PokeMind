"""Question ideas for the Coach, page by page (owner, 2026-11-18).

A `{slot}` is filled with what the page shows (the opponent, deck or card chosen); with nothing chosen, the idea
uses its fallback words instead. An idea whose slot has no fallback appears only once something is chosen, and the
« match » idea only once a game is chosen. A click fills the message box; nothing is ever sent by itself.
"""
from __future__ import annotations

from pokemind.desktop.locale_text import T, Text

OVERVIEW, COMBATS, DECK_LAB, CARDS, LEARNING, SETTINGS, TERMINAL = range(7)


def idea(fr, en, slot=None, fallback=None, requires=None):
    """`fallback`: (fr, en) words that stand for the slot when nothing is chosen; None hides the idea then."""
    return {'fr': fr, 'en': en, 'slot': slot, 'fallback': fallback, 'requires': requires}


IDEAS = {
    OVERVIEW: (
        idea('Fais-moi le bilan de ma saison en 5 points.', 'Give me my season review in 5 points.'),
        idea('Quelle est ma plus grosse faiblesse en ce moment?', 'What is my biggest weakness right now?'),
        idea('Sur quoi devrais-je m’entraîner cette semaine?', 'What should I practise this week?'),
        idea('Compare mes 10 dernières parties à mes 10 précédentes.', 'Compare my last 10 games with the 10 before.'),
        idea('Est-ce que j’ai assez de parties pour tirer de vraies conclusions?',
             'Do I have enough games to draw real conclusions?'),
        idea('Quel deck devrais-je jouer pour progresser?', 'Which deck should I play to improve?'),
    ),
    COMBATS: (
        idea('Pourquoi je perds contre {adversaire}?', 'Why do I lose against {adversaire}?', 'adversaire',
             ('mes adversaires les plus difficiles', 'my toughest opponents')),
        idea('Analyse ma dernière défaite tour par tour.', 'Analyse my last loss turn by turn.'),
        idea('Quel plan de jeu adopter contre {adversaire}?', 'What game plan should I use against {adversaire}?',
             'adversaire', ('le deck adverse que je croise le plus', 'the opposing deck I face the most')),
        idea('Quelles erreurs je répète dans mes défaites?', 'Which mistakes do I repeat in my losses?'),
        idea('Est-ce que je perds plutôt en début ou en fin de partie?', 'Do I lose more early or late in a game?'),
        idea('Qu’est-ce que j’aurais dû faire autrement dans cette partie?',
             'What should I have done differently in this game?', requires='match'),
    ),
    DECK_LAB: (
        idea('Comment améliorer {deck} sans changer son plan de jeu?', 'How can I improve {deck} without changing its game plan?',
             'deck', ('mon deck', 'my deck')),
        idea('Quelles cartes de {deck} sont les moins utiles?', 'Which cards of {deck} are the least useful?',
             'deck', ('mon deck', 'my deck')),
        idea('Quels sont les pires matchups de {deck} dans la méta datée?', 'What are the worst matchups of {deck} in the dated meta?',
             'deck', ('mon deck', 'my deck')),
        idea('Compare {deck} à la meilleure liste publique du même archétype.',
             'Compare {deck} with the best public list of the same archetype.', 'deck', ('mon deck', 'my deck')),
        idea('Est-ce que {deck} est légal en Standard aujourd’hui?', 'Is {deck} legal in Standard today?',
             'deck', ('mon deck', 'my deck')),
        idea('Explique-moi le plan de jeu de {deck} pour les trois premiers tours.',
             'Explain the game plan of {deck} for the first three turns.', 'deck', ('mon deck', 'my deck')),
    ),
    CARDS: (
        idea('Explique-moi {carte} et quand la jouer.', 'Explain {carte} to me and when to play it.', 'carte',
             ('une carte que je devrais connaître', 'a card I should know')),
        idea('Dans quels decks {carte} est-elle jouée en ce moment?', 'Which decks play {carte} right now?', 'carte'),
        idea('Quelles cartes peuvent remplacer {carte}?', 'Which cards can replace {carte}?', 'carte'),
        idea('Quels sont les decks les plus joués dans la méta datée?', 'Which decks are played the most in the dated meta?'),
        idea('Quel deck de la méta bat le mieux mon deck principal?', 'Which meta deck beats my main deck best?'),
        idea('Quelles cartes récentes changent la méta?', 'Which recent cards change the meta?'),
    ),
    LEARNING: (
        idea('Qu’est-ce que tu as appris de mes parties jusqu’ici?', 'What have you learned from my games so far?'),
        idea('Quelles hypothèses sont les plus solides en ce moment, et sur combien de parties?',
             'Which hypotheses are the strongest right now, and over how many games?'),
        idea('Propose-moi un plan à tester pour mes 5 prochaines parties.', 'Suggest a plan to test over my next 5 games.'),
        idea('Quelle habitude devrais-je corriger en premier?', 'Which habit should I fix first?'),
        idea('Qu’est-ce qui a changé depuis la dernière mise à jour?', 'What has changed since the last update?'),
    ),
    SETTINGS: (
        idea('Comment importer mes journaux de combat?', 'How do I import my battle logs?'),
        idea('Où sont gardées mes données, et qui peut les lire?', 'Where is my data kept, and who can read it?'),
        idea('Comment mettre à jour le catalogue de cartes?', 'How do I update the card catalogue?'),
        idea('Quelle est la différence entre Codex et Claude Code dans le coach?',
             'What is the difference between Codex and Claude Code in the coach?'),
        idea('Comment sauvegarder mes données?', 'How do I back up my data?'),
    ),
}


def _words(value, language):
    if isinstance(value, Text):
        return value.en if language == 'en' else value.fr
    return str(value)


def page_ideas(page, state=None):
    """The ideas of a page as texts in both languages, slots filled from `state` (adversaire, deck, carte, match).
    The Terminal page has none of its own: the caller keeps the previous page's."""
    state = state or {}
    result = []
    for item in IDEAS.get(page, ()):
        if item['requires'] and not state.get(item['requires']):
            continue
        slot = item['slot']
        if slot is None:
            result.append(T(item['fr'], en=item['en']))
            continue
        chosen = state.get(slot)
        if chosen:
            fr, en = _words(chosen, 'fr'), _words(chosen, 'en')
        elif item['fallback']:
            fr, en = item['fallback']
        else:
            continue  # « cette carte » with no card chosen would name nothing
        result.append(T(item['fr'].replace('{' + slot + '}', fr), en=item['en'].replace('{' + slot + '}', en)))
    return result
