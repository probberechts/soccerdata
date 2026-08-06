"""Unittests for class soccerdata.MatchHistory."""

from pathlib import Path

import pandas as pd
import pytest

from soccerdata import _config
from soccerdata.match_history import MatchHistory


def test_read_games(match_epl_5y: MatchHistory) -> None:
    """It should return a DataFrame with all games from the selected leagues and seasons."""
    df = match_epl_5y.read_games()
    assert isinstance(df, pd.DataFrame)
    assert len(df.index.get_level_values("season").unique()) == 5
    assert len(df) > 0
    assert not any("ï»¿" in c for c in df.columns)


def test_read_games_single_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """It should load leagues that publish all seasons in a single file.

    Some leagues (typically smaller ones) are published by football-data.co.uk
    in a single file under "/new/{league}.csv" that contains the full match
    history across all seasons, using different column names than the
    per-season files. See https://github.com/probberechts/soccerdata/issues/589
    """
    csv_content = (
        "Country,League,Season,Date,Time,Home,Away,HG,AG,Res,PSCH,PSCD,PSCA\n"
        "Switzerland,Super League,2021/2022,07/08/2021,18:00,Basel,Zurich,2,1,H,2.10,3.40,3.90\n"
        "Switzerland,Super League,2021/2022,08/08/2021,16:00,Lausanne,Sion,0,0,D,2.20,3.10,3.50\n"
        "Switzerland,Super League,2022/2023,06/08/2022,18:00,Geneve,Bern,1,0,H,2.00,3.50,4.00\n"
    )
    # cached copy of https://www.football-data.co.uk/new/SWZ.csv
    (tmp_path / "SWZ.csv").write_bytes(csv_content.encode("utf-8-sig"))

    monkeypatch.setitem(
        _config.LEAGUE_DICT,
        "SUI-Super League",
        {
            "MatchHistory": "SWZ",
            "single_file": True,
            "season_start": "Jul",
            "season_end": "May",
        },
    )
    monkeypatch.delattr(MatchHistory, "_all_leagues_dict", raising=False)

    mh = MatchHistory("SUI-Super League", seasons=["2122"], data_dir=tmp_path)
    df = mh.read_games()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.index.get_level_values("season").unique()) == ["2122"]
    assert list(df["home_team"]) == ["Basel", "Lausanne"]
    assert list(df["away_team"]) == ["Zurich", "Sion"]
    # shared columns are kept; per-season-only columns are filled with NaN
    assert "PSCD" in df.columns
    assert df["HTR"].isna().all()
    assert df["referee"].isna().all()
