from unittest.mock import MagicMock
from celery import Celery
import pytest
from io import BytesIO
from fastapi_async_celery.s3_char_count.batch_service import BatchService
from fastapi_async_celery.s3_char_count.schema import Batch, BatchInProgress
from test_s3_helper import create_bucket


class TestHandleBatch:
    @pytest.mark.anyio
    async def test_handle_batch(
        self, localstack_session, localstack_enpoint_url, clean_db
    ):
        s3_path = f"s3://test-handle-batch"
        await create_bucket(
            session=localstack_session,
            endpoint_url=localstack_enpoint_url,
            bucket_name="test-handle-batch",
            number_of_files=3,
        )

        batch_service = BatchService(
            celery_app=MagicMock(spec=Celery),
            aioboto3_session=localstack_session,
            aws_endpoint_url=localstack_enpoint_url,
        )
        batch = await batch_service.create_batch(s3_path=s3_path, db=clean_db)
        await batch_service.handle_batch(id=batch.id, db=clean_db)
        batch = await batch_service.get_batch(batch_id=batch.id, db=clean_db)
        assert batch == Batch(
            id=batch.id,
            s3_path=s3_path,
            status=BatchInProgress(total_files=3, processed_files=0),
        )
