# rosnik-python

## Getting started

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


## TODO
- [ ] Rip HTTP request headers somehow (user agent, response code)
- [ ] Support streams
- [x] Support chat completion (OAI)
- [ ] Support Anthropic
- [ ] Support Cohere
- [ ] Support sync mode
- [ ] Support guidance
- [ ] Allow for debug logs to be printed