Welcome to SoccerData
======================


SoccerData is a collection of wrappers over soccer data from `Club Elo`_,
`ESPN`_, `FBref`_, `FiveThirtyEight`_, `Football-Data.co.uk`_, `SoFIFA`_ and
`WhoScored`_. You get Pandas DataFrames with sensible, matching column names
and identifiers across datasets. Data is downloaded when needed and cached
locally.

.. code:: python

   import soccerdata as sd

   # Create scraper class instance for the Premier League
   five38 = sd.FiveThirtyEight('ENG-Premier League', '1819')

   # Fetch dataframes
   games = five38.read_games()

To learn how to install, configure and use SoccerData, see the
:ref:`Quickstart guide <quickstart>`. For documentation on each of the
supported data sources, see the :ref:`API reference <api>`.

Other useful projects
----------------------

SoccerData is not the only tool of its kind. If SoccerData doesn’t quite fit
your needs or you want to obtain data from other sources, we recommend looking
at these tools:

- `worldfootballR`_: an R package with scrapers for FBref, Transfermarkt and Understat.
- `Tyrone Mings`_: a Python package to scrape data from TransferMarkt
- `understat`_:a Python package to scrape data from Understat
- `understatr`_: an R package to scrape data from Understat
- `ScraperFC`_: a Python package to scrape data from FBRef, Understat, FiveThirtyEight and WhoScored
- `Scrape-FBref-data`_: Python package to scrape StatsBomb data via FBref


.. toctree::
   :hidden:
   :maxdepth: 1

   usage
   reference/index
   contributing
   License <license>
   Changelog <https://github.com/probberechts/soccerdata/releases>

.. _socceraction: https://socceraction.readthedocs.io/en/latest/modules/generated/socceraction.data.opta.OptaLoader.html#socceraction.data.opta.OptaLoader
.. _Club Elo: https://www.clubelo.com/
.. _ESPN: https://www.espn.com/soccer/
.. _FBref: https://www.fbref.com/en/
.. _FiveThirtyEight: https://fivethirtyeight.com/soccer-predictions/
.. _Football-Data.co.uk: https://www.football-data.co.uk/
.. _SoFIFA: https://sofifa.com/
.. _WhoScored: https://www.whoscored.com/
.. _worldfootballR: https://jaseziv.github.io/worldfootballR/index.html
.. _Tyrone Mings: https://github.com/FCrSTATS/tyrone_mings
.. _understat: https://github.com/amosbastian/understat
.. _understatr: https://github.com/ewenme/understatr
.. _ScraperFC: https://github.com/oseymour/ScraperFC
.. _Scrape-FBref-data: https://github.com/parth1902/Scrape-FBref-data
