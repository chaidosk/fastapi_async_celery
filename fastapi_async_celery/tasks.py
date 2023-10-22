import asyncio
import logging
from asgiref.sync import async_to_sync
from fastapi_async_celery.config.depends import async_db_context_manager

logger = logging.getLogger(__name__)


async def _handle_batch(id, db_url):
    _async_db_context_manager = async_db_context_manager(db_url)
    async with _async_db_context_manager() as db:
        await asyncio.sleep(2)
        logger.info(f"_handle_batch for {id} done!")


def register_handle_batch(app, db_url):
    @app.task(name="handle_batch")
    def handle_batch(id):
        handle_retrieval_sync = async_to_sync(_handle_batch)
        handle_retrieval_sync(id, db_url)
