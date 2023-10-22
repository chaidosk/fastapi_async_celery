from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_async_celery.config.depends import (
    get_batch_service,
    get_db,
)
from fastapi_async_celery.s3_char_count.batch_service import BatchService

from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchIn,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/s3_char_count/batch",
    status_code=status.HTTP_200_OK,
    response_model=Batch,
)
async def create_batch(
    batch_in: BatchIn,
    db: AsyncSession = Depends(get_db),
    batch_service: BatchService = Depends(get_batch_service),
) -> Batch:
    return await batch_service.create_batch(batch_in.s3_path, db)


@router.get(
    "/s3_char_count/batch/{id}", status_code=status.HTTP_200_OK, response_model=Batch
)
async def get_batch(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    batch_service: BatchService = Depends(get_batch_service),
) -> Batch:
    batch_in_db = await batch_service.get_batch(id, db)
    if batch_in_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    return batch_in_db
