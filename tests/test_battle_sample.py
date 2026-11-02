"""Entirely synthetic log variants; no player or personal-log fixture."""
from contextlib import closing
import hashlib
import sqlite3
from pathlib import Path

import pytest

from pokemind.battle_logs import import_battle_log
from pokemind.database import connect_readonly
from pokemind.battle_sample import conservative_sample
from pokemind.profiles import profile_summary, profile_review
from pokemind.lessons import battle_lessons
from pokemind.readiness import _completion_evidence


def _log(card="Synthetic Spark", opponent="Player B", turns=6, winner="Player A"):
    text = ("Setup\nReference player: Player A\n"
            "Player A played Synthetic Seed to the Active Spot.\n"
            f"{opponent} played Synthetic Leaf to the Active Spot.\n")
    for turn in range(1, turns + 1):
        player = "Player A" if turn % 2 else opponent
        text += (f"Turn # {turn} - {player}'s Turn\n"
                 f"{player} drew {card}.\n{player} played {card}.\n")
        if player == opponent:
            text += f"{opponent} drew a card.\n"
    return text + f"All Prize cards taken. {winner} wins.\n"


def _insert(path, *, variant, parser, deck="synthetic", **kwargs):
    return import_battle_log(path, _log(**kwargs) + f"\nSynthetic variant: {variant}\n",
                             deck_id=deck, source_kind="stdin", parser_version=parser)["battle_id"]


def _pair(path, **kwargs):
    first = _insert(path, variant="one", parser="legacy", **kwargs)
    second = _insert(path, variant="two", parser="new", **kwargs)
    # Simulate an older parser omitting only generic opponent draws.
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("DELETE FROM battle_events WHERE battle_id=? AND evidence='Player B drew a card.'", (first,))
        connection.execute("UPDATE battle_logs SET recognized_events=(SELECT COUNT(*) FROM battle_events WHERE battle_id=?) WHERE id=?", (first, first))
    return first, second


def test_cross_parser_variants_do_not_inflate_summary_or_review(local_tmp: Path):
    path = local_tmp / "synthetic.sqlite3"
    first, second = _pair(path)
    before = hashlib.sha256(path.read_bytes()).digest()
    result = profile_review(path, "synthetic")
    summary = result["summary"]
    assert summary["sample"]["stored_valid_games"] == 2
    assert summary["sample"]["valid_games"] == 1
    assert summary["sample"]["probable_duplicates_excluded"] == 1
    assert summary["outcomes"]["wins"] == 1
    assert summary["outcomes"]["win_ratio"] is None
    assert not summary["assessment_ready"]
    group = summary["sample_review"]["probable_duplicate_groups"][0]
    assert group["battle_ids"] == [first, second] and group["representative_id"] == second
    assert [item["battle_id"] for item in result["facts"]] == [second]
    assert all(item["games_seen"] == 1 for item in summary["observed_cards"])
    assert hashlib.sha256(path.read_bytes()).digest() == before


def test_probable_duplicate_losses_do_not_inflate_a_reported_win_rate(local_tmp):
    path = local_tmp / "synthetic.sqlite3"
    _pair(path, winner="Player B")
    _insert(path, variant="different", parser="new", card="Synthetic Sun")
    summary = profile_summary(path, "synthetic")
    assert summary["stored_outcomes"] == {"wins": 1, "losses": 2, "unknown": 0}
    assert summary["outcomes"]["wins"] == summary["outcomes"]["losses"] == 1
    assert summary["outcomes"]["win_ratio"] is None
    assert summary["outcome_basis"] == "PROVISIONAL_DUPLICATE_REVIEW"


def test_human_profile_marks_duplicate_assumption_explicitly(local_tmp, capsys):
    from pokemind.cli import _human_profile
    path = local_tmp / "synthetic.sqlite3"
    _pair(path)
    _human_profile(profile_summary(path, "synthetic"), review=False)
    text = capsys.readouterr().out
    assert "Bilan provisoire" in text and "doublon(s) probable(s)" in text
    assert "ratio de victoire inconnu" in text


@pytest.mark.parametrize("difference", ["card", "opponent", "deck", "same_parser", "short"])
def test_common_openings_or_different_games_are_not_collapsed(local_tmp: Path, difference):
    path = local_tmp / "synthetic.sqlite3"
    opts = {"turns": 1} if difference == "short" else {}
    first = _insert(path, variant="one", parser="legacy", **opts)
    if difference == "card": opts["card"] = "Synthetic Moon"
    if difference == "opponent": opts["opponent"] = "Player C"
    second = _insert(path, variant="two", parser="legacy" if difference == "same_parser" else "new",
                     deck="other" if difference == "deck" else "synthetic", **opts)
    with closing(connect_readonly(path)) as connection:
        result = conservative_sample(connection, [first, second])
    assert result["battle_ids"] == [first, second]
    assert not result["probable_duplicate_groups"]


def test_lessons_and_readiness_use_same_conservative_sample(local_tmp: Path):
    path = local_tmp / "synthetic.sqlite3"
    _pair(path)
    for index in range(3):
        _insert(path, variant=str(index), parser="new", card=f"Synthetic Other {index}")
    summary = profile_summary(path, "synthetic")
    assert summary["sample"]["stored_valid_games"] == 5
    assert summary["sample"]["valid_games"] == 4 and not summary["assessment_ready"]
    assert battle_lessons(path, "synthetic", as_of="2099-01-01")["sample"]["valid_battles"] == 4
    evidence = _completion_evidence(path)
    assert evidence["conservative_valid_battles"] == 4


def test_historical_view_never_uses_future_duplicate_representative(local_tmp: Path):
    path = local_tmp / "synthetic.sqlite3"
    first, second = _pair(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE battle_logs SET imported_at='2026-01-01' WHERE id=?", (first,))
        connection.execute("UPDATE battle_logs SET imported_at='2026-02-01' WHERE id=?", (second,))
    lessons = battle_lessons(path, "synthetic", as_of="2026-01-15")
    assert lessons["sample"]["valid_battles"] == 1
    assert lessons["sample_review"]["probable_duplicates_excluded"] == 0
