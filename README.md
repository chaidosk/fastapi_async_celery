## Prerequisites

1. You need to have python3.11 installed in your system
2. The repo has been build with poetry version 1.5.1

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
