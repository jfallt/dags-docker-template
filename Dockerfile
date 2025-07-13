# Stage 1: Base Image
FROM python:3.12 AS base

# Build args
ARG USER=airflow
ENV USER=${USER}

# Setup non-root user
RUN groupadd --gid 1002 ${USER} \
    && useradd --uid 1002 --gid 1002 -m ${USER}

# add additional apt packages here
RUN apt-get update && \
    apt-get install -y unixodbc-dev odbcinst iptables

# Stage 2: Setup Certificates
FROM base AS certs

# Packages updates and certificates
# if you have certs you need to install, add them here
# COPY setup/cert.cer /etc/ssl/certs/ca-certificates.crt

# Stage 3: Builder
FROM certs AS builder

# Install poetry
COPY /.netrc /root/.netrc
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.7.1 \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN pip install \
    "poetry==$POETRY_VERSION"

# Install required packages
WORKDIR /app
COPY poetry.lock .
COPY pyproject.toml .
RUN poetry config virtualenvs.in-project true \
    && poetry install --only main --no-root

# Stage 4: Source
FROM builder AS source

# Copy source files over
ENV PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /app \
    && chown $USER /app

COPY ./setup/Macquarie-CA-Bundle.cer /app/
COPY ./entrypoint/ /app/entrypoint/
COPY ./src/ /app/src/
WORKDIR /app/

# Stage 5: Pytest
FROM source AS pytest

COPY ./tests/ /app/tests/
RUN poetry install --with dev --no-root \
    && python3 -m pytest

# Stage 6: Final Image
FROM source AS final

# Update certificates
RUN apt install -y ca-certificates \
    && update-ca-certificates --fresh

ENV SSL_CERT_DIR=/etc/ssl/certs
ENV AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV PYTHONPATH="/app/src/:$PYTHONPATH"

# SPECIFY NON ROOT USER!
USER $USER

ENTRYPOINT ["python", "/app/entrypoint/app.py"]
