from __future__ import annotations

import socket
from pathlib import Path

import pytest

from pokemind.battle_logs import import_battle_log
from pokemind.profiles import profile_review, profile_summary


def _game(number: int, winner: str = "JoueurA", card: str = "Iono") -> str:
    outcome = f"All Prize cards taken. {winner} wins.\n" if winner else ""
    return (
        "Setup\nReference player: JoueurA\n"
        f"JoueurA played Ralts {number} to the Active Spot.\n"
        "AdversaireB played Pikachu to the Active Spot.\n"
        "Turn # 1 - JoueurA's Turn\n"
        f"JoueurA drew {card}.\nJoueurA played {card}.\n{outcome}"
    )


@pytest.mark.parametrize(
    ("count", "ready"),
    [(0, False), (1, False), (4, False), (5, True), (10, True)],
)
def test_profile_thresholds(local_tmp: Path, count: int, ready: bool) -> None:
    db_path = local_tmp / f"profile-{count}.sqlite3"
    if count == 0:
        import_battle_log(db_path, "journal incomplet", source_kind="stdin", deck_id="principal")
    for index in range(count):
        winner = "JoueurA" if index % 2 == 0 else "AdversaireB"
        import_battle_log(db_path, _game(index, winner), source_kind="stdin", deck_id="principal")
    result = profile_summary(db_path, "principal")
    assert result["sample"]["valid_games"] == count
    assert result["assessment_ready"] is ready
    if count:
        assert result["outcomes"]["wins"] + result["outcomes"]["losses"] == count


def test_profile_separates_two_decks_and_observed_cards_from_collection(local_tmp: Path) -> None:
    db_path = local_tmp / "two-decks.sqlite3"
    import_battle_log(db_path, _game(1, card="Iono"), source_kind="file", deck_id="alpha")
    import_battle_log(db_path, _game(2, card="Nest Ball"), source_kind="file", deck_id="beta")
    alpha = profile_summary(db_path, "alpha")
    beta = profile_summary(db_path, "beta")
    assert {item["card"] for item in alpha["observed_cards"]} >= {"Iono"}
    assert "Nest Ball" not in {item["card"] for item in alpha["observed_cards"]}
    assert {item["card"] for item in beta["observed_cards"]} >= {"Nest Ball"}
    assert "collection" in " ".join(alpha["limits"]).casefold()


def test_five_anonymous_games_keep_exact_win_loss_unknown_counts(local_tmp: Path) -> None:
    db_path = local_tmp / "five-games.sqlite3"
    winners = ["JoueurA", "AdversaireB", "JoueurA", "", "AdversaireB"]
    for index, winner in enumerate(winners):
        import_battle_log(
            db_path, _game(index, winner), source_kind="stdin", deck_id="principal"
        )
    summary = profile_summary(db_path, "principal")
    assert summary["sample"]["valid_games"] == 5
    assert summary["outcomes"] == {
        "wins": 2,
        "losses": 2,
        "unknown": 1,
        "win_ratio": 0.5,
        "ratio_denominator": 4,
    }


def test_review_has_battle_ids_turn_evidence_limits_and_questions(local_tmp: Path) -> None:
    db_path = local_tmp / "review.sqlite3"
    for index in range(5):
        import_battle_log(db_path, _game(index), source_kind="stdin", deck_id="principal")
    review = profile_review(db_path, "principal")
    assert len(review["facts"]) == 5
    assert all(fact["battle_id"] and fact["turn_evidence"] for fact in review["facts"])
    assert review["summary"]["limits"]
    assert review["hypotheses"]
    assert review["targeted_questions"]


def test_log_import_and_profile_never_use_network(local_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args, **kwargs):
        raise AssertionError("Un accès réseau a été tenté")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    db_path = local_tmp / "offline.sqlite3"
    import_battle_log(db_path, _game(1), source_kind="file", deck_id="principal")
    assert profile_summary(db_path, "principal")["sample"]["valid_games"] == 1
