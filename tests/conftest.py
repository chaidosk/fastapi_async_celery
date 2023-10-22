from unittest.mock import MagicMock
import asyncpg
from celery import Celery
import httpx
import pytest
from sqlalchemy import make_url
from fastapi_async_celery.config.depends import get_celery_app, get_db_url
from fastapi_async_celery.create_celery_app import create_celery_app
from fastapi_async_celery.main import app
from fastapi_async_celery.config.db_model_base import Base
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine
from celery.signals import task_postrun
import time

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def localstack_sqs():
    with LocalStackContainer(image="localstack/localstack") as localstack:
        localstack.with_services("sqs")
        host = localstack.get_container_host_ip()
        port = localstack.get_exposed_port(LocalStackContainer.EDGE_PORT)
        yield f"{host}:{port}"


@pytest.fixture(scope="session")
def celery_config(localstack_sqs, executed_celery_tasks):
    @task_postrun.connect(weak=False)
    def task_postrun_handler(task_id, task, retval, state, *args, **kwargs):
        executed_celery_tasks.append(
            (task.name, kwargs["args"], kwargs["kwargs"], retval, state)
        )

    import os

    if "CELERY_BROKER_URL" in os.environ:
        os.environ.pop("CELERY_BROKER_URL")
    return {
        "broker_url": f"sqs://fake:fake@{localstack_sqs}/0",  # pragma: allowlist secret
        "broker_transport_options": {"wait_time_seconds": 2},
    }


@pytest.fixture(scope="session")
def executed_celery_tasks():
    return []


@pytest.fixture(scope="function")
def test_executed_celery_tasks(executed_celery_tasks):
    executed_celery_tasks.clear()
    return executed_celery_tasks


@pytest.fixture(scope="function")
def wait_for_task(test_executed_celery_tasks):
    def _wait_for_task(task_name, args, kwargs, retval, state, max_wait=10):
        start_time = time.monotonic()
        expected_execution = (task_name, args, kwargs, retval, state)
        while True:
            if expected_execution in test_executed_celery_tasks:
                return
            if time.monotonic() - start_time > max_wait:
                assert (
                    False
                ), f"Expected {expected_execution} found {test_executed_celery_tasks}"
            time.sleep(0.2)

    return _wait_for_task


@pytest.fixture(scope="session")
def db_dsn():
    postgres = PostgresContainer(image="postgres:14")
    postgres.start()
    _db_dsn = postgres.get_connection_url().replace("psycopg2", "asyncpg")
    yield _db_dsn


async def create_database_if_not_exists(db_dsn) -> None:
    test_database_url = make_url(db_dsn)
    try:
        await asyncpg.connect(
            host=test_database_url.host,
            port=test_database_url.port,
            user=test_database_url.username,
            password=test_database_url.password,
            database=test_database_url.database,
        )
    except asyncpg.InvalidCatalogNameError:
        sys_conn = await asyncpg.connect(
            host=test_database_url.host,
            port=test_database_url.port,
            user=test_database_url.username,
            password=test_database_url.password,
            database="template1",
        )
        await sys_conn.execute(f"CREATE DATABASE {test_database_url.database}")
        await sys_conn.close()


@pytest.fixture(scope="session")
async def db_engine(db_dsn):
    await create_database_if_not_exists(db_dsn)
    engine = create_async_engine(
        db_dsn,
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest.fixture(scope="function")
async def reset_db(db_engine):
    async with db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(scope="session")
def fac_celery_app(db_dsn, celery_session_app, celery_session_worker):
    drs_celery_app = create_celery_app(
        celery_app=celery_session_app,
        db_url=db_dsn,
    )
    celery_session_worker.reload()
    return drs_celery_app


@pytest.fixture(scope="function")
async def app_with_test_db_and_celery(db_dsn, fac_celery_app, reset_db):
    def override_get_db_url():
        return db_dsn

    def override_get_celery_app():
        return fac_celery_app

    app.dependency_overrides[get_db_url] = override_get_db_url
    app.dependency_overrides[get_celery_app] = override_get_celery_app
    yield app

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def app_with_test_db_no_celery(db_dsn, reset_db):
    def override_get_db_url():
        return db_dsn

    def override_get_celery_app():
        return MagicMock(spec=Celery)

    app.dependency_overrides[get_db_url] = override_get_db_url
    app.dependency_overrides[get_celery_app] = override_get_celery_app
    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(app_with_test_db_no_celery):
    async with httpx.AsyncClient(
        app=app_with_test_db_no_celery, base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def async_client_with_celery(app_with_test_db_and_celery):
    async with httpx.AsyncClient(
        app=app_with_test_db_and_celery, base_url="http://test"
    ) as client:
        yield client
