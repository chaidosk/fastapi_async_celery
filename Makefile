test:
	poetry run python -m pytest tests

build:
	docker-compose build

up: build
	docker-compose up -d