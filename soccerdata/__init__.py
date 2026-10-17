"""A collection of tools to read and process soccer data from various sources."""

try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("soccerdata")
    except PackageNotFoundError:  # pragma: no cover
        __version__ = "unknown"

__all__ = [
    "ESPN",
    "ClubElo",
    "FBref",
    "MatchHistory",
    "SoFIFA",
    "Sofascore",
    "Understat",
    "WhoScored",
]

from .clubelo import ClubElo
from .espn import ESPN
from .fbref import FBref
from .match_history import MatchHistory
from .sofascore import Sofascore
from .sofifa import SoFIFA
from .understat import Understat
from .whoscored import WhoScored
