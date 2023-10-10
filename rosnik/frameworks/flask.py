import logging
from rosnik import headers, interaction, journey

logger = logging.getLogger(__name__)


def _get_journey_id():
    try:
        from flask import request
    except ImportError:
        logger.warning("flask is not installed")
    journey_id = request.headers.get(headers.JOURNEY_ID_KEY)
    interaction_id = request.headers.get(headers.INTERACTION_ID_KEY)
    journey.set_journey_id(journey_id)
    interaction.set_interaction_id(interaction_id)


def _annotate_response_headers(response):
    response.headers[headers.JOURNEY_ID_KEY] = journey.get_journey_id()
    response.headers[headers.INTERACTION_ID_KEY] = interaction.get_interaction_id()
    return response


class FlaskRosnik:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(_get_journey_id)
        app.after_request(_annotate_response_headers)
