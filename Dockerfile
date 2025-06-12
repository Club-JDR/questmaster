FROM python:3.13-slim AS base
WORKDIR /questmaster
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  DEBIAN_FRONTEND=noninteractive \
  LANG=fr_FR.UTF-8 \
  LANGUAGE=fr_FR:fr \
  LC_ALL=fr_FR.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  locales \
  && sed -i 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
  && locale-gen fr_FR.UTF-8 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && adduser --system --group questmaster
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY questmaster.py config.py ./
COPY website/ ./website
RUN chown -R questmaster:questmaster /questmaster

FROM base AS app-test
COPY tests/requirements.txt test-requirements.txt
RUN pip install -r test-requirements.txt
COPY tests/ ./tests

FROM base AS app
COPY migrations migrations
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown questmaster:questmaster /entrypoint.sh
USER questmaster
EXPOSE 8000
CMD ["sh", "-c", "/entrypoint.sh"]