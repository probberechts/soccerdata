=================
Contributor Guide
=================

This document lays out guidelines and advice for contributing to this project.
If you're thinking of contributing, please start by reading this document and
getting a feel for how contributing to this project works. If you have any
questions, feel free to reach out to `Pieter Robberechts`_, the primary maintainer.

.. _Pieter Robberechts: https://people.cs.kuleuven.be/~pieter.robberechts/

The guide is split into sections based on the type of contribution you're
thinking of making.


.. _bug-reports:

Bug Reports
-----------

Bug reports are hugely important! Before you raise one, though, please check
through the `GitHub issues`_, **both open and closed**, to confirm that the bug
hasn't been reported before.

When filing an issue, make sure to answer these questions:

- Which Python version are you using?
- Which version of soccerdata are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.

.. _GitHub issues: https://github.com/probberechts/soccerdata/issues


Feature Requests
----------------

If you believe there is a feature missing, feel free to raise a feature
request on the `Issue Tracker`_.

.. _Issue tracker: https://github.com/probberechts/soccerdata/issues


Documentation Contributions
---------------------------

Documentation improvements are always welcome! The documentation files live in
the ``docs/`` directory of the codebase. They're written in
`reStructuredText`_, and use `Sphinx`_ to generate the full suite of
documentation.

You do not have to set up a development environment to make small changes to
the docs. Instead, you can `edit files directly on GitHub`_ and suggest changes.

When contributing documentation, please do your best to follow the style of the
documentation files. This means a soft-limit of 79 characters wide in your text
files and a semi-formal, yet friendly and approachable, prose style.

When presenting Python code, use double-quoted strings (``"hello"`` instead of
``'hello'``).

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx-doc.org/index.html
.. _edit files directly on GitHub: https://docs.github.com/en/repositories/working-with-files/managing-files/editing-files


Code Contributions
------------------

If you intend to contribute code, do not feel the need to sit on your
contribution until it is perfectly polished and complete. It helps everyone
involved for you to seek feedback as early as you possibly can. Submitting an
early, unfinished version of your contribution for feedback can save you from
putting a lot of work into a contribution that is not suitable for the
project.

Setting up your development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To test out code changes, you'll need to set up a Python environment with all
required dependencies. It's recommended to use uv_ to set up your environment.
On macOS and Linux, you can use `curl` to the download the installation script
and execute it:

.. code:: console

   $ curl -LsSf https://astral.sh/uv/install.sh | sh


Information about installation options and instructions for Windows can be found in
`uv's installation guide <https://docs.astral.sh/uv/getting-started/installation/>`_.

Next, create and activate a virtual environment using uv with a Python version
that soccerdata supports:

.. code:: console

    $ uv venv --python 3.9
    $ source .venv/bin/activate

Alternatively, you can use `pip`. You'll need to have at least the minimum
Python version that soccerdata supports. Next, install the required
dependencies in a virtual environment as follows:

.. code:: console

    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ python -m pip install -e .
    $ python -m pip install -r requirements.txt


.. _uv: https://docs.astral.sh/uv

Steps for submitting Code
~~~~~~~~~~~~~~~~~~~~~~~~~

When contributing code, you'll want to follow this checklist:

1. Fork the repository on GitHub.
2. Run the tests to confirm they all pass on your system. If they don't, you'll
   need to investigate why they fail. If you're unable to diagnose this
   yourself, raise it as a bug report.
3. Write tests that demonstrate your bug or feature. Ensure that they fail.
4. Make your change.
5. Run the entire test suite again, confirming that all tests pass *including
   the ones you just added*.
6. Make sure your code follows the code style discussed below.
7. Send a GitHub Pull Request to the main repository's ``master`` branch.
   GitHub Pull Requests are the expected method of code collaboration on this
   project.

Testing the project
~~~~~~~~~~~~~~~~~~~

Run the full test suite:

.. code:: console

   $ make test

You can also run tests for a specific data source.
For example, invoke the unit test suite like this to run tests for ClubElo
only:

.. code:: console

   $ make test-class clubelo

Unit tests are located in the ``tests`` directory,
and are written using the pytest_ testing framework.

.. _pytest: https://pytest.readthedocs.io/

Code style
~~~~~~~~~~~

The soccerdata codebase uses the `PEP 8`_ code style. In addition, we have
a few guidelines:

- Line-length can exceed 79 characters, to 100, when convenient.
- Line-length can exceed 100 characters, when doing otherwise would be *terribly* inconvenient.
- Always use double-quoted strings (e.g. ``"#soccer"``), unless a double-quote occurs within the string.

To ensure all code conforms to this format. You can format the code using the
pre-commit hooks.

.. code:: console

   $ make pre-commit-test

Docstrings are to follow the `numpydoc guidelines`_.

.. _PEP 8: https://pep8.org/
.. _numpydoc guidelines: https://numpydoc.readthedocs.io/en/latest/format.html

Submitting changes
~~~~~~~~~~~~~~~~~~

Open a `pull request`_ to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The test suite must pass without errors and warnings.
- Include unit tests.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early, though. We can always iterate on this.

To run linting and code formatting checks before committing your change, you
can install pre-commit as a Git hook by running the following command:

.. code:: console

   $ make pre-commit-test

To automatically run the pre-commit checks before committing, you can
run

.. code:: console

   $ make pre-commit-update

It is recommended to open an issue before starting work on anything.

.. _pull request: https://github.com/probberechts/soccerdata/pulls
.. github-only
