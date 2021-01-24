# Simple Mail Sender

This project implements simple mail sending service written in flask.

Flask-caching is used for abstraction over a cache.

## Installation

To run the project be sure to have `poetry` installed (https://python-poetry.org/).

Configure server port by setting `PORT` env variable to the desired port or modify content of the `uwsgi.ini` file.

Create application configuration file based on the `conf.ini` file. And then set `MSS_CONFIG_PATH` env variable as a path to your configuration file.

In the top-level directory run:

`poetry install`

`poetry run uwsgi uwsgi.ini`

to start a server.

## Project structure

Top level directory holds server and application configuration.

* `mail_sending_service` - source files for the project,
  * `app.py` - defines functions to create an application,
  * `views.py` - defines applications endpoints,
  * `wsgi.py` - wsgi entrypoint
  * `mail/senders.py` - defines abstraction as well as concrete classes for transactional mailing providers,
* `static`- application's static files (generated using swagger.io),
* `test` - unittests for the mail sending view,

## Api

Application defines 2 endpoints:

* `/api` - static page documenting application api, generated using swaggers editor,
* `/mail` - mail sending endpoint, read api documentation or more details.


## Running in docker
