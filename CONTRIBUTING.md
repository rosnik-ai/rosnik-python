# Contributing to rosnik-python

## Development Environment

To install dependencies, including `--all-extras` so that OpenAI and other plugins are picked up:

```
poetry install --all-extras
```

## Building

We use Poetry as our package toolchain:

```
poetry build
```

## Testing

We use `pytest-recording` to minimize outbound HTTP requests during tests.

To run tests:

```
poetry run pytest
```

## Versioning

We follow [semver](https://semver.org/).
