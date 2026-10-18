"""Tests for issue #739: Cache filenames with unsafe characters."""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from soccerdata import ClubElo, FBref


def _capture_cache_filepath(
    scraper: ClubElo | FBref,
    monkeypatch: pytest.MonkeyPatch,
    call: Callable[[], object],
) -> Path:
    """Execute ``call`` and return the cache filepath passed to ``scraper.get``."""
    captured: list[Path] = []

    def fake_get(_url: str, filepath: Path, *_args: object, **_kwargs: object) -> None:
        captured.append(filepath)
        raise StopIteration

    monkeypatch.setattr(scraper, "get", fake_get)
    with pytest.raises(StopIteration):
        call()

    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize(
    ("team", "expected_filename"),
    [
        ("Bodø/Glimt", "Bodo%2FGlimt.csv"),
        ("Bodø%2FGlimt", "Bodo%252FGlimt.csv"),
        ("A/B", "A%2FB.csv"),
        ("A\\B", "A%5CB.csv"),
        ("A:B", "A%3AB.csv"),
        ("Marseille", "Marseille.csv"),
    ],
)
def test_clubelo_read_team_history_escapes_unsafe_characters_in_cache_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, team: str, expected_filename: str
) -> None:
    """It should escape unsafe characters in team names when building ClubElo cache filenames."""
    elo = ClubElo(data_dir=tmp_path)
    cache_path = _capture_cache_filepath(elo, monkeypatch, lambda: elo.read_team_history(team))
    assert cache_path == tmp_path / expected_filename


@pytest.mark.parametrize(
    ("team", "expected_filename"),
    [
        ("Bodø/Glimt", "matchlogs_Bodø%2FGlimt_20-21_schedule.html"),
        ("Bodø%2FGlimt", "matchlogs_Bodø%252FGlimt_20-21_schedule.html"),
        ("A/B", "matchlogs_A%2FB_20-21_schedule.html"),
        ("A\\B", "matchlogs_A%5CB_20-21_schedule.html"),
        ("A:B", "matchlogs_A%3AB_20-21_schedule.html"),
        ("Marseille", "matchlogs_Marseille_20-21_schedule.html"),
    ],
)
def test_fbref_read_team_match_stats_escapes_unsafe_characters_in_cache_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, team: str, expected_filename: str
) -> None:
    """It should escape unsafe characters in team names when building FBref cache filenames."""
    fbref = FBref.__new__(FBref)
    fbref.data_dir = tmp_path
    teams = pd.DataFrame(
        {"url": ["/en/squads/12345678/2020/Team-Stats"]},
        index=pd.MultiIndex.from_tuples(
            [("FRA-Ligue 1", "20-21", team)], names=["league", "season", "team"]
        ),
    )
    monkeypatch.setattr(fbref, "read_team_season_stats", lambda: teams)

    cache_path = _capture_cache_filepath(
        fbref, monkeypatch, lambda: fbref.read_team_match_stats(team=team)
    )
    assert cache_path == tmp_path / expected_filename
