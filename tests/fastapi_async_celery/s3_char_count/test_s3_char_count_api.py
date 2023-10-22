from unittest import mock
from httpx import AsyncClient
import pytest
from uuid import UUID

from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchIn,
    BatchRegistered,
    BatchStatus,
)


class TestS3CharCountApi:
    @pytest.mark.anyio
    async def test_create_batch(
        self, async_client_with_celery: AsyncClient, wait_for_task
    ):
        s3_path = "s3://bucket/key"
        response = await async_client_with_celery.post(
            url="v1/s3_char_count/batch",
            json=BatchIn(s3_path=s3_path).model_dump(),
        )
        assert response.status_code == 200
        assert response.json() == {
            "s3_path": s3_path,
            "status": {"status": BatchStatus.REGISTERED.value},
            "id": mock.ANY,
        }
        batch_id = UUID(response.json()["id"])
        wait_for_task(
            task_name="handle_batch",
            args=[],
            kwargs={
                "id": batch_id,
            },
            retval=None,
            state="SUCCESS",
            max_wait=3,
        )

    @pytest.mark.anyio
    async def test_create_and_retrieve_batch(self, async_client: AsyncClient):
        s3_path = "s3://bucket/key"
        response = await async_client.post(
            url="v1/s3_char_count/batch",
            json=BatchIn(s3_path=s3_path).model_dump(),
        )
        batch_id = response.json()["id"]
        response = await async_client.get(url=f"v1/s3_char_count/batch/{batch_id}")
        assert response.status_code == 200
        assert response.json() == {
            "s3_path": s3_path,
            "status": {"status": BatchStatus.REGISTERED.value},
            "id": mock.ANY,
        }
