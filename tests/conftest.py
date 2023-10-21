import asyncpg
import httpx
import pytest
from sqlalchemy import make_url
from fastapi_async_celery.config.depends import get_db_url
from fastapi_async_celery.main import app
from fastapi_async_celery.config.db_model_base import Base
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


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


@pytest.fixture(scope="function")
async def app_with_test_db(db_dsn, reset_db):
    def override_get_db_url():
        return db_dsn

    app.dependency_overrides[get_db_url] = override_get_db_url
    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(app_with_test_db):
    async with httpx.AsyncClient(
        app=app_with_test_db, base_url="http://test"
    ) as client:
        yield client
