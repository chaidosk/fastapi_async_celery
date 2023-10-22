from celery import Celery
from uuid import uuid4
from fastapi_async_celery.config.async_db_context_manager import (
    async_db_context_manager,
)
from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchRegistered,
    BatchStatus,
)
from fastapi_async_celery.s3_char_count.db_model import Batch as DBBatch
from sqlalchemy import select
import asyncio
import logging
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class BatchService:
    def __init__(self, celery_app: Celery):
        self._celery_app = celery_app

    def register_tasks(self, db_url):
        @self._celery_app.task(name="handle_batch")
        def handle_batch_task(id):
            handle_retrieval_sync = async_to_sync(self._handle_batch_task)
            handle_retrieval_sync(id, db_url)

    async def _handle_batch_task(self, id, db_url):
        _async_db_context_manager = async_db_context_manager(db_url)
        async with _async_db_context_manager() as db:
            await self.handle_batch(id, db)

    async def handle_batch(self, id, db):
        await asyncio.sleep(2)
        logger.info(f"handle_batch for {id} done!")

    async def create_batch(self, s3_path, db):
        batch_id = uuid4()
        db_batch = DBBatch(id=batch_id, s3_path=s3_path, status=BatchStatus.REGISTERED)
        db.add(db_batch)
        await db.commit()
        self._celery_app.send_task(
            "handle_batch",
            kwargs={
                "id": batch_id,
            },
        )
        return Batch(id=batch_id, s3_path=s3_path, status=BatchRegistered())

    async def get_batch(self, batch_id, db):
        stmt = select(DBBatch).where(DBBatch.id == batch_id)
        result = await db.execute(stmt)

        batch_in_db = result.scalars().first()
        if batch_in_db is None:
            return None
        return Batch(
            id=batch_in_db.id, s3_path=batch_in_db.s3_path, status=BatchRegistered()
        )
