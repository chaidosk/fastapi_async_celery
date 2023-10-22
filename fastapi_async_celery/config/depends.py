from fastapi import Depends
from fastapi_async_celery.config import settings
from fastapi_async_celery.config.async_db_context_manager import (
    async_db_context_manager,
)
from fastapi_async_celery.s3_char_count.batch_service import BatchService


def get_db_url() -> str:
    return str(settings.DATABASE_URL)


async def get_db(
    db_url: str = Depends(get_db_url),
):
    _async_db_context_manager = async_db_context_manager(db_url)
    async with _async_db_context_manager() as db:
        yield db


def get_celery_app():
    from fastapi_async_celery.create_celery_app import create_celery_app

    return create_celery_app()


def get_batch_service(celery_app=Depends(get_celery_app)):
    return BatchService(celery_app=celery_app)
