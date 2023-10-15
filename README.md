# rosnik-python

## Getting started

### Install

```sh
pip install --upgrade rosnik
```

### Configuration

We use environment variables to configure the SDK. 

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

Then in your application code:

```py
import rosnik
rosnik.init()
```

## Integrations

Please let us know if there are other providers that would be helpful to have automatic instrumentation.

### AI Providers

* OpenAI: we support tracking Completion and ChatCompletion creations

### Web Frameworks

* Flask: we have a Flask extension to automatically setup the SDK and link events to client-side metadata (browser SDK coming soon)

```py
from rosnik import flask_rosnik

rosnik_extension = flask_rosnik.FlaskRosnik()
# rosnik.init happens here
rosnik_extension.init_app(app)
```

## License

Licensed under the MIT license. See [LICENSE](./LICENSE).

## Interested in learning more?

Send us an email at hello@rosnik.ai!