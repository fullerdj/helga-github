A Github plugin for the helga chat bot
======================================

About
-----

Helga is a Python chat bot. Full documentation can be found at
http://helga.readthedocs.org.

This plugin allows Helga to respond to GitHub pull request numbers in IRC
and print information about them. For example::

  03:14 < fred> PR 8825
  03:14 <@helgabot> fred might be talking about
                    https://github.com/fred/crap/pull/123 [nifty_module: 
                    fix frobnicator to fizz the buzzer]

You can specify multiple PRs as well::

  03:14 < fred> PR 123 and PR 456
  03:14 <@helgabot> fred might be talking about
                    https://github.com/fred/crap/pull/123 [nifty_module:
                    fix frobnicator to fizz the buzzer] and
                    https://github.com/fred/crap/pull/456 [niftier_module:
                    repair steering wheel in the cdr car]

You can also specify a project other than the defaults to search::

  03:14 < fred> PR fred/crap 123
  03:14 <@helgabot> fred might be talking about
                    https://github.com/fred/crap/pull/123 [nifty_module: 
                    fix frobnicator to fizz the buzzer]

All projects specified in GITHUB_PROJECT are searched and the first open PR
found is returned. If no open PRs are found, the first closed PR is returned.

Installation
------------
This plugin is configured for setuptools. (``python setup.py``)

If you want to hack on the helga-redmine source code, in your virtualenv where
you are running Helga, clone a copy of this repository from GitHub and run
``python setup.py develop``.

Configuration
-------------
In your ``settings.py`` file (or whatever you pass to ``helga --settings``),
you must specify a list called ``GITHUB_PROJECTS``. Note that a list is
required even for a single project. For example::

  GITHUB_PROJECT = [ 'fred/crap', 'fifi/blah' ]

or::

  GITHUB_PROJECT = [ 'fred/crap' ]

Credits
-------

This is a simple retread of https://github.com/alfredodeza/helga-redmine/
