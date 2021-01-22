import http

import flask
import sendgrid
import requests

from abc import (
    ABC,
    abstractmethod,
    abstractstaticmethod,
)


class MailSendingError(Exception): ...


class BaseSender(ABC):

    def __init__(self, app, config):
        super().__init__()
        self.config = config

    @abstractstaticmethod
    def config_section(): ...

    @abstractmethod
    def send(self, to, topic, content): ...


class SendGridSender(BaseSender):

    @staticmethod
    def config_section():
        return "SendGrid"

    def send(self, to, topic, content):
        mess = sendgrid.helpers.mail.Mail(
            from_email=self.config['from_mail'],
            to_emails=to,
            subject=topic,
            html_content=content)
        try:
            client = sendgrid.SendGridAPIClient(self.config['api_key'])
            response = client.send(mess)
        except Exception as e:
            raise MailSendingError("SendGrid could not create client") from e
        if response.status_code != http.HTTPStatus.ACCEPTED:
            raise MailSendingError(
                f"SendGrid could not send an email: {response.status_code} {response.body}")


class MailgunSender(BaseSender):

    @staticmethod
    def config_section():
        return "Mailgun"

    def send(self, to, topic, content):
        resp = requests.post(
            self.config['api_url'],
            auth=('api', self.config['api_key']),
            data={
                "from": self.config['from_mail'],
                "to": [to],
                "subject": topic,
                "text": content
        })
        if resp.status_code != http.HTTPStatus.OK:
            raise MailSendingError(
                f"Mailgun could not send an email {resp.status_code} {resp.content}")