from celery import Celery
from uuid import uuid4
from fastapi_async_celery.config.async_db_context_manager import (
    async_db_context_manager,
)
from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchRegistered,
    BatchInProgress,
    BatchStatus,
)
from fastapi_async_celery.s3_char_count.db_model import Batch as DBBatch
from sqlalchemy import select, update
from aioboto3 import Session
import logging
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class BatchService:
    def __init__(
        self, celery_app: Celery, aioboto3_session: Session, aws_endpoint_url=None
    ):
        self._celery_app = celery_app
        self._aioboto3_session = aioboto3_session
        self._aws_endpoint_url = aws_endpoint_url

    def register_tasks(self, db_url):
        @self._celery_app.task(name="handle_batch")
        def handle_batch_task(id):
            handle_retrieval_sync = async_to_sync(self._handle_batch_task)
            handle_retrieval_sync(id, db_url)

    async def _handle_batch_task(self, id, db_url):
        _async_db_context_manager = async_db_context_manager(db_url)
        async with _async_db_context_manager() as db:
            await self.handle_batch(id, db)

    def _get_bucket_name(self, s3_path):
        return s3_path.split("/")[2]

    async def handle_batch(self, id, db):
        batch = await self.get_batch(batch_id=id, db=db)
        file_count = 0
        async with self._aioboto3_session.resource(
            "s3", endpoint_url=self._aws_endpoint_url
        ) as s3:
            bucket = await s3.Bucket(self._get_bucket_name(batch.s3_path))
            async for obj in bucket.objects.all():
                file_count += 1
        await self.update_batch(id, file_count, 0, db)
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
        if batch_in_db.status == BatchStatus.REGISTERED:
            return Batch(
                id=batch_in_db.id, s3_path=batch_in_db.s3_path, status=BatchRegistered()
            )
        else:
            return Batch(
                id=batch_in_db.id,
                s3_path=batch_in_db.s3_path,
                status=BatchInProgress(
                    total_files=batch_in_db.total_files,
                    processed_files=batch_in_db.processed_files,
                ),
            )

    async def update_batch(self, batch_id, total_files, processed_files, db):
        stmt = (
            update(DBBatch)
            .where(DBBatch.id == batch_id)
            .values(
                total_files=total_files,
                processed_files=processed_files,
                status=BatchStatus.IN_PROGRESS,
            )
        )
        await db.execute(stmt)
        await db.commit()
