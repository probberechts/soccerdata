"""
Data Source Extractors
Extracts data from various football statistics sources
"""

from .base_extractor import BaseExtractor
from .fbref_extractor import FBrefExtractor
from .fotmob_extractor import FotMobExtractor
from .understat_extractor import UnderstatExtractor
from .whoscored_extractor import WhoScoredExtractor
from .sofascore_extractor import SofascoreExtractor
from .espn_extractor import ESPNExtractor
from .clubelo_extractor import ClubEloExtractor
from .matchhistory_extractor import MatchHistoryExtractor
from .sofifa_extractor import SoFIFAExtractor

__all__ = [
    'BaseExtractor',
    'FBrefExtractor',
    'FotMobExtractor',
    'UnderstatExtractor',
    'WhoScoredExtractor',
    'SofascoreExtractor',
    'ESPNExtractor',
    'ClubEloExtractor',
    'MatchHistoryExtractor',
    'SoFIFAExtractor',
]
