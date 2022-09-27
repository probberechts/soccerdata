.. _quickstart:

Usage
=====

This tutorial will walk you through installing, configuring, and using
SoccerData.


Installation
------------

SoccerData can be easily installed via `pip <https://pip.readthedocs.org/>`__:

.. code:: bash

  python3 -m pip install soccerdata


Global configuration
---------------------

Several settings that can be configured globally using the following environment variables:

``SOCCERDATA_DIR``
    The directory where the downloaded data is cached and where logs are
    stored. By default, all data is stored to ``~/soccerdata`` on Linux / Mac
    OS and ``C:\Users\yourusername\soccerdata`` on Windows.
``SOCCERDATA_NOCACHE``
    If set to "true", no cached data is returned. Note that no-cache does not
    mean "don't cache". All downloaded data is still cached and overwrites
    existing caches. If the sense of "don't cache" that you want is actually
    "don't store", then ``SOCCERDATA_NOSTORE`` is the option to use. By default,
    data is retrieved from the cache.
``SOCCERDATA_NOSTORE``
    If set to "true", no data is stored. By default, data is cached.
``SOCCERDATA_LOGLEVEL``
    The level of logging to use. By default, this is set to "INFO".

Example:

.. code-block:: bash

  # bash
  export SOCCERDATA_DIR = "~/soccerdata"
  export SOCCERDATA_NOCACHE = "False"
  export SOCCERDATA_NOSTORE = "False"
  export SOCCERDATA_LOGLEVEL = "INFO"

Scraping data
-------------

Each of the supported data sources has its corresponding class for fetching
data with a uniform API. For example, the :class:`~soccerdata.FBref` class is
used to fetch data from `fbref.com <https://www.fbref.com/>`__.

.. code:: python

   import soccerdata as sd

   # Create scraper class instance
   fbref = sd.FBref()

This will create a ``soccerdata/FBref/`` folder in your home directory  in
which all scraped data will be cached and where logs will be saved. If you
prefer to store the data in a different folder or disable caching, you can
configure this using environment variables (see above) or by setting the
``data_dir``, ``no_cache`` and ``no_store`` parameters which are supported by
each scraper class.

.. code:: python

   # Create scraper class instance with custom caching behavior
   fbref = sd.FBref(data_dir="/tmp", no_cache=True, no_store=True)

Once you have a scraper class instance, you can use it to fetch data. See the
:ref:`API reference <api>` for the full list of options available for each scraper. For
example, to fetch aggregated shooting stats for all teams:

.. code:: python

   # Create dataframes
   season_stats = fbref.read_team_season_stats(stat_type='shooting')


The data is always returned as a convenient Pandas DataFrame.

.. csv-table::
   :file: output.csv
   :header-rows: 1

Not all data sources provide data for all leagues. The leagues available for
each source can be listed with the :meth:`~soccerdata.FBref.available_leagues`
class method.

.. code:: python

   sd.FBref.available_leagues()
   >>> ['ENG-Premier League', 'ESP-La Liga', 'FRA-Ligue 1', 'GER-Bundesliga', 'ITA-Serie A']


By default, the data for all available leagues and 10 most recent seasons will
be downloaded. In most cases, you would want to limit the data to a specific
league and / or seasons. This can be done by passing a list of leagues and
seasons to the constructor of the scraper class. For example:

.. code:: python

   # Create scraper class instance filtering on specific leagues and seasons
   fbref = sd.FBref(leagues=['ENG-Premier League'], seasons=['1718', '1819'])


See the examples and :ref:`API reference <api>` for detailed instructions for
each of the available data sources.

Additional setup for WhoScored
------------------------------

WhoScored implements strong protection against scraping using Incapsula. To
circumvent this, this scraper uses Selenium with the ChromeDriver extension to
emulate a real user. Before using this scraper, you will have to `install
Chrome`_. A Selenium driver matching your Chrome version will be downloaded
automatically when you run the scraper.

Even with this setup, it is likely that your IP address will get blocked
eventually. Therefore, is is recommended to setup a SOCKS5 proxy with Tor.
Checkout the `installation guide`_ on the Tor website for installation
instructions. After installing Tor, make sure to start it up before scraping.
This can easily be done by running the ``tor`` command from your terminal (in
a separate window), Tor will start up and run on “localhost:9050” by default.
Once Tor is running, you can enable the extension by setting ``proxy='tor'``.

.. code:: python

   ws = sd.WhoScored(proxy='tor')

The code snippet above assumes you have a Tor proxy running on
"localhost:9050". Many distributions indeed default to having a SOCKS proxy
listening on port 9050, but some may not. In particular, the Tor Browser
Bundle defaults to listening on port 9150. You can specify a custom host and
port as

.. code:: python

   ws = sd.WhoScored(proxy={
        "http": "socks5://127.0.0.1:9150",
        "https": "socks5://127.0.0.1:9150",
    })


.. _insallation guide: https://community.torproject.org/onion-services/setup/install/
.. _install Chrome: https://www.google.com/chrome/


Adding additional leagues
-------------------------

The top-5 European leagues are fully supported. If you want to add more
leagues, you can configure these in ``SOCCERDATA_DIR/config/league_dict.json``.
This file should contain a mapping between a generic name for the league and
the identifier used internally by each data source that you want to support.
For example, for the Dutch Eredivisie this would be:

.. code-block:: json

  {
    "NED-Eredivisie": {
      "ClubElo": "NED_1",
      "MatchHistory": "N1",
      "SoFIFA": "Holland Eredivisie (1)",
      "FBref": "Dutch Eredivisie",
      "ESPN": "ned.1",
      "FiveThirtyEight": "eredivisie",
      "WhoScored": "Netherlands - Eredivisie"
      "season_start": "Aug",
      "season_end": "May",
    },
  }

The ``season_end`` and ``season_start`` fields are optional. This should be the
month in which the last game and first game of a season are played,
respectively. If they are not provided, June is used as the last month of the
season and July as the first one.

Note that the provided scrapers might give some errors for the leagues you add
yourself. This is because the same data is not always available for all seasons.


Uniform team names
------------------

Each data source uses a different set of team names, which makes it difficult
to combine data from multiple sources. To mitigate this, SoccerData allows
translating the team names to uniform names. This is done by providing
a ``SOCCERDATA_DIR/config/team_dict.json`` file. This file should contain a
mapping between a generic name for each team and the team name used by each
data source that you want to support. The example below will map "Tottenham
Hotspur", "Tottenham Hotspur FC" and "Spurs" to "Tottenham" in all scraped
data.

.. code-block:: json

  {
    "Tottenham": ["Tottenham Hotspur", "Tottenham Hotspur FC", "Spurs"],
  }

Next steps
----------
Look at you! You’re now basically an expert at SoccerData! ✨

From this point you can:

- Look at the example notebooks for each :ref:`Data source <datasources>`.
- Take a deep dive into the :ref:`API <api>`.
- Give us feedback or contribute, see :ref:`Contributing <contributing>`.

Have fun! 🎉
