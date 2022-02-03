.. soccerdata package index documentation toctree
.. _api:

.. currentmodule:: soccerdata

API
===

Currently the following data sources are supported:

.. list-table::
   :widths: 30 70

   * - :ref:`Club Elo <api-clubelo>`
     - Team’s relative strengths as Elo ratings, for most European leagues. Recalculated after every round, includes history.
   * - :ref:`ESPN <api-espn>`
     - Historical results, statistics and lineups.
   * - :ref:`FBref <api-fbref>`
     - Historical results, lineups, and detailed aggregated statistics for teams and individual players based on StatsBomb data.
   * - :ref:`FiveThirtyEight <api-fivethirtyeight>`
     - Team’s relative strengths as SPI ratings, predictions and results for the top European and American leagues.
   * - :ref:`MatchHistory <api-matchhistory>`
     - Historical results, betting odds and match statistics. Level of detail depends on league.
   * - :ref:`SoFIFA <api-sofifa>`
     - Detailed scores on all player's abilities from EA Sports FIFA.
   * - :ref:`WhoScored <api-whoscored>`
     - Historical results, match preview data and detailed Opta event stream data for major leagues.

.. toctree::
   :hidden:

   clubelo
   espn
   fbref
   fivethirtyeight
   matchhistory
   sofifa
   whoscored
