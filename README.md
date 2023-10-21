## Prerequisites

1. You need to have python3.11 installed in your system
2. The repo has been build with poetry version 1.5.1
3. You need to have docker installed

## Execute tests

You can run all tests by

```sh
make test
```

## Run app in docker

You can build the docker image with

```sh
make build
```

And you can start it with

```sh
make up
```

After the application is up you can see the API specs under [http://localhost:8080/docs](http://localhost:8080/docs)

## Create new DB migrations

Start the database

```sh
make up-postgres
```

Apply existing migrations

```sh
make alembic-migrate
```

Either change an existing db model or add a new one. If you add a new one import it also in `fastapi_async_celery/config/alembic/env.py`.

Then run the script to create the migration file

```sh
make alembic-autogenerate
```

A new migration file will appear under the `fastapi_async_celery/config/alembic/versions`
