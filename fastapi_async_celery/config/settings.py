import os
from typing import List, Optional

from pydantic import BaseModel

DATABASE_SYNC_URL = os.environ.get(
    "DATABASE_SYNC_URL", "postgresql://postgres:pass@localhost/fastapi_async_celery"
)

DATABASE_URL = DATABASE_SYNC_URL.replace("postgresql://", "postgresql+asyncpg://")


class CeleryConfig(BaseModel):
    timezone: str = "UTC"
    broker_url: str = os.environ.get(
        "CELERY_BROKER_URL", "sqs://fake:fake@localstack:4566/0"
    )
    accept_content: List[str] = ["json"]
    task_serializer: str = "json"
    result_serializer: str = "json"
    task_time_limit: int = 10 * 60 * 60
    result_expires: int = 60 * 24 * 7
    result_backend: Optional[str] = ""
    broker_transport_options: dict = {
        # 'visibility_timeout': 3600,
        "polling_interval": 10,
        "wait_time_seconds": 10,  # valid values: 0 - 20
        # 'region': 'us-east-1'
        "predefined_queues": {
            "celery": {
                "url": os.environ.get(
                    "CELERY_QUEUE_URL",
                    "http://localstack:4566/000000000000/SqsQueue",
                ),
            }
        },
    }
    broker_transport: str = "sqs"
    worker_send_task_events: bool = True
    worker_max_tasks_per_child: bool = 500


CELERY_CONFIG: CeleryConfig = CeleryConfig()
