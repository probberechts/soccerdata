"""A collection of tools to read and process soccer data from various sources."""

__version__ = '1.5.3'

__all__ = [
    'FiveThirtyEight',
    'ClubElo',
    'MatchHistory',
    'FBref',
    'Fotmob',
    'ESPN',
    'WhoScored',
    'SoFIFA',
]

from .clubelo import ClubElo
from .espn import ESPN
from .fbref import FBref
from .fivethirtyeight import FiveThirtyEight
from .fotmob import Fotmob
from .match_history import MatchHistory
from .sofifa import SoFIFA
from .whoscored import WhoScored
