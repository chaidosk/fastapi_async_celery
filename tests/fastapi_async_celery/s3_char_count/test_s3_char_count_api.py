from unittest import mock
from httpx import AsyncClient
import pytest

from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchIn,
    BatchRegistered,
    BatchStatus,
)


class TestS3CharCountApi:
    @pytest.mark.anyio
    async def test_create_batch(self, async_client: AsyncClient):
        s3_path = "s3://bucket/key"
        response = await async_client.post(
            url="v1/s3_char_count/batch",
            json=BatchIn(s3_path=s3_path).model_dump(),
        )
        assert response.status_code == 200
        assert response.json() == {
            "s3_path": s3_path,
            "status": {"status": BatchStatus.REGISTERED.value},
            "id": mock.ANY,
        }
