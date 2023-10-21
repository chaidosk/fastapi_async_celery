from enum import Enum
from typing import Union
from pydantic import BaseModel
from uuid import UUID


class BatchIn(BaseModel):
    s3_path: str


class BatchStatus(Enum):
    REGISTERED = 0
    IN_PROGRESS = 1
    DONE = 2


class BatchRegistered(BaseModel):
    status: BatchStatus = BatchStatus.REGISTERED
    pass


class BatchInProgress(BaseModel):
    status: BatchStatus = BatchStatus.IN_PROGRESS
    total_files: int
    processed_files: int


class BatchDone(BaseModel):
    status: BatchStatus = BatchStatus.DONE
    total_files: int


class Batch(BaseModel):
    id: UUID
    s3_path: str
    status: Union[BatchRegistered, BatchInProgress, BatchDone]
