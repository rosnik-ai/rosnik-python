# rosnik-python

[![Build Status](https://github.com/rosnik-ai/rosnik-python/actions/workflows/test.yaml/badge.svg)](https://github.com/rosnik-ai/rosnik-python/actions/workflows/test.yaml)
[![PyPi page link -- version](https://img.shields.io/pypi/v/rosnik.svg)](https://pypi.python.org/pypi/rosnik)
![Python version](https://img.shields.io/badge/python-3.10-blue)
![Python version](https://img.shields.io/badge/python-3.11-blue)
![Python version](https://img.shields.io/badge/python-3.12-blue)


## Getting started

### Install

```sh
pip install --upgrade rosnik
```

### Configuration

Then in your application code:

```py
import rosnik
rosnik.init(api_key="api-key", environment="development")
```

#### Environment Variables

Please note that environment variables will override configuration values passed in via initialization.

```sh
# This is required to authenticate against our event ingestion tier
ROSNIK_API_KEY=

# This is optional and will mark events to the application environment (e.g. development, staging, production).
# If not supplied, it will go into a default environment.
ROSNIK_ENVIRONMENT=

# Setting this to 1 will send events on the foreground thread.
# If it's not supplied or set to 0, it will send events on a 
# background thread.
ROSNIK_SYNC_MODE=
```

## Integrations

Please let us know if there are other providers that would be helpful to have automatic instrumentation.

### AI Providers

* OpenAI: we support tracking Completion and ChatCompletion creations

### Web Frameworks

Flask:

```py
from rosnik import flask_rosnik

rosnik_extension = flask_rosnik.FlaskRosnik(api_key="api-key", environment="development")
# rosnik.init happens here
rosnik_extension.init_app(app)
```

Django: 

```py
# settings.py

MIDDLEWARE = [
    # ...other middleware
    'rosnik.frameworks.django.rosnik_middleware'
]

# The middleware pulls from settings on init.
ROSNIK_API_KEY="api-key"
ROSNIK_ENVIRONMENT="development"
```

## License

Licensed under the MIT license. See [LICENSE](./LICENSE).

## Interested in learning more?

Send us an email at hello@rosnik.ai!