import os

DATABASE_SYNC_URL = os.environ.get(
    "DATABASE_SYNC_URL", "postgresql://postgres:pass@localhost/fastapi_async_celery"
)

DATABASE_URL = DATABASE_SYNC_URL.replace("postgresql://", "postgresql+asyncpg://")
