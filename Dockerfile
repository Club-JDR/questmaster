FROM python:3.11-slim AS base
WORKDIR /questmaster
RUN apt update && apt upgrade -y
RUN apt install -y locales && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

RUN apt install -y build-essential gcc
RUN python -m pip install --upgrade pip

ADD requirements.txt /questmaster/requirements.txt
RUN python -m pip install -r requirements.txt
ADD questmaster.py  /questmaster/questmaster.py
COPY website/ /questmaster/website

FROM base AS app-test

ADD tests/requirements.txt /questmaster/test-requirements.txt
RUN python -m pip install -r test-requirements.txt
COPY tests/ /questmaster/tests

FROM base AS app

EXPOSE 8000
CMD [ "gunicorn",  "--bind",  "0.0.0.0:8000",  "questmaster:app"]