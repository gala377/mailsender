import os

from configparser import ConfigParser

from mail_sending_service import app


def run_server():
    config_path = os.environ['MSS_CONFIG_PATH']
    config = ConfigParser()
    config.read(config_path)
    server = app.create_app(config)
    server.run()

if __name__ == "__main__":
    run_server()