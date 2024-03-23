"""A collection of tools to read and process soccer data from various sources."""

__version__ = '1.6.1'

__all__ = [
    'ClubElo',
    'ESPN',
    'FBref',
    'FiveThirtyEight',
    'FotMob',
    'MatchHistory',
    'Sofascore',
    'SoFIFA',
    'Understat',
    'WhoScored',
]

from .clubelo import ClubElo
from .espn import ESPN
from .fbref import FBref
from .fivethirtyeight import FiveThirtyEight
from .fotmob import FotMob
from .match_history import MatchHistory
from .sofascore import Sofascore
from .sofifa import SoFIFA
from .understat import Understat
from .whoscored import WhoScored
