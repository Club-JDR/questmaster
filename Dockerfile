FROM python:3.11-slim AS base
WORKDIR /app
RUN apt update && apt upgrade -y
RUN apt install -y locales && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

RUN apt install -y build-essential gcc
RUN python -m pip install --upgrade pip

ADD requirements.txt /app/requirements.txt
RUN python -m pip install -r requirements.txt
ADD questmaster.py  /app/questmaster.py
COPY api/ /app/api

FROM base AS api-test

ADD tests/requirements.txt /app/test-requirements.txt
RUN python -m pip install -r test-requirements.txt
COPY tests/ /app/tests

FROM base AS api

EXPOSE 8000
CMD [ "gunicorn",  "--bind",  "0.0.0.0:8000",  "questmaster:app"]