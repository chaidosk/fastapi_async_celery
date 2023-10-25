import asyncio
import random
from celery import Celery
from uuid import uuid4
from fastapi_async_celery.config.async_db_context_manager import (
    async_db_context_manager,
)
from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchDone,
    BatchRegistered,
    BatchInProgress,
    BatchStatus,
)
from fastapi_async_celery.s3_char_count.db_model import Batch as DBBatch
from sqlalchemy import select, update
from aioboto3 import Session
import logging
from asgiref.sync import async_to_sync
import os

logger = logging.getLogger(__name__)

MIN_SLEEP_DURATION = int(os.getenv("MIN_SLEEP_DURATION", "1"))
MAX_SLEEP_DURATION = int(os.getenv("MAX_SLEEP_DURATION", "1"))


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
            handle_batch_task_sync = async_to_sync(self._handle_batch_task)
            handle_batch_task_sync(id, db_url)

        @self._celery_app.task(name="handle_file")
        def handle_file_task(id, key):
            handle_file_task_sync = async_to_sync(self._handle_file_task)
            handle_file_task_sync(id, key, db_url)

    async def _handle_batch_task(self, id, db_url):
        _async_db_context_manager = async_db_context_manager(db_url)
        async with _async_db_context_manager() as db:
            await self.handle_batch(id, db)

    async def _handle_file_task(self, id, key, db_url):
        _async_db_context_manager = async_db_context_manager(db_url)
        async with _async_db_context_manager() as db:
            await self.handle_file(id, key, db)

    def _get_bucket_name(self, s3_path):
        return s3_path.split("/")[2]

    async def handle_batch(self, id, db):
        batch = await self.get_batch(batch_id=id, db=db)
        all_keys = []
        async with self._aioboto3_session.resource(
            "s3", endpoint_url=self._aws_endpoint_url
        ) as s3:
            bucket = await s3.Bucket(self._get_bucket_name(batch.s3_path))
            async for obj in bucket.objects.all():
                all_keys.append(obj.key)
        await self.update_batch_in_progress(id, len(all_keys), db)
        for key in all_keys:
            self._celery_app.send_task(
                "handle_file",
                kwargs={"id": id, "key": key},
            )
        logger.info(f"handle_batch for {id} done!")

    async def handle_file(self, id, key, db):
        sleep_duration = random.randint(MIN_SLEEP_DURATION, MAX_SLEEP_DURATION)
        logger.info(f"handle_file for {id} - {key}. Sleeping for {sleep_duration}")
        batch = await self.get_batch(batch_id=id, db=db)
        # Download file, count characters and do other things!
        await asyncio.sleep(sleep_duration)
        await self.update_batch_file_processed(batch_id=id, db=db)
        logger.info(f"handle_file for {id} - {key} Done!")

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
        elif batch_in_db.status == BatchStatus.IN_PROGRESS:
            return Batch(
                id=batch_in_db.id,
                s3_path=batch_in_db.s3_path,
                status=BatchInProgress(
                    total_files=batch_in_db.total_files,
                    processed_files=batch_in_db.processed_files,
                ),
            )
        else:
            return Batch(
                id=batch_in_db.id,
                s3_path=batch_in_db.s3_path,
                status=BatchDone(
                    total_files=batch_in_db.total_files,
                ),
            )

    async def update_batch_in_progress(self, batch_id, total_files, db):
        stmt = (
            update(DBBatch)
            .where(DBBatch.id == batch_id)
            .values(
                total_files=total_files,
                processed_files=0,
                status=BatchStatus.IN_PROGRESS,
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def update_batch_file_processed(self, batch_id, db):
        stmt = (
            update(DBBatch)
            .where(DBBatch.id == batch_id)
            .values(
                processed_files=DBBatch.processed_files + 1,
            )
        )
        await db.execute(stmt)
        batch = await self.get_batch(batch_id=batch_id, db=db)
        if batch.status.processed_files == batch.status.total_files:
            stmt = (
                update(DBBatch)
                .where(DBBatch.id == batch_id)
                .values(
                    status=BatchStatus.DONE,
                )
            )
            await db.execute(stmt)

        await db.commit()
