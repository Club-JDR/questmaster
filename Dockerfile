FROM python:3.13-alpine AS builder

WORKDIR /app
RUN apk add --no-cache \
  bash \
  build-base \
  jpeg-dev \
  libffi-dev \
  libxml2-dev \
  libxslt-dev \
  postgresql-dev \
  python3-dev \
  tzdata \
  zlib-dev
COPY pyproject.toml .
RUN mkdir -p website && touch website/__init__.py \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir --prefix=/install .


FROM python:3.13-alpine AS base
WORKDIR /questmaster
RUN apk add --no-cache \
  bash \
  curl \
  jpeg \
  libffi \
  libpq \
  libxml2 \
  libxslt \
  musl-locales \
  musl-locales-lang \
  tzdata \
  zlib \
  && adduser -D -g '' questmaster
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  MUSL_LOCPATH="/usr/share/i18n/locales/musl" \
  LANG=fr_FR.UTF-8 \
  LANGUAGE=fr_FR:fr \
  LC_ALL=fr_FR.UTF-8
COPY --from=builder /install /usr/local
COPY questmaster.py config.py ./
COPY website/ ./website
COPY migrations/ ./migrations
RUN chown -R questmaster:questmaster /questmaster

FROM base AS app-test
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[test,lint]"
COPY tests/ ./tests

FROM base AS app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown questmaster:questmaster /entrypoint.sh
USER questmaster
EXPOSE 8000
CMD ["sh", "-c", "/entrypoint.sh"]
