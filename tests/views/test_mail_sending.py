import http

from flask.globals import session
from flask.helpers import stream_with_context
from flask.views import MethodView

import pytest

from unittest import mock

from flask import Flask
from flask_caching import Cache

from mail_sending_service import app
from mail_sending_service.views import MailSender
from mail_sending_service.mail.senders import MailSendingError


TEST_CONFIG = {
    "Views": {
        "static_files_path": ""
    },
    "Cache": {
        "CACHE_TYPE": "simple",
    },
}

def create_mock_sender():
    return mock.Mock()

def create_failing_sender():
    sender = mock.Mock()
    sender.send.side_effect = MailSendingError("")
    return sender


def get_test_client(*senders):
    test_app = Flask("test_application")
    cache = app.init_cache(test_app, TEST_CONFIG)
    app.init_views(test_app, TEST_CONFIG, cache=cache, senders=senders)
    return test_app, cache


EXAMPLE_MAIL = {
    "to": "example@example.com",
    "topic": "example",
    "content": "example",
}

def send_example_mail(test_app):
    with test_app.test_client() as client:
        return client.post("/mail", json=EXAMPLE_MAIL)

def test_sending_passes_mail_to_sender():
    sender = create_mock_sender()
    test_app, _ = get_test_client(sender)
    resp = send_example_mail(test_app)
    assert resp.status_code == http.HTTPStatus.ACCEPTED
    sender.send.assert_called_once_with(*EXAMPLE_MAIL.values())


def test_sending_first_mail_sets_cache_to_default():
    test_app, cache = get_test_client(create_mock_sender())
    assert cache.get(MailSender.CURR_SENDER_KEY) is None
    send_example_mail(test_app)
    assert cache.get(MailSender.CURR_SENDER_KEY) == MailSender.DEFAULT_SENDER_INDEX

def test_empty_senders_returns_503():
    test_app, _ = get_test_client()
    resp = send_example_mail(test_app)
    assert resp.status_code == http.HTTPStatus.SERVICE_UNAVAILABLE

def test_failing_sending_to_only_returns_503():
    test_app, _ = get_test_client(create_failing_sender())
    resp = send_example_mail(test_app)
    assert resp.status_code == http.HTTPStatus.SERVICE_UNAVAILABLE

def test_failing_on_single_sender_does_not_move_index():
    test_app, cache = get_test_client(create_failing_sender())
    resp = send_example_mail(test_app)
    assert cache.get(MailSender.CURR_SENDER_KEY) == 0

def test_failing_sending_to_first_provide_moves_to_the_next_one():
    senders = [create_failing_sender(), create_mock_sender()]
    test_app, cache = get_test_client(*senders)
    resp = send_example_mail(test_app)
    assert resp.status_code == http.HTTPStatus.ACCEPTED
    for s in senders:
        s.send.assert_called_once_with(*EXAMPLE_MAIL.values())

def test_failing_sending_to_first_provide_moves_more_than_once():
    senders = [
        create_failing_sender(),
        create_failing_sender(),
        create_failing_sender(),
        create_mock_sender()
    ]
    test_app, cache = get_test_client(*senders)
    resp = send_example_mail(test_app)
    assert resp.status_code == http.HTTPStatus.ACCEPTED
    for s in senders:
        s.send.assert_called_once_with(*EXAMPLE_MAIL.values())

def test_failing_sending_moves_sender_index():
    test_app, cache = get_test_client(create_failing_sender(), create_mock_sender())
    assert cache.get(MailSender.CURR_SENDER_KEY) is None
    send_example_mail(test_app)
    assert cache.get(MailSender.CURR_SENDER_KEY) == 1

def test_failing_sending_moves_sender_index_more_than_one():
    test_app, cache = get_test_client(
        create_failing_sender(),
        create_failing_sender(),
        create_mock_sender(),
        create_failing_sender())
    assert cache.get(MailSender.CURR_SENDER_KEY) is None
    send_example_mail(test_app)
    assert cache.get(MailSender.CURR_SENDER_KEY) == 2

def test_view_picks_up_from_last_working_sender():
    senders = [
        create_failing_sender(),
        create_mock_sender(),
        create_failing_sender(),
    ]
    test_app, _ = get_test_client(*senders)
    send_example_mail(test_app)
    send_example_mail(test_app)
    senders[0].send.assert_called_once_with(*EXAMPLE_MAIL.values())
    senders[1].send.assert_has_calls([
        mock.call(*EXAMPLE_MAIL.values()),
        mock.call(*EXAMPLE_MAIL.values())])
    senders[2].send.assert_not_called()

def test_picking_up_from_last_working_sender_does_not_change_index():
    senders = [
        create_failing_sender(),
        create_mock_sender(),
        create_failing_sender(),
    ]
    test_app, cache = get_test_client(*senders)
    send_example_mail(test_app)
    assert cache.get(MailSender.CURR_SENDER_KEY) == 1
    send_example_mail(test_app)
    assert cache.get(MailSender.CURR_SENDER_KEY) == 1

def test_all_failing_senders_returns_503():
    test_app, _ = get_test_client(
        create_failing_sender(),
        create_failing_sender(),
        create_failing_sender())
    resp = send_example_mail(test_app)
    assert resp.status_code == http.HTTPStatus.SERVICE_UNAVAILABLE

def test_all_failing_senders_leave_index_in_valid_state():
    senders = [
        create_failing_sender(),
        create_failing_sender(),
        create_failing_sender()]
    test_app, cache = get_test_client(*senders)
    send_example_mail(test_app)
    assert 0 <= cache.get(MailSender.CURR_SENDER_KEY) < len(senders)

def test_missing_key_returns_400():
    test_app, _ = get_test_client()
    mail_template = EXAMPLE_MAIL.copy()
    for key in {"to", "topic", "content"}:
        mail = mail_template.copy()
        del mail[key]
        with test_app.test_client() as client:
            resp = client.post("/mail", json=mail)
        assert resp.status_code == http.HTTPStatus.BAD_REQUEST
        assert resp.data.decode("utf-8") == f"Missing key '{key}'"

def test_non_json_request_returns_400():
    test_app, _ = get_test_client()
    with test_app.test_client() as client:
        resp = client.post("/mail", data=EXAMPLE_MAIL)
    assert resp.status_code == http.HTTPStatus.BAD_REQUEST
    assert resp.data.decode("utf-8") == "Request is not a json"

def test_additional_key_returns_400():
    test_app, _ = get_test_client()
    mail = EXAMPLE_MAIL.copy()
    mail['invalid_key'] = "example value"
    with test_app.test_client() as client:
        resp = client.post("/mail", json=mail)
    assert resp.status_code == http.HTTPStatus.BAD_REQUEST
    assert resp.data.decode("utf-8") == "Illegal key 'invalid_key'"

def test_empty_json_returns_400():
    test_app, _ = get_test_client()
    with test_app.test_client() as client:
        resp = client.post("/mail", data={})
    assert resp.status_code == http.HTTPStatus.BAD_REQUEST
