from celery import Celery
from fastapi_async_celery.config import settings
from fastapi_async_celery.s3_char_count.batch_service import BatchService


def create_celery_app(
    celery_app=None,
    db_url: str = settings.DATABASE_URL,
) -> Celery:
    if celery_app is None:
        celery_app = Celery(broker=settings.CELERY_CONFIG.broker_url)

        celery_app.config_from_object(settings.CELERY_CONFIG)

    batch_service = BatchService(celery_app=celery_app)
    batch_service.register_tasks(db_url=db_url)
    return celery_app
