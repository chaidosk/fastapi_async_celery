test:
	poetry run python -m pytest tests

build:
	docker-compose build

up: build
	docker-compose up -d

up-postgres:
	docker-compose up -d postgres

down:
	docker-compose down

alembic-autogenerate:
	poetry run alembic -c fastapi_async_celery/config/alembic/alembic.ini revision --autogenerate

alembic-migrate:
	poetry run alembic -c fastapi_async_celery/config/alembic/alembic.ini upgrade head