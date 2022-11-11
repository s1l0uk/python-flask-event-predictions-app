FROM python:3.7-alpine

RUN apk update && apk upgrade
RUN apk add --no-cache build-base libffi-dev mariadb-connector-c-dev


COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN pip install authlib

COPY src/ /src
WORKDIR /src

CMD exec gunicorn --bind 0.0.0.0:8000 app:app
