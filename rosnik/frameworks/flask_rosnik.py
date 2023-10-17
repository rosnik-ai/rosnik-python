import logging
import warnings

from rosnik import client, headers, state

try:
    from flask import request
except ImportError:
    request = None

logger = logging.getLogger(__name__)


def _before_request():
    # Import this JIT to avoid warning / errors for non-Flask environments.
    if request is None:
        warnings.warn("Could not import flask.request")

    journey_id = request.headers.get(headers.JOURNEY_ID_KEY)
    if journey_id is None:
        journey_id = state.create_journey_id()
    state.store(state.State.JOURNEY_ID, journey_id)

    interaction_id = request.headers.get(headers.INTERACTION_ID_KEY)
    state.store(state.State.USER_INTERACTION_ID, interaction_id)

    device_id = request.headers.get(headers.DEVICE_ID_KEY)
    state.store(state.State.DEVICE_ID, device_id)


def _annotate_response_headers(response):
    response.headers[headers.JOURNEY_ID_KEY] = state.get_journey_id()
    return response


class FlaskRosnik:
    def __init__(
        self, app=None, api_key=None, sync_mode=None, environment=None, event_context_hook=None
    ):
        self.api_key = api_key
        self.sync_mode = sync_mode
        self.environment = environment
        self.event_context_hook = event_context_hook
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(_before_request)
        app.after_request(_annotate_response_headers)
        client.init(
            api_key=self.api_key,
            sync_mode=self.sync_mode,
            environment=self.environment,
            event_context_hook=self.event_context_hook,
        )
