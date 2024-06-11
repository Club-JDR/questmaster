FROM python:3.11-slim AS base
WORKDIR /questmaster
RUN adduser --system --group questmaster

RUN apt update && apt upgrade -y
RUN apt install -y --no-install-recommends locales && \
  sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
  dpkg-reconfigure --frontend=noninteractive locales

FROM base AS build

RUN apt install -y --no-install-recommends build-essential gcc && apt clean
RUN python -m pip install --upgrade pip

FROM build AS code
ADD requirements.txt /questmaster/requirements.txt
RUN python -m pip install -r requirements.txt
ADD questmaster.py  /questmaster/questmaster.py
COPY website/ /questmaster/website
RUN chown -R questmaster: /questmaster

FROM code AS app-test
ADD tests/requirements.txt /questmaster/test-requirements.txt
RUN python -m pip install -r test-requirements.txt
COPY tests/ /questmaster/tests

FROM code AS app
USER questmaster
EXPOSE 8000
CMD [ "gunicorn",  "--bind",  "0.0.0.0:8000",  "questmaster:app"]