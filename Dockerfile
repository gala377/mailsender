FROM python:3.8

RUN mkdir /app
RUN mkdir /conf

VOLUME ["/conf"]

WORKDIR /app

COPY uwsgi.ini /etc/uwsgi/

RUN pip install poetry
RUN poetry config virtualenvs.create false
COPY . /app/

RUN poetry install --no-dev

ENV PORT = 8080
ENV MSS_CONFIG_PATH="/app/conf.ini"

EXPOSE 8080

CMD ["uwsgi", "/etc/uwsgi/uwsgi.ini"]
