from logging import getLogger
from threading import current_thread, local
from typing import AsyncContextManager
from fastapi_async_celery.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

_THREAD_LOCAL_ASYNC_ENGINES = local()
logger = getLogger(__name__)


def _get_or_create_async_engine(db_url: str) -> AsyncEngine:
    _thread = current_thread()
    if not hasattr(_THREAD_LOCAL_ASYNC_ENGINES, "engines"):
        _THREAD_LOCAL_ASYNC_ENGINES.engines = {}
    if db_url in _THREAD_LOCAL_ASYNC_ENGINES.engines:
        logger.debug(f"Found engine in thread {_thread.name} - {_thread.ident}")
        return _THREAD_LOCAL_ASYNC_ENGINES.engines[db_url]  # type: ignore
    logger.info(f"Create engine in thread {_thread.name} - {_thread.ident}")
    engine: AsyncEngine = create_async_engine(db_url, pool_pre_ping=True)
    _THREAD_LOCAL_ASYNC_ENGINES.engines[db_url] = engine
    return engine


def async_session_maker(db_url: str) -> sessionmaker:
    async_engine: AsyncEngine = _get_or_create_async_engine(db_url)
    _async_session_maker = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    return _async_session_maker


def async_db_context_manager(
    db_url: str = settings.DATABASE_URL,
):
    class _AsyncDBContextManager(AsyncContextManager[AsyncSession]):
        def __init__(self) -> None:
            _async_session_maker = async_session_maker(db_url)
            self.db: AsyncSession = _async_session_maker()

        async def __aenter__(self) -> AsyncSession:
            return self.db

        async def __aexit__(self, *exc):
            await self.db.close()

    return _AsyncDBContextManager
