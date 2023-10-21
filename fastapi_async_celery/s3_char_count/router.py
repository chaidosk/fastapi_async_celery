from uuid import uuid4
from fastapi import APIRouter, status

from fastapi_async_celery.s3_char_count.schema import Batch, BatchIn, BatchRegistered

router = APIRouter()


@router.post(
    "/s3_char_count/batch",
    status_code=status.HTTP_200_OK,
    response_model=Batch,
)
async def create_batch(batch_in: BatchIn) -> Batch:
    return Batch(id=uuid4(), s3_path=batch_in.s3_path, status=BatchRegistered())
