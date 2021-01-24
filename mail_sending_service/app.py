import flask

from flask import Flask
from flask_caching import Cache

from mail_sending_service.views import ViewBase
from mail_sending_service.mail import senders


CONFIG_APP_SECTION = "Server"
CACHE_CONFIG_SECTION = "Cache"
VIEWS_SECTION = "Views"


def create_app(config=None):
    app = Flask(__name__)
    cache = init_cache(app, config)
    mail_senders = init_mail_senders(app, config)
    init_views(app, config, cache=cache, senders=mail_senders)
    return app


def init_cache(app, config):
    config = config[CACHE_CONFIG_SECTION]
    config = {k.upper(): v for k, v in config.items()}
    cache = Cache(config=config)
    cache.init_app(app)
    return cache

def init_views(app, config, **kwargs):
    ViewBase.init_app(app, **{"config": config[VIEWS_SECTION], **kwargs})


def init_mail_senders(app, config):
    mail_senders = []
    mail_senders.append(
        senders.SendGridSender(app, config[senders.SendGridSender.config_section()]))
    mail_senders.append(
        senders.MailgunSender(app, config[senders.MailgunSender.config_section()]))
    return mail_senders