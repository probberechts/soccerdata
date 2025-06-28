"""Pytest fixtures for soccerdata package."""

import pytest

import soccerdata as sd


@pytest.fixture()
def espn_seriea() -> sd.ESPN:
    """Return a correctly initialized instance of ESPN filtered by league: Serie A."""
    return sd.ESPN("ITA-Serie A", "20-21")


@pytest.fixture()
def sofifa_bundesliga() -> sd.SoFIFA:
    """Return a correctly initialized instance of SoFIFA filtered by league: Bundesliga."""
    return sd.SoFIFA("GER-Bundesliga", versions=[230012])


@pytest.fixture()
def fbref_ligue1() -> sd.FBref:
    """Return a correctly initialized instance of FBref filtered by league: Ligue 1."""
    return sd.FBref("FRA-Ligue 1", "20-21")


@pytest.fixture()
def fotmob_laliga():
    """Return a correctly initialized instance of Fotmob filtered by league: La Liga."""
    return sd.FotMob("ESP-La Liga", "20-21")


@pytest.fixture()
def elo() -> sd.ClubElo:
    """Return a correctly initialized ClubElo instance."""
    return sd.ClubElo()


@pytest.fixture()
def match_epl_5y() -> sd.MatchHistory:
    """Return a MatchHistory instance for the last 5 years of the EPL."""
    return sd.MatchHistory("ENG-Premier League", list(range(2019, 2025)))


@pytest.fixture()
def whoscored() -> sd.WhoScored:
    """Return a correctly initialized instance of WhoScored."""
    return sd.WhoScored("ENG-Premier League", "20-21", headless=False)


@pytest.fixture()
def understat_epl_1516() -> sd.Understat:
    """Return a correctly initialized instance of Understat filtered by league: Premier League."""
    return sd.Understat("ENG-Premier League", "15-16")


@pytest.fixture()
def understat_epl_9091() -> sd.Understat:
    """Return a correctly initialized instance of Understat filtered by league: Premier League."""
    return sd.Understat("ENG-Premier League", "90-91")


@pytest.fixture()
def sofascore_epl_1516() -> sd.Sofascore:
    """Return a correctly initialized instance of Sofascore filtered by league: Premier League."""
    return sd.Sofascore("ENG-Premier League", "15-16")
