
# Welcome to your Python project!

This project is set up Python project with dev tooling pre-configured

* black
* flake8
* isort
* mypy
* VS Code support

## Setup

```shell
# create virtualenv
$ poetry shell

# install dependencies
(.venv)$ poetry install

```

## Develop the code for the stack

```shell
# run unit tests
pytest
```

## integrate with New Relic

Follow the simple steps below. See [offical Github repo](https://github.com/newrelic/newrelic-lambda-cli#installation) for details.

```shell
pip3 install newrelic-lambda-cli

newrelic-lambda integrations install --nr-account-id <newrelic_account id> --nr-api-key <newrelic_api key>
```
