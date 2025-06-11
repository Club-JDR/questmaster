FROM python:3.11-slim AS base

# Set work directory and environment
WORKDIR /questmaster
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  DEBIAN_FRONTEND=noninteractive \
  LANG=fr_FR.UTF-8 \
  LANGUAGE=fr_FR:fr \
  LC_ALL=fr_FR.UTF-8

# System packages in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  locales \
  && sed -i 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
  && locale-gen fr_FR.UTF-8 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && adduser --system --group questmaster

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY questmaster.py config.py ./
COPY website/ ./website

# Set permissions
RUN chown -R questmaster:questmaster /questmaster

# Test image
FROM base AS app-test
COPY tests/requirements.txt test-requirements.txt
RUN pip install -r test-requirements.txt
COPY tests/ ./tests

# Final production image
FROM base AS app
USER questmaster
EXPOSE 8000
CMD ["gunicorn", "--workers=2", "--threads=4", "--bind", "0.0.0.0:8000", "questmaster:app"]
