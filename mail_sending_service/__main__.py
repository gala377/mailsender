from mail_sending_service import app


def run_server():
    server = app.create_app(None)
    server.run()

if __name__ == "__main__":
    run_server()