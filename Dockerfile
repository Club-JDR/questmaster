FROM node:24-alpine AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY assets/ ./assets/
COPY vite.config.js ./
COPY website/templates/ ./website/templates/
RUN npm run build


FROM python:3.14-alpine3.23 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /bin/uv
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
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-emit-project -o /tmp/requirements.txt \
  && pip install --require-hashes --only-binary :all: --no-cache-dir --prefix=/install -r /tmp/requirements.txt


FROM python:3.14-alpine3.23 AS base
WORKDIR /questmaster
RUN apk add --no-cache \
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
  TZ=Europe/Paris \
  MUSL_LOCPATH="/usr/share/i18n/locales/musl" \
  LANG=fr_FR.UTF-8 \
  LANGUAGE=fr_FR:fr \
  LC_ALL=fr_FR.UTF-8
COPY --from=builder --chmod=555 /install /usr/local
COPY --chmod=555 config ./config
COPY --chmod=555 migrations/ ./migrations
COPY --chmod=555 website/ ./website
COPY --chmod=555 questmaster.py ./
COPY --from=frontend-builder --chmod=555 /app/website/static/dist/ ./website/static/dist/

FROM base AS app-test
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-emit-project --extra test --extra lint -o /tmp/requirements-test.txt \
  && pip install --require-hashes --only-binary :all: --no-cache-dir -r /tmp/requirements-test.txt
COPY --chmod=555 tests/ ./tests

FROM base AS app
COPY --chmod=555 entrypoint.sh /entrypoint.sh
USER questmaster
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1
ENTRYPOINT ["/entrypoint.sh"]
