from unittest.mock import MagicMock

from celery import Celery
import pytest
from fastapi_async_celery.s3_char_count.batch_service import BatchService
from fastapi_async_celery.s3_char_count.schema import Batch, BatchDone


class TestHandleFile:
    @pytest.mark.anyio
    async def test_handle_file(self, clean_db):
        batch_service = BatchService(
            celery_app=MagicMock(spec=Celery),
            aioboto3_session=MagicMock(),
            aws_endpoint_url="",
        )
        batch = await batch_service.create_batch(s3_path="test", db=clean_db)
        await batch_service.update_batch_in_progress(
            batch_id=batch.id, total_files=3, db=clean_db
        )
        await batch_service.handle_file(id=batch.id, key="key1", db=clean_db)
        await batch_service.handle_file(id=batch.id, key="key2", db=clean_db)
        await batch_service.handle_file(id=batch.id, key="key3", db=clean_db)
        batch = await batch_service.get_batch(batch_id=batch.id, db=clean_db)
        assert batch == Batch(
            id=batch.id, s3_path="test", status=BatchDone(total_files=3)
        )
