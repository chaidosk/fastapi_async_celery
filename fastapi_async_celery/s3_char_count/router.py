from uuid import UUID, uuid4
from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from fastapi_async_celery.config.depends import get_celery_app, get_db

from fastapi_async_celery.s3_char_count.schema import (
    Batch,
    BatchIn,
    BatchRegistered,
    BatchStatus,
)
from fastapi_async_celery.s3_char_count.db_model import Batch as DBBatch
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
    celery_app: Celery = Depends(get_celery_app),
) -> Batch:
    batch_id = uuid4()
    db_batch = DBBatch(
        id=batch_id, s3_path=batch_in.s3_path, status=BatchStatus.REGISTERED
    )
    db.add(db_batch)
    await db.commit()
    celery_app.send_task(
        "handle_batch",
        kwargs={
            "id": batch_id,
        },
    )
    return Batch(id=batch_id, s3_path=batch_in.s3_path, status=BatchRegistered())


@router.get(
    "/s3_char_count/batch/{id}", status_code=status.HTTP_200_OK, response_model=Batch
)
async def get_batch(id: UUID, db: AsyncSession = Depends(get_db)) -> Batch:
    stmt = select(DBBatch).where(DBBatch.id == id)
    result = await db.execute(stmt)

    batch_in_db = result.scalars().first()
    if batch_in_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    return Batch(
        id=batch_in_db.id, s3_path=batch_in_db.s3_path, status=BatchRegistered()
    )
