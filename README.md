# Simple Mail Sender

This project implements simple mail sending service written in flask.

Flask-caching is used for abstraction over a cache. Deployed server uses redis as a cache.

When getting request to send an email application will try to get the index of the provider to send the mail to from cache. If no such record exists in cache it will create it with default value. Then, starting from this index, it will try to send an email using every provider until it succeeds or makes a full cycle in which case it will return 503.

If the index of the provider which has successfully accepted our request is different from the value taken from the cache then the new index is stored as to start with the last working provider next time.


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

Run docker build to build an image.

By default application starts on ports `:8080`.

By default empty configuration is provided wich will result in 500 status code when running the server.

To provide your own configuration set `MSS_CONFIG_PATH` variable to point to your configurations **absolute** path. You can use `/conf` volume to pass your own configuration path.

If you want to provide your own configuration on the build time rather then runtime then change the content of the `conf.ini` file to your desired value.
