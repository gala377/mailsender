from flask import Flask
from flask_caching import Cache

from mail_sending_service.views import ViewBase


def create_app(config):
    app = Flask(__name__)
    init_cache(app, config)
    init_views(app, config)
    return app

def init_cache(app, config):
    cache = Cache(config={'CACHE_TYPE': 'simple'})
    cache.init_app(app)

def init_views(app, config):
    ViewBase.init_app(app)
