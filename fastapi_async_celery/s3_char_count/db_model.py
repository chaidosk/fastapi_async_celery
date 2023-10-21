from sqlalchemy import Column, Enum, String

from sqlalchemy.dialects.postgresql import UUID
from fastapi_async_celery.config.db_model_base import Base

from fastapi_async_celery.s3_char_count.schema import BatchStatus


class Batch(Base):
    id = Column(UUID, primary_key=True, index=True)
    s3_path = Column(String)
    status = Column(Enum(BatchStatus))
