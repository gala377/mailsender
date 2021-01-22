import http

import flask

from flask import request
from flask.views import MethodView

from mail_sending_service.mail import senders


class ViewBase(MethodView):
    name = None
    route = None

    __subclasses = []

    def __init__(self, *args, **kwargs):
        super().__init__()

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if cls.name is None:
            raise ValueError("Views `name` has o be set")
        if cls.route is None:
            raise ValueError("Views `route` has to be set")
        cls.__subclasses.append(cls)

    @classmethod
    def init_app(cls, app, *args):
        for view in cls.__subclasses:
            view.logger = app.logger
            app.add_url_rule(
                view.route,
                view_func=view.as_view(view.name, *args))


class HelloView(ViewBase):
    name = "hello"
    route = "/hello"

    def get(self):
        return "Hello World!"


class RequestValidationError(Exception):
    def __init__(self, message, *args):
        super().__init__(*args)
        self.message = message


class MailSender(ViewBase):
    name = "mail"
    route = "/mail"

    CURR_SENDER_KEY = "CURRENT_SENDER"
    DEFAULT_SENDER_INDEX = 0

    def __init__(self, cache, senders):
        self.cache = cache
        self.email_senders = senders

    def post(self):
        content = request.json
        try:
            self._verify_request(content)
        except RequestValidationError as e:
            return (e.message, http.HTTPStatus.BAD_REQUEST)
        return self._try_sending_email(content)

    def _verify_request(self, req):
        # todo
        pass

    def _try_sending_email(self, req):
        sender_index = self._get_sender_index()
        sent_on = self._fallbackable_email_send(req, sender_index)
        if sent_on is None:
           return ("Could not sent an email", http.HTTPStatus.SERVICE_UNAVAILABLE)
        if sent_on != sender_index:
            self._set_sender_index(self, sent_on)
        return ("", http.HTTPStatus.OK)

    def _get_sender_index(self):
        index_store = self.cache
        sender_index = index_store.get(self.CURR_SENDER_KEY)
        if sender_index is None:
            index_store.set(self.CURR_SENDER_KEY, self.DEFAULT_SENDER_INDEX)
            sender_index = self.DEFAULT_SENDER_INDEX
        return sender_index

    def _set_sender_index(self, value):
        index_store = self.cache
        index_store.set(self.CURR_SENDER_KEY, value)

    def _fallbackable_email_send(self, req, starting_index):
        made_full_cycle = False
        senders_list = self.email_senders
        sender_index = starting_index
        while not made_full_cycle:
            try:
                senders_list[sender_index].send(
                    req['to'], req['topic'], req['content'])
            except senders.MailSendingError as e:
                self.logger.warning("Error while sending email: %a", e)
                sender_index = (sender_index + 1) % len(senders_list)
                made_full_cycle = senders_list == starting_index
            else:
                return sender_index
        return None

