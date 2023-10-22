FROM python:3.11.6-alpine3.18

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.5.1 \
    PYCURL_SSL_LIBRARY=openssl

RUN pip install "poetry==$POETRY_VERSION"

RUN apk add --no-cache libcurl
RUN apk add --no-cache --virtual .build-deps build-base curl-dev

WORKDIR /app
COPY compose/migrate /app/
RUN chmod +x migrate
COPY compose/start /app/
RUN chmod +x start
COPY compose/start-worker /app/
RUN chmod +x start-worker
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-ansi

COPY fastapi_async_celery/ /app/fastapi_async_celery/